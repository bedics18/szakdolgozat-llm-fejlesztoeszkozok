import os
import pandas as pd

os.makedirs("tiszta", exist_ok=True)


# ---- 1. Stack Overflow havi kérdésszám (Stack Exchange Data Explorer) ----
# minden fájl egy Id-sáv eredménye (a lekérdezések: script/sede_lekerdezesek.sql),
# a sávhatáron lévő hónap két fájlban is szerepel, ezért hónaponként összeadjuk őket.
# 66-70 millió és 74 millió felett a PostsWithDeleted táblából (törölt kérdésekkel is)
SEDE_FAJLOK = [
    "adatok/QueryResults.csv",      # 46-50 millió: 2017-08 és 2018-04 között
    "adatok/QueryResults-2.csv",    # 50-54 millió: 2018-04 és 2019-01 között
    "adatok/QueryResults-3.csv",    # 54-58 millió: 2018-11 és 2019-09 között
    "adatok/QueryResults-4.csv",    # 58-62 millió: 2019-09 és 2020-05 között
    "adatok/QueryResults-5.csv",    # 62-66 millió: 2020-04 és 2021-02 között
    "adatok/QueryResults-9.csv",    # 66-70 millió: 2021-01 és 2021-11 között
    "adatok/QueryResults-6.csv",    # 70-74 millió: 2021-10 és 2022-10 között
    "adatok/QueryResults-10.csv",   # 74 millió felett: 2022-10 és 2026-11 között
]

reszek = []
for fajl in SEDE_FAJLOK:
    t = pd.read_csv(fajl)
    t = t.rename(columns={"Megmaradt": "Kerdesek"})   # a két újabb fájlban ez a neve
    if "Osszes" not in t.columns:                       # a régebbi fájlokban nincs ilyen
        t["Osszes"] = pd.NA
    reszek.append(t[["Ev", "Ho", "Kerdesek", "Osszes"]])

so = pd.concat(reszek)
so = so.groupby(["Ev", "Ho"]).agg(
    Kerdesek=("Kerdesek", "sum"),
    Osszes=("Osszes", lambda s: s.sum(min_count=1)),    # üres marad, ha nincs adat
).reset_index()
so["Datum"] = so["Ev"].astype(str) + "-" + so["Ho"].astype(str).str.zfill(2)

# csak teljes hónapok: 2017 hiányos, 2026 novembere még nem ért véget
so = so[(so["Datum"] >= "2018-01") & (so["Datum"] <= "2026-10")]
so = so[["Datum", "Ev", "Ho", "Kerdesek", "Osszes"]]
so.to_csv("tiszta/so_havi.csv", index=False)
print(f"[1] Stack Overflow: {len(so)} hónap (106 kell), "
      f"2022-11: {so.set_index('Datum').loc['2022-11', 'Kerdesek']} kérdés")


# ---- 2. Fejlesztői felmérések (Stack Overflow Developer Survey 2023–2026) ----
# a fájlnévből nem látszik az év, ezért az oszlopok számából derítjük ki
FELMERES_FAJLOK = ["adatok/results.csv", "adatok/results-2.csv",
                   "adatok/results-3.csv", "adatok/survey_results_public.csv"]
OSZLOPSZAM_EV = {84: 2023, 114: 2024, 172: 2025, 212: 2026}

# ezek az oszlopok kellenek (nem mindegyik van meg minden évben)
KELLENEK = ["AISelect", "WorkExp", "Age", "Country", "SOVisitFreq", "AIAgents", "SOChange"]


def ai_hasznalat(ev, v):
    """Használ-e AI-eszközt: 1 = igen, 0 = nem, üres = nem válaszolt."""
    if v == "NA":
        return None
    if ev in (2023, 2024):                       # "Yes" / "No, but I plan to soon" / ...
        return 1 if v == "Yes" else 0
    if ev == 2025:                               # "Yes, I use AI tools daily" stb.
        return 1 if v.startswith("Yes") else 0
    return 0 if "t use AI tools" in v else 1     # 2026: milyen eszközt használ


def ai_gyakorisag(ev, v):
    """Csak 2025-ben kérdezték: milyen gyakran használ AI-eszközt."""
    if ev != 2025 or v == "NA":
        return None
    if "daily" in v:
        return "naponta"
    if "weekly" in v:
        return "hetente"
    if "monthly" in v:
        return "havonta vagy ritkábban"
    return "nem használja"


def tapasztalat(evek):
    """A szakmai tapasztalat éveit öt csoportba sorolja."""
    if pd.isna(evek):
        return None
    if evek <= 2:
        return "0–2 év"
    if evek <= 5:
        return "3–5 év"
    if evek <= 10:
        return "6–10 év"
    if evek <= 20:
        return "11–20 év"
    return "20 év felett"


