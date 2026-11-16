# Sources

The originals that the map and the research read. Each file exists exactly once. Files lie in folders by origin: the
body that published the file where we fetched it, so the folder says where to fetch it again
(`docs/architecture.md`, Layout). What a file is used for stands in `pipeline/config.py`, `docs/architecture.md`
(Data flow) and the READMEs of the use cases. File names stay as the publisher gave them; an answer of a web service
gets the name of the service and its layer. Our own extracts
(Zensus database, election pages, monitoring table) lie next to their originals; this file says how they were made.
A source without a file in this folder is marked „not stored“. A list of links without files is not kept.

Lines in German below are copied unchanged from the old provenance files (`Weblinks.txt`, `Hinweis.txt`).

## zensus

Extracts of the Zensus database (Statistische Ämter des Bundes und der Länder) for Frankfurt, Zensus 2011 and 2022.

`grid/` holds the Frankfurt extracts of the 100 m grids and, for the two vacancy rates, of the 1 km grids. Each
extract keeps the rows of the original CSV whose cell lies in the box `BBOX_3035` of
`pipeline/shared/zensus/model.py`, with all columns and the original header. The 2011 extracts keep only the features
EIGENTUM, INSGESAMT, BAUJAHR_MZ (dwellings) and EIGENTUM, ZAHLWOHNGN_HHG (buildings), byte for byte. The two 1 km
extracts (`..._1km-Gitter_Frankfurt.csv`) come from the same ZIPs as the 100 m extracts of the vacancy rates
(Leerstandsquote_in_Gitterzellen.zip, Marktaktive_Leerstandsquote_in_Gitterzellen.zip, members `..._1km-Gitter.csv`).
They keep the rows whose 1 km square meets the box `BBOX_3035`, with the original header and unchanged values („–“
stays „–“). `pipeline/update_sources.py` downloads the ZIPs into `cache/` and writes the extracts. URL and date of
each download stand in `sources/fetched.csv`. The ZIPs (`DOWNLOADS` in `pipeline/config.py`):

- Zensus 2022, https://www.destatis.de/static/DE/zensus/gitterdaten/:
  - Zensus2022_Bevoelkerungszahl.zip: Zensus2022_Bevoelkerungszahl_100m-Gitter_Frankfurt.csv
  - Eigentuemerquote_in_Gitterzellen.zip: Zensus2022_Eigentuemerquote_100m-Gitter_Frankfurt.csv
  - Durchschnittliche_Nettokaltmiete_und_Anzahl_der_Wohnungen.zip:
    Zensus2022_Durchschn_Nettokaltmiete_Anzahl_der_Wohnungen_100m-Gitter_Frankfurt.csv
  - Leerstandsquote_in_Gitterzellen.zip: Zensus2022_Leerstandsquote_100m-Gitter_Frankfurt.csv
  - Marktaktive_Leerstandsquote_in_Gitterzellen.zip: Zensus2022_Marktaktive_Leerstandsquote_100m-Gitter_Frankfurt.csv
  - Flaeche_der_Wohnung_10m2_Intervalle.zip: Zensus2022_Flaeche_der_Wohnung_10m2_Intervalle_100m-Gitter_Frankfurt.csv
  - Gebaeude_nach_Eigentumsform_100mGitter.zip: Zensus2022_Gebaeude_nach_Eigentumsform_100m_Gitterzellen_Frankfurt.csv
  - Gebaeude_nach_Anzahl_der_Wohnungen_im_Gebaeude.zip:
    Zensus2022_Gebaeude_nach_Anzahl_der_Wohnungen_100m-Gitter_Frankfurt.csv
- Zensus 2011, https://www.destatis.de/static/DE/zensus/2011_gitterdaten/:
  - Wohnungen_im_100_Meter-Gitter.zip: Wohnungen100m_Frankfurt.csv
  - Gebaeude_und_Wohnungen_im_100_Meter-Gitter.zip: Geb100m_Frankfurt.csv

Tables of the Zensus database. Our long CSV extracts, written by `pipeline/update_sources.py` from the open proxy API
of the web client (no login). Table and key of each file stand in `ZENSUS_TABLES` of `pipeline/config.py`, URL and
date in `sources/fetched.csv`:

- Zensusdatenbank, Tabelle 4000W-1008 "Wohnungen: Baujahr (Mikrozensus-Klassen)", Frankfurt, Zensus 2011 und 2022
  (Gebietsstand 15.05.2022): Zensus2022_4000W-1008_Frankfurt_2011_2022.csv.
- Zensusdatenbank, Frankfurt (064120000000):
  - Tabelle 4000W-0001 "Wohnungskennzahlen: Leerstandsquote und Eigentumsquote", 2011 und 2022:
    Zensus2022_4000W-0001_Frankfurt_2011_2022.csv. Inhalt WHG007$QMU = Eigentumsquote (%), WHG009$QMU = Leerstandsquote
    (%).
  - Tabelle 4000W-0004 "Wohnungskennzahlen: Durchschnittliche Nettokaltmiete", 2022:
    Zensus2022_4000W-0004_Frankfurt.csv. Inhalt WHG012$QMU = €/m².
  - Tabelle 1000A-0004 "Personenkennzahlen: Durchschnittliche Wohnfläche je Bewohner/-in", 2022:
    Zensus2022_1000A-0004_Frankfurt.csv. Inhalt PRS028$QMU = m².
- Zensusdatenbank, Tabelle 4000W-2002 "Wohnungen: Art der Wohnungsnutzung - Eigentumsform des Gebäudes", Frankfurt,
  Zensus 2011 und 2022 (Gebietsstand 15.05.2022): Zensus2022_4000W-2002_Frankfurt_2011_2022.csv.
  WHGNZ2 = Art der Nutzung. Inhalt WHG002$ID0004 = Anzahl Wohnungen, WHG002$PO0004 = Prozent. Die Werte von 2022
  gleichen der früheren Handlieferung (Tabelle von Hand heruntergeladen).
- Zensusdatenbank, Tabelle 4000W-1011 "Wohnungen: Eigentumsform des Gebäudes" und Tabelle 3000G-2001 "Gebäude: Baujahr
  (Jahrzehnte) - Eigentumsform des Gebäudes", Frankfurt, Zensus 2011 und 2022 (Gebietsstand 15.05.2022):
  Zensus2022_4000W-1011_Frankfurt_2011_2022.csv, Zensus2022_3000G-2001_Frankfurt_2011_2022.csv. Inhalt WHG002$ID0004 =
  Anzahl Wohnungen, WHG002$PO0004 = Prozent; GEB001$QMU = Anzahl Gebäude. Qualität "e" = endgültig, "-" = null.
- Zensusdatenbank, Tabelle 3000G-2007 "Gebäude: Eigentumsform des Gebäudes - Art des Gebäudes/Heizungsart/Wohnungen im
  Gebäude" und Tabelle 4000W-2013 "Wohnungen: Eigentumsform des Gebäudes - Art des Gebäudes/Heizungsart/Wohnungen im
  Gebäude", Frankfurt, Zensus 2011 und 2022 (Gebietsstand 15.05.2022), je nach Eigentumsform und Wohnungen im Gebäude
  (GEBWG2):
  Zensus2022_3000G-2007_Frankfurt_2011_2022.csv, Zensus2022_4000W-2013_Frankfurt_2011_2022.csv. Inhalt GEB001$QMU =
  Anzahl Gebäude, WHG002$QMU = Anzahl Wohnungen.
- Zensusdatenbank, Tabelle 4000W-2013 "Wohnungen: Eigentumsform des Gebäudes - Art des Gebäudes/Heizungsart/Wohnungen im
  Gebäude", Frankfurt, Zensus 2011 und 2022 (Gebietsstand 15.05.2022), je nach Eigentumsform und Heizungsart (HZGAT1):
  Zensus2022_4000W-2013_Heizungsart_Frankfurt_2011_2022.csv. Inhalt
  WHG002$QMU = Anzahl Wohnungen. Not read by the build; the analysis (tenancy and heating of the GdWE) lies outside
  the repo.
- Zensus database, households of Frankfurt, Zensus 2011 and 2022 (territory of 15.05.2022). Finding:
  research/2026-10-31-household-types.md.
  - Table 5000H-1001 "Haushalte: Größe des privaten Haushalts (bis 6 und mehr Personen)":
    Zensus2022_5000H-1001_Frankfurt_2011_2022.csv. Content HSH002$ID0004 = number of households, HSH002$PO0004 =
    percent.
  - Table 5000H-1005 "Haushalte: Typ des privaten Haushalts": Zensus2022_5000H-1005_Frankfurt_2011_2022.csv. The
    answer also holds HSHTP4 (single mothers and single fathers apart).
  - Table 5000H-2001 "Haushalte: Größe des privaten Haushalts - Typ des privaten Haushalts (nach Familien)":
    Zensus2022_5000H-2001_Frankfurt_2011_2022.csv. Content HSH002$QMU = number of households. Its margins equal
    5000H-1001 and 5000H-1005.
  - The key needs the content variable HSH002. Without it the API answers 404.
