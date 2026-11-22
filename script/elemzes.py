import os
import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.lines import Line2D

os.makedirs("eredmenyek", exist_ok=True)
os.makedirs("abrak", exist_ok=True)
pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 12)

so = pd.read_csv("tiszta/so_havi.csv")
felmeres = pd.read_csv("tiszta/felmeres.csv", low_memory=False)
indeed = pd.read_csv("tiszta/indeed_havi.csv")

CHATGPT = pd.Timestamp("2022-11-30")
EVEK = [2023, 2024, 2025, 2026]


def cim(szoveg):
    print("\n" + "=" * 78 + "\n" + szoveg + "\n" + "=" * 78)


def ment(tabla, nev, index=True):
    tabla.to_csv(f"eredmenyek/{nev}.csv", index=index)


# az ábrák közös kinézete
plt.rcParams.update({
    "font.family": ["Times New Roman", "DejaVu Serif"],
    "font.size": 10,
    "axes.spines.top": False, "axes.spines.right": False, "axes.spines.left": False,
    "axes.edgecolor": "#c3c2b7", "axes.grid": True, "axes.grid.axis": "y",
    "grid.color": "#e1e0d9", "grid.linewidth": 0.6, "axes.axisbelow": True,
    "xtick.color": "#52514e", "ytick.color": "#52514e", "ytick.major.size": 0,
    "axes.labelcolor": "#52514e", "legend.frameon": False,
})
CM = 1 / 2.54
KEK, NARANCS, SZURKE, HALVANY = "#2a78d6", "#eb6834", "#52514e", "#898781"
KEKEK = ["#86b6ef", "#5598e7", "#2a78d6", "#1c5cab", "#104281"]   # világostól a sötétig


def ment_abra(fig, nev):
    fig.savefig(f"abrak/{nev}.png", dpi=300, facecolor="white")
    plt.close(fig)


def szazalek_tengely(ax):
    ax.set_ylim(0, 100)
    ax.set_yticks(range(0, 101, 20))
    ax.set_yticklabels([f"{v}%" for v in range(0, 101, 20)])


# ---- 4.2 Tudásmegosztás (K2, H2) ----
cim("4.2 Tudásmegosztás: a Stack Overflow havi kérdésszáma")

# havi átlag évenként, és mennyit változott az előző évhez képest
evi = so.groupby("Ev")["Kerdesek"].mean().round(0).to_frame("havi_atlag")
evi["valtozas_elozo_evhez_%"] = (evi["havi_atlag"].pct_change() * 100).round(1)
print("\nÉvenkénti havi átlag (2026: január és október között):")
print(evi)
ment(evi, "k2_evenkenti_atlag")

# H2: éves ütem a ChatGPT előtt és után (egyenes a kérdésszám logaritmusára)
so["sorszam"] = range(len(so))


def eves_utem(resz):
    meredekseg = np.polyfit(resz["sorszam"], np.log(resz["Kerdesek"]), 1)[0]
    return round((math.exp(12 * meredekseg) - 1) * 100, 1)


szakaszok = pd.DataFrame({
    "szakasz": ["ChatGPT előtt (2018-01 és 2022-11 között)",
                "ChatGPT után (2022-12 és 2026-10 között)",
                "ChatGPT után, csak a végleges hónapok (2022-12 és 2025-10 között)"],
    "eves_valtozas_%": [eves_utem(so[so["Datum"] <= "2022-11"]),
                        eves_utem(so[so["Datum"] >= "2022-12"]),
                        eves_utem(so[(so["Datum"] >= "2022-12") & (so["Datum"] <= "2025-10")])],
})
print("\nH2: a kérdésszám átlagos éves változása szakaszonként:")
print(szakaszok.to_string(index=False))
ment(szakaszok, "k2_h2_szakaszok", index=False)

