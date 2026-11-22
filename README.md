# Az LLM-alapú fejlesztőeszközök diffúziója és mérhető hatásai a fejlesztői ökoszisztémára a 2022 és 2026 közötti időszakban, nyilvánosan elérhető adatforrások alapján

Bedőcs Bálint szakdolgozatának kódja és adatai
(Budapesti Corvinus Egyetem, Gazdaságinformatikus BSc, 2026).

A tároló azt tartalmazza, amivel a dolgozat 4.2–4.5. alfejezetének számai, táblázatai és ábrái
elkészültek. A két szkript sorban lefuttatva a nyers adatokból újra előállítja őket.

## Mappák

| Mappa / fájl | Tartalom |
| --- | --- |
| `script/sede_lekerdezesek.sql` | A Stack Overflow havi kérdésszámának SQL-lekérdezései (Stack Exchange Data Explorer) |
| `script/adatok_tisztitasa.py` | 1. lépés: beolvassa és egységesíti a nyers adatokat, a `tiszta` mappába ment |
| `script/elemzes.py` | 2. lépés: kiszámolja az eredményeket, és elkészíti az ábrákat |
| `adatok/` | Nyers adatok: a lekérdezések eredményei (`QueryResults*.csv`) és az Indeed-index négy országra |
| `tiszta/` | Az 1. lépés kimenete: három egységesített tábla |
| `eredmenyek/` | A 2. lépés táblái |
| `abrak/` | A dolgozat ábrái |

## Adatforrások

1. **Stack Exchange Data Explorer** (https://data.stackexchange.com/stackoverflow):
   a havi kérdésszám. A lekérdezéseket 2026. november 8-án futtattam, kérdésazonosító-sávokra
   bontva, mert a teljes tábla túllépi a felület időkorlátját.
2. **Stack Overflow Developer Survey 2023–2026**: a fejlesztői felmérések válaszai.
   A fájlok 100 MB-nál nagyobbak, ezért nincsenek a tárolóban. Innen tölthetők le:
   https://github.com/StackExchange/Survey/tree/main/packages/archive

   A letöltött fájlokat ezeken a neveken kell az `adatok` mappába menteni:

   | Letöltendő fájl | Mentés neve |
   | --- | --- |
   | `2023/results.csv` | `adatok/results-3.csv` |
   | `2024/results.csv` | `adatok/results-2.csv` |
   | `2025/results.csv` | `adatok/results.csv` |
   | `2026/survey_results_public.csv` | `adatok/survey_results_public.csv` |

3. **Indeed Hiring Lab Job Postings Index** (https://github.com/hiring-lab/job_postings_tracker):
   a szoftverfejlesztési ágazat és az összes hirdetés indexe az Egyesült Államokra,
   az Egyesült Királyságra, Németországra és Franciaországra. Az elemzés a 2026 októberéig
   tartó hónapokat használja.



## Futtatás

Python 3.12 vagy újabb kell. A tároló gyökérmappájából:

    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt

    python script/adatok_tisztitasa.py   # 1. lépés: kellenek hozzá a letöltött felmérésfájlok
    python script/elemzes.py             # 2. lépés: letöltés nélkül is lefut, a tiszta mappából dolgozik

A szkriptek a legfontosabb számokat a képernyőre is kiírják, alfejezetenként.

## Licencek és forrásmegjelölés

- Stack Overflow Developer Survey: Open Database License (ODbL)
- Stack Exchange-tartalom: CC BY-SA 4.0
- Indeed Hiring Lab adatai: CC BY 4.0, forrás: Indeed Hiring Lab