- Zensusdatenbank, Metadaten (Definition GEBEG1 "Eigentumsform des Gebäudes", Variablen der Tabellen 4000W-1011 und
  3000G-2001, Tabellenliste 4000W), abgerufen am 09.10.2026: Zensus2022_Metadaten_Eigentumsform.json

## frankfurt/statistics

Bürgeramt, Statistik und Wahlen of the city of Frankfurt (Statistikportal, statistik.aktuell, Statistisches
Jahrbuch, Frankfurter Statistische Berichte, survey „Leben in Frankfurt“, election results).

- Building and dwelling stock: Gebäudedatei 2020 to 2025 (xlsx, csv), Statistisches Jahrbuch 2021, Frankfurter
  Statistische Berichte 2025.
  Archive (not read by the build):
  - `Abbruch- Gebäude und Wohnungen.xlsx`
  - `Fertiggestellte Wohnungen und Wohnräume im Neu- und Umbau.xlsx`
  - `Fertiggestellte neue Gebäude und Wohnungen.xlsx`
  - `Fertiggestellte neue Wohngebäude und Wohnungen.xlsx`
  - `Gebäude- und Wohnungsbestand, Wohnfläche.xlsx`
  - `Wohnungsbestand - Indikatoren.xlsx`
  - `BT_Reinzugang.csv`
  - `Statistisches Jahrbuch 2021.pdf`
  - `FSB_2025.pdf`
- Statistik aktuell 11/2013, Gebäude- und Wohnungszählung 2011 in Frankfurt am Main: Erste Ergebnisse auf einen Blick
  (vorläufige Werte, nur Wohngebäude): statistik.aktuell 11-2013 Gebäude und Wohnungen Frankfurt.pdf
- Survey „Leben in Frankfurt“ 2025 and 2024: reports (Frankfurter Umfragen 5 and 4), single datasets (CSV) with
  codebooks, and exports from the Statistikportal in `statistikportal/`. The build reads the two reports and the two
  CSV files (rent burden by household income, `pipeline/use_cases/survey/`).
  - `FU_5_Leben_in_Frankfurt_2025.pdf`, `FU_4_Leben_in_Frankfurt_2024.pdf`. FU 4 from
    https://statistikportal.frankfurt.de/download/Frankfurter_Umfragen/FU_4_Leben_in_Frankfurt_2024.pdf
  - `leben-in-frankfurt_2025.csv`, `leben-in-frankfurt_2024.csv`. The 2024 file from
    https://offenedaten.frankfurt.de/download/umfragen/leben-in-frankfurt_2024.csv (downloaded 20.10.2026). Licence
    dl-de/by-2-0 (Datenlizenz Deutschland – Namensnennung – Version 2.0), Stadt Frankfurt am Main; the codebook
    says so (2025 and 2024).
  - Trap: the codebook 2024 PDF prints wrong codes for `WOkami_a`, `WOflae_a` and `Umfragebezirk`. The 2024 CSV uses
    the codes of 2025. Evidence: the weight share of each survey area differs by at most 0.1 points between the years.
    Never read the 2024 data with the codes of the 2024 PDF.
  Archive (not read by the build; `research/scripts/lif.py`, `bez.py` and `rent_burden_income.py` read the datasets):
  - `codebook-2025.pdf`
  - `codebook-2024.pdf`, from https://offenedaten.frankfurt.de/download/umfragen/codebook_leben-in-frankfurt_2024.pdf
  - The exports in `statistikportal/`, one per question of the survey:
    - `Haben Sie vor umzuziehen - nach Umfragebezirk.xlsx`
    - `Haben Sie vor, in den nächsten 12 Monaten umzuziehen?.xlsx`
    - `In welcher Art von Gebäude leben Sie?.xlsx`
    - `Mit welchem Energieträger heizen Sie überwiegend Ihre Wohnung:Ihr Haus?.xlsx`
    - `Seit wie vielen Jahren leben Sie in Frankfurt?.xlsx`
    - `Wer vermietet Ihnen die Wohnung:das Haus?.xlsx`
    - `Wie hoch ist Ihre gegenwärtige monatliche Kaltmiete bzw. Belastung für Wohneigentum – ohne Heizungs- und sonstige Betriebskosten?.xlsx`
- Residents per Stadtbezirk 2012 to 2025 from the Statistikportal: „Demographische Kennzahlen (Stadtbezirke)“.
  Archive (not read by the build; `research/scripts/mon.py` weights with it):
  `Demographische Kennzahlen (Stadtbezirke).xlsx`
  - Trap: the column „Haushalte“ is wrong in 2018, 2023 and 2025. 2018 holds the persons in households of every
    Stadtbezirk (sum 773,824 instead of 413,365 households). 2023 holds them from 483 to the end of the table (33
    Stadtbezirke, sum 542,360 instead of 419,582). 2025 holds the households with German nationality (sum 284,194
    instead of 426,293). A fresh export from the Statistikportal on 31.10.2026 has the same values.
  - 2024 differs from the open data in 44 Stadtbezirke by 2 to 195 households (sum 424,723 instead of 422,398). The
    citywide table of the Statistikportal also says 424,723. The cause is not known.
  - The other years and the other columns are fine. 2022 matches the open data in every Stadtbezirk.
  - Stadtbezirk 483 includes 484 (footnote 7). Höchst-Süd (592) is suppressed (`-`).
  - For households per Stadtbezirk use `bevoelkerung_in_haushalten_stadtbezirke_.csv`.
- Households and persons in households per Stadtbezirk 2010 to 2025, Melderegister, 31.12., by nationality
  (`insgesamt`, `deutsch`, `ausländisch`): `bevoelkerung_in_haushalten_stadtbezirke_.csv`. Open data of the city,
  https://offenedaten.frankfurt.de/dcat/dataset/de-he-frankfurtam-bevoelkerung_in_haushalten_stadtbezirke_
  (`/content.csv`, downloaded 31.10.2026), licence dl-de/by-2-0. The build reads the row with `insgesamt` in
  Stadtbezirk, Stadtteil and Nation for persons per household (`read_household_size`, view Neubau).
  - The Stadtbezirke add up to the row `insgesamt` in every year.
  - In 2024, 621 includes 622; the row 622 is missing.
  - „Anzahl Personen in Haushalten“ is not the same count as „Einwohner/-innen“ of the Statistikportal. For the city
    it is 3 to 4 percent higher until 2018 and about 1 percent higher from 2019.
- Households per Stadtteil, Melderegister (Haushaltegenerierung, main and secondary residences), 31.12. Open data of
  the city, https://offenedaten.frankfurt.de/dcat/dataset/de-he-frankfurtam-<name> (`/content.csv`, downloaded
  31.10.2026), licence dl-de/by-2-0. Archive (not read by the build). Finding:
  `research/2026-10-31-household-types.md`.
  - `haushaltsstruktur.csv`: households by type, 2012–2024, 45 Stadtteile (Sachsenhausen-Süd is named
    „Sachsenhausen-Süd (inkl. Flughafen)“). Types: Einpersonenhaushalte, Paare und Ehepaare ohne Kinder bis 17 Jahre,
    Paare und Ehepaare mit Kindern bis 17 Jahre, Alleinerziehende, sonstige Mehrpersonenhaushalte. The city sums of
    2012–2020 equal table 2.29 of the Statistisches Jahrbuch 2021.
  - `haushalte_nach_groesse.csv`: households by size (1 to 5 and more persons) and Einpersonenhaushalte 65 Jahre und
    älter, 2010–2025, 45 Stadtteile and the row `insgesamt`. The Stadtteile add up to `insgesamt` in every year. The
    totals and the Einpersonenhaushalte equal `haushaltsstruktur.csv` in every Stadtteil and year.
  - Trap: „Einpersonenhaushalte 65 Jahre und älter“ of 2025 is not plausible. The city value jumps from 52,324 to
    75,455, Kalbach-Riedberg from 602 to 2,111. 2011–2020 equal table 2.28 of the Jahrbuch. Do not use 2025.
  - `kinder_in_haushalten.csv`: Alleinerziehende and Paare mit Kindern bis 17 Jahre by number of children,
    Alleinerziehende by sex, 2012–2024, 45 Stadtteile. In 8 of 585 rows a sum differs by 1 from its parts or from
    `haushaltsstruktur.csv`, all in small Stadtteile.