# ugyanez a törölt kérdésekkel együtt, ellenőrzésnek
s = so.set_index("Datum")
torolt = pd.DataFrame({
    "csak_megmaradt": s["Kerdesek"],
    "torolttel_egyutt": s["Osszes"],
}).loc[["2022-11", "2023-11", "2024-11", "2025-10", "2026-10"]]
for o in ["csak_megmaradt", "torolttel_egyutt"]:
    torolt[o + "_valtozas_%"] = ((torolt[o] / torolt.loc["2022-11", o] - 1) * 100).round(1)
print("\nVáltozás 2022 novemberéhez képest, a törölt kérdésekkel és nélkülük:")
print(torolt)
ment(torolt, "k2_torolt_kerdesek")

# naponta jár-e a Stack Overflow-ra: aki használ AI-t és aki nem
latog = felmeres.dropna(subset=["AI", "SO_latogatas"])
latog = latog.assign(naponta=(latog["SO_latogatas"] == "naponta"))
napi = (latog.groupby(["Ev", "AI"])["naponta"].mean() * 100).round(1).unstack()
napi.columns = ["nem_hasznal_AI_%", "hasznal_AI_%"]
print("\nA Stack Overflow-t naponta látogatók aránya (felmérés, 2023 és 2025 között):")
print(napi)
ment(napi, "k2_napi_latogatok")

# 2026: mit változtatott az AI a Stack Overflow használatán (több válasz is lehet)
VALASZOK = {
    "Visit less for simple questions": "egyszerű kérdésekkel ritkábban látogatja",
    "Ask fewer questions": "kevesebb kérdést tesz fel",
    "Contribute less": "kevesebbet járul hozzá (válasz, szerkesztés)",
    "No change": "nem változott",
    "Visit more for verification": "ellenőrzés miatt gyakrabban látogatja",
}
v = felmeres[felmeres["Ev"] == 2026].dropna(subset=["SO_valtozas"])
sorok = []
for angol, magyar in VALASZOK.items():
    jelolte = v["SO_valtozas"].str.contains(angol, regex=False)
    sorok.append({"valasz": magyar,
                  "osszes_%": round(jelolte.mean() * 100, 1),
                  "hasznal_AI_%": round(jelolte[v["AI"] == 1].mean() * 100, 1),
                  "nem_hasznal_AI_%": round(jelolte[v["AI"] == 0].mean() * 100, 1)})
so_valt = pd.DataFrame(sorok)
print(f"\n2026: hogyan változott a Stack Overflow használata az AI miatt "
      f"({len(v)} válaszoló, ebből {int((v['AI'] == 1).sum())} AI-t használó és "
      f"{int((v['AI'] == 0).sum())} nem használó; több válasz is jelölhető):")
print(so_valt.to_string(index=False))
ment(so_valt, "k2_so_valtozas_2026", index=False)

# 1. ábra
so["Idopont"] = pd.to_datetime(so["Datum"] + "-15")
ezer = so["Kerdesek"] / 1000
n = (so["Datum"] < "2025-11").sum()            # az utolsó 12 hónapból még törölhetnek kérdéseket
fig, ax = plt.subplots(figsize=(16 * CM, 8 * CM), dpi=300)
ax.plot(so["Idopont"][:n], ezer[:n], color=KEK, lw=1.6)
ax.plot(so["Idopont"][n - 1:], ezer[n - 1:], color=KEK, lw=1.6, ls=(0, (2, 1.5)))
ax.axvline(CHATGPT, color=SZURKE, lw=0.8)
ax.text(CHATGPT + pd.Timedelta(days=25), 192, "ChatGPT megjelenése\n(2022. 11. 30.)",
        va="top", color=SZURKE, fontsize=9)