KORCSOPORT = {
    "Under 18 years old": "18 év alatt", "18-24 years old": "18–24 év",
    "25-34 years old": "25–34 év", "35-44 years old": "35–44 év",
    "45-54 years old": "45–54 év", "55-64 years old": "55–64 év",
    "65 years or older": "65 év felett",
}


def so_latogatas(v):
    """Milyen gyakran látogatja a Stack Overflow-t (2023–2025), négy csoportba vonva."""
    if pd.isna(v) or v == "NA":
        return None
    if v in ("Multiple times per day", "Daily or almost daily"):
        return "naponta"
    if v == "A few times per week":
        return "hetente többször"
    if v == "A few times per month or weekly":
        return "havonta többször vagy hetente"
    return "ritkábban"


def agens(v):
    """Csak 2025-ben kérdezték: használ-e AI-ágenst a munkájában."""
    if pd.isna(v) or v == "NA":
        return None
    if "daily" in v:
        return "naponta"
    if "weekly" in v:
        return "hetente"
    if "monthly" in v:
        return "havonta vagy ritkábban"
    return "nem használ"


tablak = []
for fajl in FELMERES_FAJLOK:
    fejlec = pd.read_csv(fajl, nrows=0).columns
    ev = OSZLOPSZAM_EV[len(fejlec)]
    oszlopok = [o for o in KELLENEK if o in fejlec]
    t = pd.read_csv(fajl, usecols=oszlopok, dtype=str, keep_default_na=False)
    t = t.reindex(columns=KELLENEK)              # a hiányzó oszlopok üresen jönnek létre

    t["Ev"] = ev
    t["AI"] = [ai_hasznalat(ev, v) for v in t["AISelect"]]
    t["AI_gyakorisag"] = [ai_gyakorisag(ev, v) for v in t["AISelect"]]
    t["Tapasztalat"] = pd.to_numeric(t["WorkExp"], errors="coerce").apply(tapasztalat)
    t["Korcsoport"] = t["Age"].map(KORCSOPORT)
    t["Magyar"] = (t["Country"] == "Hungary").astype(int)
    t["SO_latogatas"] = t["SOVisitFreq"].apply(so_latogatas)
    t["Agens"] = t["AIAgents"].apply(agens)
    # 2026: mit változtatott az AI a Stack Overflow használatán (több válasz, szövegként marad)
    t["SO_valtozas"] = t["SOChange"].where(t["SOChange"] != "NA")
    tablak.append(t[["Ev", "AI", "AI_gyakorisag", "Tapasztalat", "Korcsoport",
                     "Country", "Magyar", "SO_latogatas", "Agens", "SO_valtozas"]])
    print(f"[2] {fajl}: {ev}, {len(t)} válaszadó")

felmeres = pd.concat(tablak)
felmeres.to_csv("tiszta/felmeres.csv", index=False)
print(f"[2] Felmérés összesen: {len(felmeres)} válaszadó (234 715 kell)")


# ---- 3. Indeed álláshirdetési index (Hiring Lab) ----
# 100 = a 2020. február 1-jei szint, a napi adatokból havi átlagot számolunk
ORSZAGOK = ["US", "GB", "DE", "FR"]
reszek = []
for kod in ORSZAGOK:
    agazat = pd.read_csv(f"adatok/{kod}/job_postings_by_sector_{kod}.csv", parse_dates=["date"])
    szoftver = agazat[(agazat["display_name"] == "Software Development")
                      & (agazat["variable"] == "total postings")]
    szoftver = szoftver.set_index("date")["indeed_job_postings_index"]

    osszes = pd.read_csv(f"adatok/{kod}/aggregate_job_postings_{kod}.csv", parse_dates=["date"])
    osszes = osszes[osszes["variable"] == "total postings"]
    osszes = osszes.set_index("date")["indeed_job_postings_index_SA"]

    havi = pd.DataFrame({
        "szoftverfejlesztes": szoftver.resample("MS").mean(),
        "osszes": osszes.resample("MS").mean(),
    })[:"2026-10"]
    havi["orszag"] = kod
    havi["Datum"] = havi.index.strftime("%Y-%m")
    havi["csucs_napja"] = str(szoftver.idxmax().date())   # a szoftveres index legmagasabb napja
    reszek.append(havi)

indeed = pd.concat(reszek)[["orszag", "Datum", "szoftverfejlesztes", "osszes", "csucs_napja"]]
indeed.to_csv("tiszta/indeed_havi.csv", index=False)
print(f"[3] Indeed: {indeed['orszag'].nunique()} ország, {indeed['Datum'].nunique()} hónap")

print("\nKész: a tiszta adatok a 'tiszta' mappában vannak.")