- statistik.aktuell 03/2021 „Wohnen mit Grundsicherung für Arbeitsuchende in Frankfurt am Main“ (Bürgeramt,
  Statistik und Wahlen, data of the BA, 15.12.2019), downloaded by the user from frankfurt.de on 1.11.2026:
  `FSA_2021_03_Wohnen_mit_Grundsicherung_2019.pdf`. Archive (not read by the build). Page 3 splits the costs:
  Unterkunftskosten 73.7 %, Betriebskosten 18.9 %, Heizkosten 7.4 %.
  Finding: `research/2026-11-01-warm-rent-and-income.md`.
- Kommunalwahl Frankfurt 15.3.2026:
  - Ortsbeiraete_2026_Wahlbeteiligung.csv: Export aus dem Statistikportal (Kapitel 2, Wahlbeteiligung je Ortsbezirk).
  - Ortsbeiraete_2026_Stimmen.csv und _Sitze.csv: ausgelesen aus
    https://statistikportal.frankfurt.de/fwa/kw2026/kap2/Ortsbeirat-1.html bis -16.html (Stimmen, Anteile, Veränderung
    zu 2021, Sitze 2026 und 2021). Summe der Stimmen = gültige Stimmen, geprüft am 6.10.2026.
    Archive, not read by the build: Ortsbeiraete_2026_Wahlbeteiligung.csv, Ortsbeiraete_2026_Stimmen.csv,
    Ortsbeiraete_2026_Sitze.csv.

## frankfurt/parlis

Documents of the Stadtverordnetenversammlung from PARLIS: reports of the Magistrat (B, M) and answers of the Magistrat
(F, ST).

Sozialwohnungen und Bindungen – Herkunft der Dateien (abgerufen am 8.10.2026)

Alle Dateien stammen aus PARLIS, dem Informationssystem der Stadtverordnetenversammlung.
Lesbare Fassung jeder Vorlage auch unter https://www.frankfurt-gestalten.de/vorlage/<Vorlage>

Jahresberichte „Kommunale Wohnraumversorgung“ (Amt für Wohnungswesen), Tabellen je Stadtteil. Ab 2025 neue Zählweise:
nur tatsächlich geförderte Wohnungen: 2016 · B 16/2018 Datei: B_16_2018_AN_Jahresbericht_2016.pdf
https://www.stvv.frankfurt.de/PARLISLINK/DDW?W=DOK_NAME='B_16_2018' 2017 · B 356/2018 Datei:
B_356_2018_AN_Jahresbericht_2017.pdf https://www.stvv.frankfurt.de/PARLISLINK/DDW?W=DOK_NAME='B_356_2018' 2018 · B
35/2020 Datei: B_35_2020_AN_Wohnraumversorgung_2018.pdf
https://www.stvv.frankfurt.de/PARLISLINK/DDW?W=DOK_NAME='B_35_2020' 2020 · B 54/2022 Datei:
B_54_2022_AN_Jahresbericht_2020.pdf https://www.stvv.frankfurt.de/PARLISLINK/DDW?W=DOK_NAME='B_54_2022' 2021 · B
276/2023 Datei: B_276_2023_AN_Taetigkeitsbericht_2021.pdf
https://www.stvv.frankfurt.de/PARLISLINK/DDW?W=DOK_NAME='B_276_2023' 2022 · B 457/2023 Datei:
B_457_2023_AN_Komm_Wohnraumversorgung.pdf https://www.stvv.frankfurt.de/PARLISLINK/DDW?W=DOK_NAME='B_457_2023' 2023 und
2024 · B 224/2026 Datei: B_224_2026.pdf, B_224_2026_AN1_Bericht_2023.pdf, B_224_2026_AN2_Bericht_2024.pdf
https://www.stvv.frankfurt.de/PARLISLINK/DDW?W=DOK_NAME='B_224_2026' 2025 · B 223/2026 Datei: B_223_2026.pdf,
B_223_2026_AN1_Bericht_2025.pdf https://www.stvv.frankfurt.de/PARLISLINK/DDW?W=DOK_NAME='B_223_2026'
No report for 2019 was found (8 Oct 2026).

Wohnungsmarktbericht:
  2019/2020 · B 430/2022
    Datei: B_430_2022_AN_Wohnungsmarktbericht.pdf
    https://www.stvv.frankfurt.de/PARLISLINK/DDW?W=DOK_NAME='B_430_2022'

Antworten des Magistrats an Ortsbeiräte (ST) und in der Fragestunde (F):
  Sozialwohnungen im Ortsbezirk 5 · ST 219/2018
    Datei: ST_219_2018.pdf
    https://www.stvv.frankfurt.de/PARLISLINK/DDW?W=DOK_NAME='ST_219_2018'
  Geförderte Wohnungen im Ortsbezirk 10 · ST 1719/2016
    Datei: ST_1719_2016.pdf
    https://www.stvv.frankfurt.de/PARLISLINK/DDW?W=DOK_NAME='ST_1719_2016'
  Sozialwohnungen in Bergen-Enkheim nach Eigentümer · ST 1359/2026
    Datei: ST_1359_2026.pdf
    https://www.stvv.frankfurt.de/PARLISLINK/DDW?W=DOK_NAME='ST_1359_2026'
  Geförderte Wohnungen im Ortsbezirk 12 · ST 650/2016
    Datei: ST_650_2016.pdf
    https://www.stvv.frankfurt.de/PARLISLINK/DDW?W=DOK_NAME='ST_650_2016'
  Geförderter Wohnraum in Kalbach-Riedberg · ST 1769/2021
    Datei: ST_1769_2021.pdf
    https://www.stvv.frankfurt.de/PARLISLINK/DDW?W=DOK_NAME='ST_1769_2021'
  Auslaufende Bindungen 2018–2020 · F 2072/2019
    Datei: F_2072_2019.pdf
    https://www.stvv.frankfurt.de/PARLISLINK/DDW?W=DOK_NAME='F_2072_2019'
  Auslaufende Bindungen 2019–2022 · F 255/2021
    Datei: F_255_2021.pdf
    https://www.stvv.frankfurt.de/PARLISLINK/DDW?W=DOK_NAME='F_255_2021'

New construction (Neubau) and subsidised new dwellings, research of 15.10.2026
(`research/2026-10-15-new-construction-data.md`). Archive (the build reads B 12/2024, F 3150/2025, F 79/2026,
F 9/2026 and F 158/2026, and B 483/2025 for a check); downloaded 15.10.2026 from
`https://www.stvv.frankfurt.de/download/<ID>.pdf`:
- Magistrat, Bericht B 12/2024 (8.1.2024), „Sozialwohnungen in Frankfurt“: subsidised new dwellings completed per year
  2010–2023, Förderweg 1 and 2. B_12_2024.pdf
- Magistrat, Bericht B 483/2025 (5.12.2025), „Sozialer Wohnungsbau“: completed dwellings 2019–2024, FW 1 completions
  2019–2024 by builder (sum). B_483_2025.pdf. The annex (Bilanz Förderjahr 2024, 8 MB) is a link only:
  https://www.stvv.frankfurt.de/download/B_483_2025_AN1.pdf
- Magistrat, Antwort auf Frage F 147/2021: subsidised completions 2020, first count. F_147_2021.pdf
- Magistrat, Antwort auf Frage F 3150/2025 (Sachstand 7.5.2025): FW 1 and FW 2 completions 2023 and 2024.
  F_3150_2025.pdf
- Magistrat, Antwort auf Frage F 79/2026 (Sachstand 24.6.2026): completions 2024 („Fertigstellungsanzeige nach HBO“),
  FW 1 and FW 2 2024 and 2025. F_79_2026.pdf
- Magistrat, Antwort auf Frage F 9/2026 (Sachstand 24.6.2026): FW 1 and FW 2 completions 2025. F_9_2026.pdf
- Magistrat, Antwort auf Frage F 158/2026 (Sachstand 26.8.2026): FW 1 completions 2023–2025 by housing companies or
  cooperatives against private builders. F_158_2026.pdf
- Magistrat, Antwort auf Frage F 120/2026 (Sachstand 26.8.2026): subsidised completions since 2020 in projects with a
  30 % quota, by public, private and community projects. F_120_2026.pdf

Ownership:
- Magistrat, Antwort auf Frage F 3283/2025 (Sachstand 2.7.2025), S. 1: „Der Frankfurter Wohnungsbestand der GWH
  umfasst 12.528 Wohnungen.“ https://www.stvv.frankfurt.de/download/F_3283_2025.pdf: F_3283_2025.pdf