ax.set_ylim(0, 200)
ax.set_xlim(pd.Timestamp("2017-12-01"), pd.Timestamp("2026-12-31"))
ax.set_ylabel("Kérdések száma havonta (ezer)")
ax.xaxis.set_major_locator(mdates.YearLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
fig.tight_layout()
ment_abra(fig, "k2_so_kerdesek")


# ---- 4.3 Eszközhasználat csoportonként (K3, H3) ----
cim("4.3 Eszközhasználat: kik használnak AI-eszközt")
ai = felmeres.dropna(subset=["AI"])            # csak aki válaszolt az AI-kérdésre

# összesen
osszes = ai.groupby("Ev")["AI"].agg(arany_pct="mean", valaszolok="count")
osszes["arany_pct"] = (osszes["arany_pct"] * 100).round(1)
print("\nAI-t használók aránya, összes válaszadó:")
print(osszes)
ment(osszes, "k3_osszes")

# tapasztalat szerint
SORREND = ["0–2 év", "3–5 év", "6–10 év", "11–20 év", "20 év felett"]
tap = ai.dropna(subset=["Tapasztalat"])
tap_arany = (tap.pivot_table(index="Tapasztalat", columns="Ev", values="AI", aggfunc="mean")
             .reindex(SORREND) * 100).round(1)
tap_db = tap.pivot_table(index="Tapasztalat", columns="Ev", values="AI", aggfunc="count").reindex(SORREND)
print("\nAI-t használók aránya (%) szakmai tapasztalat szerint:")
print(tap_arany)
print("\nVálaszolók száma tapasztalat szerint:")
print(tap_db)
ment(tap_arany, "k3_tapasztalat_arany")
ment(tap_db, "k3_tapasztalat_db")

# életkor szerint
KOR = ["18 év alatt", "18–24 év", "25–34 év", "35–44 év", "45–54 év", "55–64 év", "65 év felett"]
kor = (ai.dropna(subset=["Korcsoport"])
       .pivot_table(index="Korcsoport", columns="Ev", values="AI", aggfunc="mean")
       .reindex(KOR) * 100).round(1)
print("\nAI-t használók aránya (%) életkor szerint:")
print(kor)
ment(kor, "k3_eletkor")

# 2025: milyen gyakran használják, tapasztalat szerint
gy = felmeres[(felmeres["Ev"] == 2025)].dropna(subset=["AI_gyakorisag", "Tapasztalat"])
gyak = (pd.crosstab(gy["Tapasztalat"], gy["AI_gyakorisag"], normalize="index") * 100).round(1)
gyak = gyak.reindex(SORREND)[["naponta", "hetente", "havonta vagy ritkábban", "nem használja"]]
print("\n2025: az AI-használat gyakorisága (%) tapasztalat szerint:")
print(gyak)
ment(gyak, "k3_gyakorisag_2025")

# 2025: AI-ágensek, tapasztalat szerint
ag = felmeres[(felmeres["Ev"] == 2025)].dropna(subset=["Agens", "Tapasztalat"])
agens = (pd.crosstab(ag["Tapasztalat"], ag["Agens"], normalize="index") * 100).round(1)
agens = agens.reindex(SORREND)[["naponta", "hetente", "havonta vagy ritkábban", "nem használ"]]
print("\n2025: AI-ágensek használata (%) tapasztalat szerint:")
print(agens)
ment(agens, "k3_agensek_2025")


# Magyarország és az összes válaszadó, 95%-os sáv Wilson-módszerrel
def wilson(p, n, z=1.96):
    nevezo = 1 + z * z / n
    kozep = (p + z * z / (2 * n)) / nevezo
    fel = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / nevezo
    return kozep - fel, kozep + fel


sorok = []
for ev, cs in ai.groupby("Ev"):
    hu = cs[cs["Magyar"] == 1]["AI"]
    also, felso = wilson(hu.mean(), len(hu))
    sorok.append({"Ev": ev, "osszes_%": round(cs["AI"].mean() * 100, 1),
                  "magyar_%": round(hu.mean() * 100, 1), "magyar_n": len(hu),
                  "sav_also_%": round(also * 100, 1), "sav_felso_%": round(felso * 100, 1)})
hu_tabla = pd.DataFrame(sorok)
print("\nMagyarország és az összes válaszadó:")
print(hu_tabla.to_string(index=False))
ment(hu_tabla, "k3_magyarorszag", index=False)

# 2. ábra
fig, ax = plt.subplots(figsize=(16 * CM, 8 * CM), dpi=300)
for i, csop in enumerate(SORREND):
    ax.plot(EVEK, tap_arany.loc[csop, EVEK], color=KEKEK[i], lw=1.8,
            marker="o", ms=4.5, mec="white", mew=0.8, label=csop)
ax.set_xticks(EVEK)
szazalek_tengely(ax)
ax.set_ylabel("AI-eszközt használók aránya")
ax.legend(title="Szakmai tapasztalat", ncol=5, fontsize=9, title_fontsize=9,
          loc="lower center", bbox_to_anchor=(0.5, 1.0))
fig.tight_layout()
ment_abra(fig, "k3_tapasztalat")

# 3. ábra
fig, ax = plt.subplots(figsize=(16 * CM, 7 * CM), dpi=300)
ax.plot(hu_tabla["Ev"], hu_tabla["osszes_%"], color=KEK, lw=1.8, marker="o", ms=4.5, mec="white")
ax.errorbar(hu_tabla["Ev"] + 0.04, hu_tabla["magyar_%"],
            yerr=[hu_tabla["magyar_%"] - hu_tabla["sav_also_%"], hu_tabla["sav_felso_%"] - hu_tabla["magyar_%"]],
            color=NARANCS, lw=1.8, marker="o", ms=4.5, mec="white", capsize=3, elinewidth=1)
ax.text(2026.12, hu_tabla["osszes_%"].iloc[-1] + 2.5, "Összes válaszadó", color=SZURKE, fontsize=9)
ax.text(2026.12, hu_tabla["magyar_%"].iloc[-1] - 4, "Magyarország", color=SZURKE, fontsize=9, va="top")
for _, sor in hu_tabla.iterrows():
    ax.text(sor["Ev"] + 0.04, sor["sav_also_%"] - 2, f"n = {int(sor['magyar_n'])}",
            ha="center", va="top", fontsize=8, color=HALVANY)
ax.set_xticks(EVEK)
ax.set_xlim(2022.8, 2026.75)
szazalek_tengely(ax)
ax.set_ylabel("AI-eszközt használók aránya")
fig.tight_layout()
ment_abra(fig, "k3_magyarorszag")


# ---- 4.4 Álláshirdetések (K4, H4) ----
cim("4.4 Munkaerő-kereslet: szoftverfejlesztői és összes álláshirdetés")
NEVEK = {"US": "Egyesült Államok", "GB": "Egyesült Királyság",
         "DE": "Németország", "FR": "Franciaország"}
indeed["Ev"] = indeed["Datum"].str[:4].astype(int)

# H4: változás a 2022-es átlaghoz képest, 2026 októberéig
sorok = []
for kod, nev in NEVEK.items():
    t = indeed[indeed["orszag"] == kod].set_index("Datum")
    ev2022 = t[t["Ev"] == 2022]
    sorok.append({
        "orszag": nev,
        "szoftver_valtozas_%": round((t.loc["2026-10", "szoftverfejlesztes"] / ev2022["szoftverfejlesztes"].mean() - 1) * 100, 1),
        "osszes_valtozas_%": round((t.loc["2026-10", "osszes"] / ev2022["osszes"].mean() - 1) * 100, 1),
        "szoftver_csucs_napja": t["csucs_napja"].iloc[0],
    })
h4 = pd.DataFrame(sorok)
print("\nH4: változás a 2022-es átlagtól 2026 októberéig:")
print(h4.to_string(index=False))
ment(h4, "k4_h4_valtozas", index=False)

# a szoftveres és az összes hirdetés aránya (2022 = 100), így kiszűrődik az általános csökkenés
evi_ind = indeed.groupby(["orszag", "Ev"])[["szoftverfejlesztes", "osszes"]].mean()
evi_ind["arany"] = evi_ind["szoftverfejlesztes"] / evi_ind["osszes"]
arany_index = evi_ind["arany"].unstack()
arany_index = (arany_index.div(arany_index[2022], axis=0) * 100).round(1).rename(index=NEVEK)
print("\nA szoftverfejlesztői hirdetések súlya az összes hirdetésen belül (2022 = 100):")
print(arany_index)
ment(arany_index, "k4_szoftver_arany_2022_100")

# 4. ábra
fig, axs = plt.subplots(2, 2, figsize=(16 * CM, 10.5 * CM), dpi=300, sharex=True, sharey=True)
for ax, (kod, nev) in zip(axs.flat, NEVEK.items()):
    t = indeed[indeed["orszag"] == kod]
    ido = pd.to_datetime(t["Datum"])
    ax.axhline(100, color="#c3c2b7", lw=0.8)
    ax.plot(ido, t["osszes"], color=NARANCS, lw=1.5)
    ax.plot(ido, t["szoftverfejlesztes"], color=KEK, lw=1.5)
    ax.axvline(CHATGPT, color=SZURKE, lw=0.7)
    ax.set_title(nev, fontsize=10, loc="left")
    ax.set_ylim(0, 250)
    ax.xaxis.set_major_locator(mdates.YearLocator(2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
axs[0, 0].text(pd.Timestamp("2023-01-15"), 232, "ChatGPT", fontsize=8, color=SZURKE)
for ax in axs[:, 0]:
    ax.set_ylabel("Index (2020. febr. 1. = 100)", fontsize=9)
fig.legend([Line2D([], [], color=KEK, lw=1.8), Line2D([], [], color=NARANCS, lw=1.8)],
           ["Szoftverfejlesztői hirdetések", "Összes álláshirdetés"],
           ncol=2, loc="upper center", fontsize=9)
fig.tight_layout(rect=(0, 0, 1, 0.94))
ment_abra(fig, "k4_indeed")


# ---- 4.5 Közös idővonal (K5, H5) ----
cim("4.5 Közös idővonal: a rétegek évenként és havonta, 2022 = 100")
so_evi = so.groupby("Ev")["Kerdesek"].mean()
ind_evi = indeed.groupby("Ev")[["szoftverfejlesztes", "osszes"]].mean()   # a négy ország átlaga
idovonal = pd.DataFrame({
    "so_kerdesek_2022_100": (so_evi / so_evi[2022] * 100).round(1),
    "szoftver_hirdetes_2022_100": (ind_evi["szoftverfejlesztes"] / ind_evi.loc[2022, "szoftverfejlesztes"] * 100).round(1),
    "osszes_hirdetes_2022_100": (ind_evi["osszes"] / ind_evi.loc[2022, "osszes"] * 100).round(1),
    "ai_hasznalok_%": osszes["arany_pct"],
})
print(idovonal)
ment(idovonal, "k5_idovonal")
havi = indeed.groupby("Datum")[["szoftverfejlesztes", "osszes"]].mean()
alap = havi[havi.index.str.startswith("2022")].mean()
havi_2022_100 = (havi / alap * 100).round(1)
print(havi_2022_100.loc["2022-05":"2022-11"])


def havi_utem(kezdet, veg, oszlop):
    resz = havi.loc[kezdet:veg, oszlop]
    meredekseg = np.polyfit(range(len(resz)), np.log(resz), 1)[0]
    return round((math.exp(meredekseg) - 1) * 100, 1)


oszlopok = ["szoftverfejlesztes", "osszes"]
utem = pd.DataFrame({
    "chatgpt_elott_2022_06_11": [havi_utem("2022-06", "2022-11", o) for o in oszlopok],
    "chatgpt_utan_2022_12_2023_05": [havi_utem("2022-12", "2023-05", o) for o in oszlopok],
}, index=oszlopok)
print(utem)
ment(utem, "k5_havi_utem")

so_ev = so.set_index("Datum")["Kerdesek"]
so_eves = (so_ev / so_ev.shift(12) * 100 - 100).round(1).loc["2022-06":"2023-06"]
print(so_eves)
ment(so_eves.to_frame("eves_valtozas_pct"), "k5_so_eves_valtozas")

# 5. ábra: három panel közös időtengellyel
so_havi = so.set_index("Datum")["Kerdesek"]
so_2022 = so_havi[so_havi.index.str.startswith("2022")].mean()
idovonal_havi = pd.DataFrame({
    "so_kerdesek_2022_100": (so_havi / so_2022 * 100).round(1),
    "szoftver_hirdetes_2022_100": (havi["szoftverfejlesztes"] / alap["szoftverfejlesztes"] * 100).round(1),
    "osszes_hirdetes_2022_100": (havi["osszes"] / alap["osszes"] * 100).round(1),
})
print(idovonal_havi.loc[["2022-11", "2026-10"]])
ment(idovonal_havi, "k5_idovonal_havi")

# a felmérések kitöltési időszakának közepe, ide kerülnek az AI-pontok az ábrán
FELMERES_KOZEPE = {2023: "2023-05-15", 2024: "2024-06-04", 2025: "2025-06-10", 2026: "2026-07-14"}
ai_idopont = pd.to_datetime([FELMERES_KOZEPE[e] for e in osszes.index])

ido = pd.to_datetime(idovonal_havi.index + "-15")
n = (idovonal_havi.index < "2025-11").sum()      # az utolsó 12 hónapból még törölhetnek kérdéseket
fig, axs = plt.subplots(3, 1, figsize=(16 * CM, 15 * CM), dpi=300, sharex=True)
so_ind = idovonal_havi["so_kerdesek_2022_100"]
axs[0].plot(ido[:n], so_ind[:n], color=KEK, lw=1.6)
axs[0].plot(ido[n - 1:], so_ind[n - 1:], color=KEK, lw=1.6, ls=(0, (2, 1.5)))
axs[0].set_title("Stack Overflow-kérdések (2022 = 100)", fontsize=10, loc="left")
axs[0].set_ylim(0, 180)
axs[1].plot(ido, idovonal_havi["szoftver_hirdetes_2022_100"], color=KEK, lw=1.6, label="Szoftverfejlesztői hirdetések")
axs[1].plot(ido, idovonal_havi["osszes_hirdetes_2022_100"], color=NARANCS, lw=1.6, label="Összes álláshirdetés")
axs[1].set_title("Álláshirdetések, négy ország átlaga (2022 = 100)", fontsize=10, loc="left")
axs[1].set_ylim(0, 120)
axs[1].legend(fontsize=8, loc="lower left")
axs[2].plot(ai_idopont, osszes["arany_pct"], color=KEK, lw=1.6, marker="o", ms=4, mec="white")
axs[2].set_title("AI-eszközt használó fejlesztők aránya (a felmérések időpontjában)", fontsize=10, loc="left")
szazalek_tengely(axs[2])
for ax in axs:
    ax.axvline(CHATGPT, color=SZURKE, lw=0.8)
axs[0].text(CHATGPT + pd.Timedelta(days=25), 172, "ChatGPT", fontsize=8, color=SZURKE, va="top")
axs[2].set_xlim(pd.Timestamp("2017-12-01"), pd.Timestamp("2026-12-31"))
axs[2].xaxis.set_major_locator(mdates.YearLocator())
axs[2].xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
fig.tight_layout()
ment_abra(fig, "k5_idovonal")

print("\nKész: a táblák az 'eredmenyek', az ábrák az 'abrak' mappában vannak.")