- Magistrat, Antwort auf Frage F 677/2017 (Frage vom 22.6.2017, Sachstand 4.4.2018), S. 1–2: the owners with at least 50
  subsidised dwellings of the 1. Förderweg, 31.12.2016; the table names „Sahle Wohnen 915“ (the tooltips of the view
  „Trend“ name Sahle Wohnen as an example of a private housing company). Downloaded 15.10.2026 from
  https://www.stvv.frankfurt.de/download/F_677_2017.pdf: F_677_2017.pdf
- Research on a third private housing company (`research/2026-10-15-third-private-housing-company.md`). Archive (not
  read by the build); downloaded 15.10.2026 from `https://www.stvv.frankfurt.de/download/<ID>.pdf`:
  - Magistrat, Antwort auf Frage F 1527/2018 (Frage vom 1.11.2018, Sachstand 12.12.2018): Helenenhöfe of the Sahle
    Wohnen GmbH in the Europaviertel, subsidised under the Frankfurter Programm. F_1527_2018.pdf
  - Magistrat, Stellungnahme ST 1041/2020 (25.5.2020): power cables of the Sahle Baubetreuungsgesellschaft mbH at the
    Maastrichter Ring. ST_1041_2020.pdf
  - Magistrat, Stellungnahme ST 1419/2025 (1.9.2025): the VBL sells its dwellings in the Nordend. ST_1419_2025.pdf

Wärmeplanung: Magistrat report M 109/2026 with the Fachgutachten (annex 1) and the study annex of M 118/2024. See
`research/2026-10-11-heat-saving-and-construction-year.md`. Archive (not read by the build): M_109_2026.pdf,
M_109_2026_AN1_Fachgutachten.pdf, M_118_2024_AN2_e-think_Anhang_Studie.pdf.

## frankfurt/geodata

Umfragebezirke, Stadtbezirke and Stadtteile as GML from the WFS of the city of Frankfurt, with the capabilities of the
two services (`WFS_*.xml`). Archive (not read by the build): Umfragebezirke.gml (the map shows no survey areas),
WFS_Stadtgebietsgliederung.xml and WFS_Umfragebezirksgliederung.xml, the capabilities of the services that serve the
three GML files.
A preview of the map „Potenzial Wärmeverbrauchsreduktion“ of the heat planning from the
Geodatenkatalog of the city (© Klimareferat; see `research/2026-10-11-heat-saving-and-construction-year.md`).
Archive (not read by the build): Geodatenkatalog_Potenzial_Waermeverbrauchsreduktion_Vorschau.jpg.

Unchanged copies of three layers of the planAS WFS (Stadtplanungsamt), written by `pipeline/update_sources.py`. URL
and date of each download stand in `sources/fetched.csv`; the map shows that date as „Abruf“.
- planAS_erhaltungssatzungen_e-rv.gml: Erhaltungssatzungen in Kraft,
  https://planas.frankfurt.de/wfs/erhaltungssatzungen (typeName e-rv)
- planAS_erhaltungssatzungen_e-iv.gml: Erhaltungssatzungen im Verfahren (typeName e-iv)
- planAS_bebauungsplaene_bplan_iv.gml: Bebauungspläne im Verfahren,
  https://planas.frankfurt.de/wfs/bebauungsplaene_geltungsbereiche (typeName bplan_iv)

## frankfurt/offices

Other offices of the city of Frankfurt, from frankfurt.de (often downloaded by hand: frankfurt.de blocks automatic
requests).

Unchanged copies of the results of the Stadtverordnetenwahl 2026 from votemanager (Wahlamt), written by
`pipeline/update_sources.py`, https://votemanager-ffm.ekom21cdn.de/2026-03-15/06412000/daten/ (URL and date in
`sources/fetched.csv`): Open-Data-06412000-Stadtverordnetenwahl-Ortsteil.csv,
Open-Data-06412000-Stadtverordnetenwahl-Gemeinde.csv and votemanager_ergebnis_ebene_3_id_1_0.json (from
`api/wahl_54/ergebnis_ebene_3_id_1_0.json`).

- Monitoring 2024 zur sozialen Segregation und Benachteiligung, Teil 1 (Materialienreihe Jugend und Soziales, Band 10.1,
  as of 31.12.2022).
  `Monitoring2024_Stadtbezirke_nach_Umfragebezirk.csv` is our extract: `research/scripts/mon.py` reads it from the PDF
  and assigns each Stadtbezirk its survey area. The columns `Gruppe_Arbeitslosendichte_%`, `Gruppe_Mindestsich_%` and
  `Gruppe_Benacht_Index` hold the number label of the source row as printed (e.g. `202/203/213`, `424/25`; empty if the
  table has no row for the district): districts with the same label within a column share one value. EW, HH and
  EW15_65 (Statistikportal "Demographische Kennzahlen (Stadtbezirke)", 31.12.2022) are empty where the source
  suppresses them (`-`).
  The PDF is the origin of the extract (not read by the build):
  `Monitoring 2024 zur sozialen Segregation und Benachteiligung - Teil 1.pdf`
- Stadt Frankfurt, PM „Neuer Mietspiegel wird gut angenommen“ 2.9.2026 (Anhang mit Mietstrukturanalyse als PDF in diesem
  Ordner): https://frankfurt.de/de-de/aktuelle-meldung/amt-fuer-wohnungswesen/neuer-mietspiegel-wird-gut-angenommen/
  Archive (not read by the build): `64_S1_Frankfurter_Mietspiegel_2026_Mietenstruktur_PM_Anhang.pdf`
- Frankfurter Mietspiegel 2008 to 2026 (Amt für Wohnungswesen), downloaded by hand by the user on 31.10.2026 from
  https://frankfurt.de/service-und-rathaus/verwaltung/publikationen/amt-fuer-wohnungswesen/mietspiegel-frankfurt-am-main
  The build reads seven of the files (marked „read by the build“: means of the new and the older contracts and survey
  days, `RENT_SOURCES`; printed growth rates, `REPORT_GROWTHS`). The others are an archive (not read by the build).
  Findings: `research/2026-10-31-real-rents.md`, `research/2026-10-31-rents-wages.md`.
  - Brochures:
    - `64_S1_Frankfurter Mietspiegel 2008.pdf`
    - `64_S1_Frankfurter Mietspiegel 2010.pdf`
    - `64_S1_Frankfurter Mietspiegel 2012.pdf`
    - `64_S1_Frankfurter Mietspiegel 2014.pdf`
    - `64_S1_Frankfurter Mietspiegel 2016.pdf`
    - `64_S1_Frankfurter Mietspiegel 2018.pdf`
    - `64_S1_Frankfurter Mietspiegel 2020.pdf`
    - `64_S1_Frankfurter Mietspiegel 2022.pdf` (read by the build: survey day 1.7.2021)
    - `64_S1_Frankfurter Mietspiegel 2024.pdf` (read by the build: survey day 1.7.2023)
    - `64_S1_Frankfurter_Mietspiegel_2026.pdf` (read by the build: survey day 1.7.2025)
  - Reports with the sample mean:
    - `64_S1_Frankfurter Mietspiegel 2014_Gutachten_Dokumentation.pdf`
    - `64_S1_Frankfurter Mietspiegel 2018 - Gutachten_Dokumentation.pdf` (read by the build: survey month June 2017)
    - `64_S1_Frankfurter Mietspiegel 2022 - Gutachten_Dokumentation.pdf` (read by the build: rents 2017 and 2021)
    - `64_S1_Frankfurter Mietspiegel 2024 - Gutachten.pdf` (read by the build: rents 2023)
    - `64_S1_Frankfurter_Mietspiegel_2026_Dokumentation.pdf` (read by the build: rents 2025)
  - There is no report for 2010. Its mean (7.78 €/m²) is quoted in the report of 2014 (PDF page 21, footnote 4).
  - `64_S1_Frankfurter_Mietspiegel_2026_Wohnlagenverzeichnis.pdf`: the list of residential locations of 2026.
  - Trap: 2012, 2016 and 2020 are no surveys. They carry the previous table forward with the consumer price index
    (brochures, PDF page 4). Their values are not rents. 2024 is carried forward with a sample of its own.
  - Trap: since 2020 the Mietspiegel counts rents agreed or changed in the last six years (§ 558 BGB), before in the
    last four years. The survey of 2021 is the first with six years.
- Amt für Wohnungswesen, „Wohnungsmarktbericht 2019/2020“, final version of December 2022, downloaded by the user
  from frankfurt.de on 1.11.2026: `Wohnungsmarktbericht 2019_2020.pdf`. The build reads figure 41 (view „Miete“).
  The same report as `sources/frankfurt/parlis/B_430_2022_AN_Wohnungsmarktbericht.pdf`, but here the values of the
  figures are text, there images. Figures 40 and 41 (PDF pages 62 and 63): Mietbelastung (Bruttokaltmiete ÷
  Haushaltsnettoeinkommen) in Frankfurt by household net income, Mikrozensus 2006, 2010, 2014 and 2018.
  Finding: `research/2026-11-01-warm-rent-and-income.md`.
- Kommunalwahl 15.3.2026: AB2026_Nr_S4 ...pdf: Amtsblatt, Sonderausgabe vom 8.4.2026 mit den endgültigen Ergebnissen
  (Stadtverordnetenversammlung und Ortsbeiräte).
- Wärmeplanung: the Masterplan 100 % Klimaschutz (2015) and the presentation of the potential analysis (29.9.2025,
  Fraunhofer IFAM and Mainova for the city). Their URLs were not recorded (added 11.10.2026). Archive (not read by the
  build): `Masterplan-Klimaschutz_2015.pdf`, `Praesentation_2025_09_29_KWP-FFM_Potenzialanalyse_Ergebnisse.pdf`.

Wohnungspolitik der Stadt – Herkunft der Dateien (von Hand geladen am 8.10.2026; frankfurt.de sperrt automatische
Abrufe)

Archive (not read by the build): `Wohnungspolitische Leitlinien 2005 (Fassung 2008).pdf` and
`IWU Wohnungsbedarfsprognose 2016.pdf`.

Wohnungspolitische Leitlinien 2005 (Fassung 2008):
https://frankfurt.de/-/media/frankfurtde/service-und-rathaus/verwaltung/aemter-und-institutionen/amt-fuer-wohnungswesen/pdf/wohnungspolitische-leitlinien-der-stadt-frankfurt-am-main.pdf

IWU Wohnungsbedarfsprognose (Endbericht 20.05.2016, Zeitraum 2014–2040):
https://frankfurt.de/-/media/frankfurtde/service-und-rathaus/verwaltung/aemter-und-institutionen/amt-fuer-wohnungswesen/pdf/wohnungsbedarfsprogonose-2040.pdf

## companies

Publications of companies and the press: the examples in the ⓘ of „Private Unternehmen“ and in the tooltips of the
view „Trend“.

- Vonovia, Pressemitteilung „Vonovia investiert 15 Millionen in Frankfurter Wohnungen“, 24.2.2026, S. 2: „Insgesamt
  hat Vonovia in Frankfurt einen Bestand von rund 16.000 Wohnungen.“ Downloaded 14.10.2026 from
  https://www.vonovia.com/content/download/316454/16092725: Vonovia_PM_2026-02-24_Frankfurt.pdf
- GWH Immobilien Holding, Geschäftsbericht 2022: „Die oberste Muttergesellschaft des Teilkonzerns ist die
  Landesbank Hessen-Thüringen Girozentrale … („Helaba“).“ From gwh.de, downloaded 14.10.2026:
  GWH_Geschaeftsbericht_2022.pdf
- Catella, press release „Catella stellt Living Lyon fertig“ (2019): 123 apartments; „residential portfolio of
  Industria Wohnen in Lyoner Quartier, which comprises around 250 units“.
  https://www.catella.com/en/germany/news-and-press-releases/project-management/2019/catella-stellt-living-lyon-fertig
  (saved 14.10.2026): Catella_2019_Living_Lyon.html
- Cash., „Hamburg Trust: AIF übernimmt Mikroapartments“, 5.12.2014: Domicilium 11 Little East, 272 micro flats in
  Frankfurt am Main. https://www.cash-online.de/a/hamburg-trust-aif-ubernimmt-mikroapartments-222575/ (saved
  14.10.2026): cash-online_2014-12-05_Hamburg_Trust_Little_East.html
- Kooperation Frankfurt (association of ten housing cooperatives), pages of three members, each with „Anzahl der
  Wohnungen“ as of 31.12.2024: Volks- Bau- und Sparverein Frankfurt am Main eG (4.375), Beamten-Wohnungs-Verein
  Frankfurt am Main eG (1.491), Bauverein für Höchst am Main und Umgebung eG (1.500).
  https://www.kooperation-frankfurt.de/kooperationspartner/vbs, …/bwv, …/bvh (saved 14.10.2026):
  Kooperation_Frankfurt_vbs.html, Kooperation_Frankfurt_bwv.html, Kooperation_Frankfurt_bvh.html
- Sahle Wohnen, page „Geschäftsführung“ (undated; the page says „modified“ 7.7.2026): „Die familiengeführte Gruppe
  besitzt, vermietet und betreut etwa 23.000 Wohnungen.“ and „Darüber hinaus ist das Unternehmen in Hamburg und
  Frankfurt am Main aktiv“. The 23,000 dwellings lie mostly in North Rhine-Westphalia; the tooltips print no number.
  https://www.sahle-wohnen.de/geschaeftsfuehrung/ (retrieved 15.10.2026; the page is not verbatim: the `<script>`,
  `<style>`, `<noscript>`, `<svg>`, `<iframe>` and `<template>` elements, the `<link>` tags and the comments are
  removed, the visible text is unchanged): Sahle_Wohnen_Geschaeftsfuehrung.html

Research on a third private housing company (`research/2026-10-15-third-private-housing-company.md`). Archive (not read
by the build); retrieved 15.10.2026. The HTML pages are stored like the page above: not verbatim, the `<script>`,
`<style>`, `<noscript>`, `<svg>`, `<iframe>` and `<template>` elements, the `<link>` tags and the comments are removed,
the visible text is unchanged. The PDFs are verbatim.
- Sahle Wohnen, page „Firmengeschichte“: „Mit dem Bau von Wohnungen für seine Mitarbeiter im Grevener Hansaviertel legt
  der Schuhfabrikant Paul Sahle im Jahr 1963 den Grundstein für das Unternehmen Sahle Wohnen.“ (page modified
  17.8.2021). https://www.sahle-wohnen.de/firmengeschichte/: Sahle_Wohnen_Firmengeschichte.html
- Sahle Wohnen, page „Wohnen in Frankfurt am Main“: customer centre Valentin-Senger-Straße 136b; „Die Mehrzahl unserer
  Wohnungen ist gefördert“. https://www.sahle-wohnen.de/wohnen-in/frankfurt-am-main/:
  Sahle_Wohnen_Wohnen_in_Frankfurt.html
- Gemeinnütziges Siedlungswerk GmbH (GSW), page „Gesellschafter“: the owners are four Catholic dioceses and their
  Caritas associations. https://www.gsw-ffm.de/de/gsw/gesellschafter/: GSW_Gesellschafter.html
- GSW, page „Das Unternehmen“: „Bewirtschaftung von bezahlbarem Wohnraum mit ca. 9.000 Wohnungen“, average rent
  8,10 €/m². https://www.gsw-ffm.de/de/gsw/das-unternehmen/: GSW_Das_Unternehmen.html
- GSW, Geschäftsbericht 2025 (not stored, 8.9 MB; GSW is not named on the map; the research cites pages 11, 13, 14,
  22, 23 and 55): 7.654 own dwellings on 31.12.2025, chart of the regions (Großraum Frankfurt 3.536), shareholders,
  Gewinnrücklagen. https://www.gsw-ffm.de/pdf/GSW%20GB2025.pdf
- GSW, Geschäftsbericht 2024 (not stored, 6.5 MB; the research cites pages 6 and 9): founded 1949, Großraum
  Frankfurt 3.523 on 31.12.2024. https://www.gsw-ffm.de/pdf/GSW_GB_2024.pdf
- Not stored (not cited as evidence): the pages „Geschäftsbericht“, „Immobilienmanagement“ and the home page of GSW,
  the home pages and the page „125 Jahre“ of Sahle Wohnen, search results of PARLIS and screenshots of the research.

## hessen/statistics

Hessisches Statistisches Landesamt (HSL), Statistische Berichte. The build reads tables 15, 17 and 19 of F II 2 (view
„Neubau“), research of 15.10.2026 (`research/2026-10-15-new-construction-data.md`), table 4 of F I 1 (the stock) and
the reports A I 2 (the population), research of 25.10.2026 (`research/2026-10-25-dwelling-stock.md`):
- „Baufertigstellungen in Hessen im Jahr 2025“ (F II 2 j/25), table 15: all completed dwellings per district, table
  17: new residential buildings and dwellings, table 19: new non-residential buildings and their dwellings,
  Frankfurt 2025. https://statistik.hessen.de/sites/statistik.hessen.de/files/2026-05/fii2_j25.pdf:
  fii2_j25.pdf
- „Baufertigstellungen in Hessen im Jahr 2024“ (F II 2 j/24): same for 2024, tables 15, 17 and 19 only for a check;
  definitions („Wohnheime werden erst ab 1983 den Wohngebäuden zugeordnet“).
  https://www.statistischebibliothek.de/mir/servlets/MCRFileNodeServlet/HEHeft_derivate_00014706/FII2_j24_a.pdf:
  FII2_j24_a.pdf
- Baugenehmigungen neuer Wohngebäude in Hessen 1985 bis 2024 (table sheet F II 1), footnote „Ab 2002 inklusive
  Wohnheime“: FII1_T2.pdf
- „Die Bevölkerung der hessischen Gemeinden am 31. Dezember 2022“ (A I 2 mit A II, A III, A V, June 2023), the last
  population on the base of the Zensus 2011: Frankfurt 773,068 on 31.12.2022 (the Regionaldatenbank gives 747,389 on the
  base of the Zensus 2022). The title page prints „hj 1/22“, although the data are of 31.12.2022, the second half
  year (the file name says 22-2hj). Fetched on 25.10.2026 from
  https://www.statistischebibliothek.de/mir/servlets/MCRFileNodeServlet/HEHeft_derivate_00012084/AI2_AII_AIII_AV_22-2hj_a.pdf:
  AI2_AII_AIII_AV_22-2hj_a.pdf
- „Bevölkerung in Hessen am 31. Dezember 2025 und Bevölkerungsbewegungen im Jahr 2025 nach Gemeinden“ (A I 2 mit
  A II, A III, A V – hj 2/25, July 2026; the text layer of the title page reads „JuOi 2026“, the rendered page
  „Juli 2026“), Fortschreibung on the base of the Zensus 15. Mai 2022: Frankfurt 760,656 on 31.12.2025 (PDF pages 28
  and 35, row „412000“). The build reads it only for a check against the Regionaldatenbank. Fetched on 25.10.2026
  from
  https://www.statistischebibliothek.de/mir/servlets/MCRFileNodeServlet/HEHeft_derivate_00016211/AI2_AII_AIII_AV_25-2hj_a.pdf:
  AI2_AII_AIII_AV_25-2hj_a.pdf
- „Bestand an Wohngebäuden und Wohnungen in Hessen“ (F I 1 j/25, June 2026), Fortschreibung to 31.12.2025 on the
  base of the Zensus 2022. Table 4: dwellings in residential and non-residential buildings per municipality, Frankfurt
  415,359 (the build reads it). Downloaded by hand on 25.10.2026 (the site checks the browser):
  https://statistik.hessen.de/sites/statistik.hessen.de/files/2026-06/fi1_j25.pdf: fi1_j25.pdf
  Table 1 (PDF page 7), footnote 6: „Ab 2021 auf der Basis der Gebäude- und Wohnungszählung 2022.“ The report re-bases
  Hessen on 31.12.2021 (3,125,004); the Regionaldatenbank keeps 2021 on the old base (3,102,732). Vorbemerkungen (PDF
  page 4): since the HBO of 14.10.2025 (§ 63a) the recording of Bauabgänge may be affected.
- „Bestand an Wohngebäuden und Wohnungen in Hessen“ (F I 1 j/22, July 2023), Fortschreibung to 31.12.2022 on the
  base of the Gebäude- und Wohnungszählung 2011, the last one on that base. Table 4, Frankfurt 408,605 (PDF page 12;
  the build reads it for the chained growth of the stock). Fetched on 25.10.2026:
  https://www.statistischebibliothek.de/mir/servlets/MCRFileNodeServlet/HEHeft_derivate_00012246/FI1_j22_a.pdf:
  FI1_j22_a.pdf
- „Verbraucherpreisindex in Hessen 2022 bis 2025“ (M I 2 j/25, January 2026), base 2020 = 100. Table 3 (PDF page 20,
  printed 18): the overall index for Hessen per month and year (multi-year overview, used here for 2009–2025). The
  build reads table 3 (`read_price_index`, view Neubau). Table 1 (PDF page 11): the index of the Nettokaltmiete
  2022–2025 (not read by the build). Fetched on 31.10.2026 from
  https://statistik.hessen.de/sites/statistik.hessen.de/files/2026-01/mi2_j25.pdf: mi2_j25.pdf. Finding:
  `research/2026-10-31-real-rents.md`.
- „Entwicklung des Reallohn-, Nominallohn- und Verbraucherpreisindex in Hessen 2007 bis 2025“ (HSL, press table of
  the 3rd quarter of 2025), one sheet „nach Jahren und Quartalen“: Reallohnindex and Nominallohnindex (2022 = 100,
  index of the gross monthly earnings including special payments) and Verbraucherpreisindex (2020 = 100), per year
  2007–2024 and per quarter 2016 to the 3rd quarter of 2025. Footnote: up to 2021 the index covers the branches B to
  S, from 2022 A to S of the WZ 2008. Downloaded by hand by the user from statistik.hessen.de on 31.10.2026 (the
  report N I 8 of the 4th quarter of 2025 is no longer online): pm_verdienste_q3_2025_statistikhessen.xlsx. The
  build reads the Nominallohnindex per quarter (`read_wage_index`, view Neubau).
- „Verdienstverteilung in Hessen im Jahr 2025“ (N I 9 j/25, 2nd edition, July 2026), Verdiensterhebung April 2025.
  Table 2.2.4 (PDF page 36): quantiles of the gross monthly wage without special payments of full-time employees in
  Hessen (median 4,471 €, 9th decile 8,318 €). The build reads P88 and P89 (view „Miete“): where the pension
  ceiling lies in the distribution. There is no such table for Frankfurt and none before 2022.
  Finding: `research/2026-11-01-warm-rent-and-income.md`.
  https://statistik.hessen.de/sites/statistik.hessen.de/files/2026-07/ni9_j25_2aa.pdf (downloaded 1.11.2026):
  ni9_j25_2aa.pdf

## hessen/boris

Bodenrichtwerte (BORIS Hessen, Gutachterausschüsse, zones as of 1.1.2024, dl-de/zero-2-0; WFS and WMS allow every use
without condition): the pages boris_00.gml to boris_05.gml of the WFS
https://www.gds.hessen.de/wfs2/boris/cgi-bin/brw/2024/wfs (type BR_BodenrichtwertZonal, box around Frankfurt, 500
features per page), unchanged. Written by `pipeline/update_sources.py`; URL and date in `sources/fetched.csv`.

values_2026.csv: the Bodenrichtwerte of 1.1.2026 per zone number (`number`, `value` in €/m², `as_of`). For each zone
of the pages, a GetFeatureInfo of the WMS `hboris_feature`
(https://www.gds-srv.hessen.de/cgi-bin/lika-services/ogc-free-maps.ows) at its inner point; the zone of 2026 with the
same number gives value and Stichtag. Empty where the number does not hold there, or where the zone has no single
value in €/m² (farmland). Written by `pipeline/update_sources.py`; URL and date in `sources/fetched.csv`.

## hessen/lod2

3D-Gebäudemodell LoD2 Hessen (Hessische Verwaltung für Bodenmanagement und Geoinformation, HVBG, Geodaten online
https://gds.hessen.de). Geobasisdaten without restriction. A source note marks changes: „HVBG, eigene Auswertung“.
The raw package is not stored here (540 MB, in `cache/lod2/`). It is the ZIP of 59 Gemarkung ZIPs for the
Kreisfreie Stadt Frankfurt; each holds `<Gemarkung>-LoD2.gml` (CityGML 1.0, AdV profile, EPSG:25832, DHHN2016) and
`<Gemarkung>-LoD2.txt` (`Anzahl der 3D-Gebäude`, `Lieferdatum`). The link of the package holds a date. The REST API of
the download center names it, so `pipeline/update_sources.py` asks the API (`LOD2_API` in `pipeline/config.py`) and
takes `searchresult.packages[0].downloadLink.uri`.

lod2_frankfurt_parts.csv.gz: one row per part of each unique building (292,356 rows, 230,165 buildings). Written by
`pipeline/update_sources.py` with `pipeline/shared/readers/citygml.py`. Columns: `building` (gml:id), `function`
(Gebäudefunktion, e.g. 31001_1000), `gemarkung`, `created` (year of `creationDate`, empty if missing), `part` (0, 1, …;
a building without parts has part 0), `roof_type` (AdV code, 1000 is flat), `height_m` (`measuredHeight`, empty if
missing), `ground_m2` (area of the exterior rings of the GroundSurface, 1 decimal) and `footprint` (those rings in
EPSG:25832, rounded to 0.1 m, `x,y x,y …`, rings joined by `;`). The row order is the order of the package, then of
the file, then of the parts. The gzip header holds no time, so a rerun gives the same bytes.

Duplicates: 857 buildings stand in two Gemarkungen and 9 in three, so the files hold 875 extra copies (gml:id
counted over the 59 GML files of the package, 10.11.2026). The first copy is kept. Every other copy must have the
same function and the same parts, otherwise the run stops with a `ValueError`.
The txt files give 231,040 buildings, the files hold the same number. Without the copies 230,165 remain.

lod2_frankfurt_gemarkungen.csv: one row per Gemarkung: `gemarkung`, `buildings` (txt), `parsed` (buildings in the gml,
copies included), `delivered` (`Lieferdatum`, 2026-06-26).

Produktbeschreibung_3D-Gebäudemodelle.pdf: product description of the HVBG (Stand 31.03.2025), unchanged. It says that
`measuredHeight` of every part counts from the GroundSurface of the whole building (p. 7), and gives the height accuracy
(p. 1). URL and date in `sources/fetched.csv`.

## hessen/alkis

ALKIS, Liegenschaftskataster Hessen (HVBG, Geodaten online https://gds.hessen.de), Bestandsdatenausgabe Grundriss (NAS
XML), Kreisfreie Stadt Frankfurt am Main. Geobasisdaten without restriction. A source note marks changes: „HVBG, eigene
Auswertung“. The raw package is not stored here (one XML of 6.3 GB, in `cache/alkis/`). Delivery date (`portion_date`):
see `alkis_meta.csv`. Like the LoD2 package, the link holds a date, so `pipeline/update_sources.py` asks the REST API
of the download center (`ALKIS_API` in `pipeline/config.py`). It takes the one entry of type „File“ under `downloads`
(`Frankfurt am Main.zip`, `Frankfurt_am_Main-DOM1.zip`, `Frankfurt_am_Main-DGM1.zip`), never the package „Alle
Dateien …“ under `packages`: that is a ZIP holding the file's ZIP. Written by `update_alkis` with
`pipeline/shared/readers/nas.py`. All CSVs hold geometry as WKT in EPSG:25832. The gzip header holds no time, so a rerun
gives the same bytes.

- alkis_parcels.csv.gz: one row per parcel. Columns `gml_id`, `kz` (Flurstückskennzeichen), `official_m2`
  (amtliche Fläche), `created` (Entstehung), `addresses` (count of addresses), `wkt`.
- alkis_buildings.csv.gz: one row per building. Columns `gml_id`, `function` (Gebäudefunktion), `wkt`.
- alkis_landuse.csv.gz: one row per area of the actual land use. Columns `gml_id`, `cls` (AX_ class), `function`,
  `wkt`.
- alkis_meta.csv: rows `key,value` with `portion_date`, `parcels`, `buildings`, `landuse`, and the thresholds the
  cover file was measured with (`cover_high_m`, `cover_ndvi_green`; the check compares them with `model.py`).
- building_gaps_cover.csv: one row per geometry candidate of the building gaps. Columns `gml_id`, `px` (pixels of the
  parcel), `building`, `tree`, `green`, `open` (shares of the pixels), `nan_share` (share without height value) and
  `flight` (date of the orthophoto flight). The height model DOM1 and DGM1 (packages in `cache/dom/` and `cache/dgm/`,
  same download center) and the CIR orthophoto (WMS `DOP_WMS`, 20 cm, PNGs in `cache/dop/`) enter only this file. They
  are too large for `sources/`. Its row in `sources/fetched.csv` holds the three URLs (DOM1, DGM1, WMS), joined by a
  space, and the date of the run.

## regionalstatistik

Regionaldatenbank Deutschland (Statistische Ämter des Bundes und der Länder). Our long CSV extracts, written by
`pipeline/update_sources.py` from the open API of the web client (no login). Table and key of each file stand in
`REGIONAL_TABLES` of `pipeline/config.py`, URL and date in `sources/fetched.csv`:
- Table 31121-01-02-4 „Fertigstellungen neuer Wohngebäude und Wohnungen in Wohngebäuden nach Zahl der Wohnungen“,
  Gebäudeart „Wohngebäude (inkl. Wohnheime)“, Frankfurt (06412), 1995–2024:
  Regionalstatistik_31121-01-02-4_Frankfurt.csv. Content BAU015$QMU = buildings, WOHN01$QMU = dwellings,
  FLC001$QMU = living space in 1,000 m². Quality "e" = final, "." = no value.
- Table 31121-02-02-4 „Fertigstellungen neuer Nichtwohngebäude“, Frankfurt (06412), 1995–2024:
  Regionalstatistik_31121-02-02-4_Frankfurt.csv. Content BAU015$QMU = buildings, FLC002$QMU = usable floor space,
  WOHN01$QMU = dwellings (the build reads this one).
- Table 31121-03-02-4 „Fertigstellungen von Wohnungen in Wohn- und Nichtwohngebäuden nach Zahl der Räume“, Frankfurt
  (06412), 1995–2024: Regionalstatistik_31121-03-02-4_Frankfurt.csv. Content WOHN02$QMU = dwellings, row
  WHGGR2 = %TOTAL% (the build reads this one).
- Table 31231-02-01-4 „Bestand an Wohngebäuden und Wohnungen in Wohn- und Nichtwohngebäuden“ (Fortschreibung),
  Stichtag 31.12., Frankfurt (06412), 2011–2024:
  Regionalstatistik_31231-02-01-4_Frankfurt.csv. Content WOHNY1$QMU = dwellings in residential and non-residential
  buildings, row WHGGR1 = %TOTAL%. 2011–2021 rest on the Zensus 2011, from 2022 on the Zensus 2022: the series
  breaks between 2021 and 2022 (the HSL report F I 1 j/25 re-bases 2021 instead, footnote 6 of table 1). 31.12.2024
  (411,592) equals table 4 of the HSL report F I 1 j/24. The build reads this one.
- Table 12411-01-01-4 „Bevölkerung nach Geschlecht“ (Fortschreibung des Bevölkerungsstandes), Stichtag 31.12.,
  Hauptwohnsitz, Frankfurt (06412), 1995–2025: Regionalstatistik_12411-01-01-4_Frankfurt.csv.
  Content BEVSTD$QMU, row GES = %TOTAL%. 2011–2021 rest on the Zensus 2011, from 2022 on the Zensus 2022. 31.12.2021,
  2024 and 2025 equal the HSL reports A I 2 (2021,02; 2024,02; 2025,02).

## arbeitsagentur

Statistik der Bundesagentur für Arbeit, https://statistik.arbeitsagentur.de (downloaded 1.11.2026, no login, licence
of the BA: free use with source). Excel files as the BA names them. The build reads the four
Kosten-der-Unterkunft files and the Entgeltstatistik files of 2017 and of the series 2021 to 2025 (view „Miete“).
`entgelt-d-0-201612-xlsm.xlsm` is read by the research only (mid-year sensitivity).
Finding: `research/2026-11-01-warm-rent-and-income.md`.

- Kosten der Unterkunft, „Wohn- und Kostensituation“ SGB II, Kreis Frankfurt am Main (06412), one file per month:
  `https://statistik.arbeitsagentur.de/Statistikdaten/Detail/<YYYYMM>/iiia7/kdu-kdu/kdu-06412-0-<YYYYMM>-xlsx.xlsx`.
  Read: sheet „Tabelle 1b HH Miete“, block „Laufende tatsächliche Kosten der Unterkunft“, rows „pro qm“ of
  Unterkunftskosten, laufende Betriebskosten and Heizkosten (column „Insgesamt“). Files: `kdu-06412-0-201706-xlsx.xlsx`,
  `kdu-06412-0-202106-xlsx.xlsx`, `kdu-06412-0-202306-xlsx.xlsx`, `kdu-06412-0-202506-xlsx.xlsx`.
  Trap: the costs of households in the Grundsicherung, not of all tenants. Footnote 7 (Betriebskosten booked into the
  Unterkunftskosten by some Jobcenter) does not hit Frankfurt: statistik.aktuell 03/2021
  (`sources/frankfurt/statistics/FSA_2021_03_Wohnen_mit_Grundsicherung_2019.pdf`) shows Betriebskosten apart.
- Entgeltstatistik, median gross monthly wage of full-time employees of the Kerngruppe, 31.12.:
  `https://statistik.arbeitsagentur.de/Statistikdaten/Detail/<YYYY>12/iiia6/beschaeftigung-entgelt-entgelt/<file>`.
  - `entgelt-d-0-201612-xlsm.xlsm`, `entgelt-d-0-201712-xlsm.xlsm`: sheet „16.2“, row Frankfurt am Main, columns
    „Insgesamt (Arbeitsort)“ and „Insgesamt (Wohnort)“.
  - `entgelt-dwolk-0-202512-xlsx.xlsx`: sheets „8.2“ (Arbeitsort) and „9.2“ (Wohnort), time series 31.12.2021 to
    31.12.2025, row 06412 „Insgesamt“; sheet „9.1“ holds the wage classes of the residents in 2025.
  - Trap: the files of 2020 to 2022 hold no Wohnort tables. 31.12.2018 to 31.12.2020 by Wohnort are not published in
    this series.
  - Trap: wages above the Beitragsbemessungsgrenze of the pension insurance are cut at the ceiling; the top class
    („ü. 6.000 €“) is open.

## other

The Bundestag, the Rosa-Luxemburg-Stiftung, the Protestant church, the Hessian building law, the examples of the
building gaps and our own research.

- `building_gaps_examples/`: the sources of the five suitability examples in the tooltip of a building gap. The build
  does not read them; `reference/building_gaps_examples.csv` holds the quotes, the URLs and the paths of these copies.
  Fetched 15.11.2026.
  - Deutsches Architektenblatt 05/2025, excerpt of seven PDF pages that ZRS Architekten put online (their project
    Ellener Hof stands in the same article). Magazine p. 24–25 (PDF p. 4–5): the house of the group „Gemeinsam
    suffizient leben“, Friedberger Landstraße, Frankfurt (312 m², 15 adults and ten children, nine flats).
    https://www.zrs.berlin/wp-content/uploads/2025/07/250501_DAB-Magazin-05_2025_ZRS_Ellener_Hof.pdf:
    250501_DAB-Magazin-05_2025_ZRS_Ellener_Hof.pdf
  - Gemeinwohlbau Berlin, „Investorengespräch Kurzvorstellung“, 06/2026, p. 1 (19 Mieter*innen, 15 m wide) and p. 4
    (table „Flächenberechnung“, an image: Grundstück 365 qm). Public on Google Drive, byte for byte this copy
    (checked 15.11.2026). https://drive.google.com/file/d/1ZC27kiv9f84Sxetdd6MQUSzqRwFVdsQ9/view:
    202606_Investorengespräch_Kurzvorstellung.pdf
    The page https://gemeinwohlbau.de/idee (Downloads, „Gemeinwohlbau Präsentation“) links a later version of
    10.9.2026 with the same numbers (p. 1 and p. 4). The map links that page.
  - ABG Frankfurt Holding, press release 18.12.2025 „Spatenstich für neuen Wohnraum im Gallus: ABG baut auf
    ehemaligem Bunkerareal 42 geförderte Wohnungen“, Herxheimerstraße 10 (about 2,000 m²).
    https://www.abg.de/wp-content/uploads/2025_12_18_PM_Herxheimer-Strasse_Spatenstich-fuer-42-gefoerderte-Wohnungen.pdf:
    2025_12_18_PM_Herxheimer-Strasse_Spatenstich-fuer-42-gefoerderte-Wohnungen.pdf
  - ABG Frankfurt Holding, press page „ABG stellt 67 Passivhaus-Wohnungen in Frankfurt-Griesheim fertig“, Am
    Wingertsgrund (5,400 m², 67 flats, ready 5.2.2025), saved as HTML.
    https://www.abg.de/presse/abg-stellt-67-passivhaus-wohnungen-in-frankfurt-griesheim-fertig/:
    abg-stellt-67-passivhaus-wohnungen-in-frankfurt-griesheim-fertig.html
  - gpwirth architekten, project page „Studentenwohnheim Allersberger Straße“, Nürnberg (1,270 qm plot, 177
    apartments, 2015), saved as HTML.
    https://www.gpwirth-architekten.de/portfolio/studentenwohnheim-allersberger-strasse/:
    studentenwohnheim-allersberger-strasse.html

- Stellungnahme AfW im Bundestag 2024 (PDF in diesem Ordner, archive, not read by the build,
  `Stellungnahme AfW Frankfurt Bundestag 2024-02-15.pdf`):
  https://www.bundestag.de/resource/blob/990266/e7dfdbbfc7cf508120d9405f9de3af7b/Stellungnahme-Wagner_AfW.pdf
- Wem gehört die Stadt? (Rosa-Luxemburg-Stiftung), Frankfurt: https://www.wemgehoertdiestadt.de/frankfurt-am-main
  (Daten: page-data JSON in diesem Ordner, archive, not read by the build,
  `wemgehoertdiestadt_frankfurt_page-data.json`; Basis GWZ 2011, fortgeschrieben, "Beta")
- Rosa-Luxemburg-Stiftung, „Stadtprofil: So wirkt der Mietendeckel. Frankfurt am Main“ (Redaktionsschluss September
  2025), p. 1: the owner groups of the Zensus in two sectors, „Privat“ (70,7 % of the rented dwellings) and
  „Gemeinschaft“ (29,3 %: Kommune, Bund oder Land, Wohnungsgenossenschaften, Organisation ohne Erwerbszweck). The
  view „Trend“ takes only this grouping, the class names and the colour scheme (greys against reds), no number, and
  does not cite the profile.
  https://www.rosalux.de/fileadmin/user_upload/Frankfurt.pdf (downloaded 14.10.2026): RLS_Stadtprofil_Frankfurt.pdf
- Institut Wohnen und Umwelt (IWU) for the Deutscher Mieterbund, „Wohnkostenbelastung von Mietenden in Deutschland“,
  Kurzstudie, June 2026, table 2 (PDF page 29): Bruttokaltmiete and Wohnkostenbelastung of the Top-7 cities,
  Mikrozensus 2022 projected to 2024. Commissioned by an association: cross-check only, never a value of the map.
  https://mieterbund.de/app/uploads/2026/06/Kurzstudie-WohnkostenbelastungIWU_DMB.pdf (downloaded 1.11.2026):
  Kurzstudie-WohnkostenbelastungIWU_DMB.pdf
  Finding: `research/2026-11-01-warm-rent-and-income.md`.
- Own research of the ABG sites from public sources (as of 8.10.2026): ABG-Holding-Karte.geojson. Method in
  `research/2026-10-08-abg-abgleich-protokoll.md`.
- Deutscher Bundestag, Drucksache 19/7092 (17.1.2019), Antwort der Bundesregierung auf eine Kleine Anfrage zur
  Bundesanstalt für Immobilienaufgaben, Anlage 1, S. 15: „Frankfurt am Main 1.015 1.156 2.171“ (Darlehenswohnungen,
  bundeseigene Wohnungen, gesamt; as of 1.8.2018). Only the answer of the government is used.
  https://dserver.bundestag.de/btd/19/070/1907092.pdf (downloaded 14.10.2026): BT-Drs_19_7092.pdf
- Evangelisches Frankfurt und Offenbach (efo-magazin, the magazine of the Protestant church), „Stadtdekan Achim
  Knecht über Kirche und Immobilien: „Wir spekulieren nicht““, 17.9.2019: „Wir haben gut 500 Mietwohnungen“
  (Evangelischer Regionalverband Frankfurt und Offenbach, both cities together), „rund 170 Seniorenwohnungen im
  Westend“.
  https://www.efo-magazin.de/magazin/politik-welt/kirche-und-immobilien-wir-spekulieren-nicht/ (saved 14.10.2026):
  efo-magazin_2019-09-17_Kirche_und_Immobilien.html
- Hessisches Ministerium für Wirtschaft, Energie, Verkehr, Wohnen und ländlichen Raum (HMWVW), Referat VII 3
  Baurecht, „Drittes Gesetz zur Änderung der Hessischen Bauordnung (Baupaket I)“, Synopse, 22.10.2025 (Beschluss des
  Hessischen Landtages vom 9. Oktober 2025). Old and new wording side by side. § 6 Abs. 5 Satz 4, new column: „In
  allen Fällen muss die Tiefe der Abstandsflächen mindestens 2,50 m betragen.“ (old column: 3 m). It backs the wall
  strip of the low flat roofs (`WALL_GAP_M`); the check of `flat_roofs` reads the sentence.
  https://www.akh.de/fileadmin/Beratung/Recht/Gesetze/HBO/2025_HBO_Synopse_Baupaket_I.pdf (redirects to
  architektenkammer-hessen.de; downloaded 10.11.2026, 223,677 bytes): 2025_HBO_Synopse_Baupaket_I.pdf
