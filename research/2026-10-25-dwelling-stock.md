# Dwelling stock of Frankfurt 2011–2025

25 Oct 2026. Data check before the second chart of the view „Neubau“: the dwelling stock on 31.12. of each year.
Question: how far did the stock grow in the 10 years of the lead above the columns, and which list fits the columns?
Second question, the same day: did the dwellings grow faster than the population? The answer turned the chart into a
chart of dwellings against population (section „Population against dwellings“).

## Sources

- `sources/regionalstatistik/Regionalstatistik_31231-02-01-4_Frankfurt.csv`: Regionaldatenbank table 31231-02-01-4,
  Fortschreibung des Wohngebäude- und Wohnungsbestands, content `WOHNY1$QMU` (dwellings in residential and
  non-residential buildings), row `WHGGR1` = `%TOTAL%`, Stichtag 31.12., Frankfurt (06412), 2011–2024. All values
  have quality flag „e“.
- `sources/hessen/statistics/fi1_j25.pdf`: HSL report F I 1 j/25 (June 2026), table 4 „Bestand an Wohnungen in Wohn-
  und Nichtwohngebäuden in den hessischen Gemeinden am 31.12.2025“. The heading runs over two pages: PDF page 12
  holds its start and the row „412 000 Frankfurt am Main, Stadt“, page 13 the end with the day. First number of the
  row: 415 359.
- `sources/hessen/statistics/FI1_j22_a.pdf`: HSL report F I 1 j/22 (July 2023), Fortschreibung to 31.12.2022 on the
  base of the Gebäude- und Wohnungszählung 2011 (title page: „Ergebnisse auf Grundlage der Gebäude- und
  Wohnungszählung 2011“). Table 4, row „412 000 Frankfurt am Main, Stadt“, PDF page 12: 408 605. The PyMuPDF text
  of the title page drops some digits („Juli 202“, „j/2“); the heading of table 4 (PDF page 13) reads
  „31.12.2022“ in full.
- `sources/regionalstatistik/Regionalstatistik_31121-03-02-4_Frankfurt.csv` (2011–2024) and
  `sources/hessen/statistics/fii2_j25.pdf`, table 15 (2025: 3,772): all completed dwellings, the columns of the view.
- `sources/frankfurt/statistics/Gebäude- und Wohnungsbestand, Wohnfläche.xlsx`: the stock of the city's Gebäudedatei
  per Stadtteil, 2020–2025, one sheet per year.
- `sources/frankfurt/statistics/BT_Reinzugang.csv`: Zugang, Abgang and Reinzugang of the Gebäudedatei, 2020–2025, row
  „insgesamt“.
- `sources/frankfurt/statistics/Statistisches Jahrbuch 2021.pdf`, table 3.10 „Zugang, Abgang und Reinzugang von
  Wohnungen seit 2000“ (PDF page 86, printed page 72).
- `sources/frankfurt/parlis/B_483_2025.pdf`: B 483/2025, all completed dwellings 2019–2024 as the Magistrat gives
  them.
- `sources/regionalstatistik/Regionalstatistik_12411-01-01-4_Frankfurt.csv`: Regionaldatenbank table 12411-01-01-4,
  Fortschreibung des Bevölkerungsstandes, content `BEVSTD$QMU`, rows `GESM`, `GESW` and `%TOTAL%`, Stichtag 31.12.,
  Hauptwohnsitz, Frankfurt (06412), 1995–2025. All values have quality flag „e“. Male plus female equals the total
  in every year.
- `sources/hessen/statistics/AI2_AII_AIII_AV_25-2hj_a.pdf`: HSL report „Bevölkerung in Hessen am 31. Dezember 2025
  und Bevölkerungsbewegungen im Jahr 2025 nach Gemeinden“ (A I 2 mit A II, A III, A V – hj 2/25, July 2026), title
  page „Fortschreibungsergebnisse auf Basis Zensus 15. Mai 2022“. Frankfurt 760 656 on PDF pages 28 and 35 (row
  „412000“, German 535 235, not German 225 421), the same as the Regionaldatenbank. [belegt]
- `sources/hessen/statistics/AI2_AII_AIII_AV_22-2hj_a.pdf`: HSL report „Die Bevölkerung der hessischen Gemeinden am
  31. Dezember 2022“ (A I 2 mit A II, A III, A V, June 2023), title page „Fortschreibungsergebnisse Basis Zensus 09.
  Mai 2011“. Frankfurt 773 068 on PDF page 33 (row „412 Frankfurt am Main, Stadt“, insgesamt, male 380 566, female
  392 502) and on pages 36 and 43 (row „412000“, German 534 096, not German 238 972). Pages 9 and 11 give the balance
  of the year (see below).
- `sources/frankfurt/statistics/Wohnungsbestand - Indikatoren.xlsx`: Statistikportal, „Stadtteile - 2020 - 2025
  (Stichtag 31.12.) - Melderegister, Statistische Gebäudedatei“, one sheet per year, 45 Stadtteil rows with
  Einwohner/-innen and Wohnungen.

All numbers below were read from these files with `.venv/bin/python -I` on 25 Oct 2026.

## Results

### Stock, change, completions and outflow

Outflow = completed − change. Change and outflow stay empty for 2011 (no year before) and 2022 (new base).

| 31.12. | Stock | Change | Completed | Outflow |
|---|---|---|---|---|
| 2011 | 366,541 | | 2,138 | |
| 2012 | 368,933 | 2,392 | 2,682 | 290 |
| 2013 | 372,039 | 3,106 | 3,156 | 50 |
| 2014 | 376,431 | 4,392 | 4,418 | 26 |
| 2015 | 380,510 | 4,079 | 4,325 | 246 |
| 2016 | 384,609 | 4,099 | 4,273 | 174 |
| 2017 | 389,524 | 4,915 | 5,122 | 207 |
| 2018 | 393,186 | 3,662 | 3,761 | 99 |
| 2019 | 397,709 | 4,523 | 4,641 | 118 |
| 2020 | 402,210 | 4,501 | 4,675 | 174 |
| 2021 | 406,003 | 3,793 | 3,914 | 121 |
| 2022 | 404,227 | (−1,776) | 2,951 | |
| 2023 | 407,457 | 3,230 | 3,661 | 431 |
| 2024 | 411,592 | 4,135 | 4,203 | 68 |
| 2025 | 415,359 | 3,767 | 3,772 | 5 |

[belegt] Stock and completions are in the source files. [eigene Auswertung] Change and outflow are own differences.

- The outflow lies from 5 to 431 in the 13 years with one base on both ends (2012–2021, 2023–2025). Mean: 154.54.
- No outflow is negative. Every year the stock grew by less than the completions.
- 31.12.2024 = 411,592 in the Regionaldatenbank and in table 4 of the report F I 1 j/24. [belegt] Checked by hand;
  the report F I 1 j/24 is not stored in `sources/`.

### Break of the base in 2022

- 2011–2021 rest on the Zensus 2011, from 2022 on the Zensus 2022. [belegt] (`sources/README.md`, regionalstatistik)
- The stock falls from 406,003 (2021) to 404,227 (2022), by 1,776. Yet 2,951 dwellings were completed in 2022.
  [belegt]
- On the old base the HSL gives 408,605 for 31.12.2022 (report F I 1 j/22, table 4). [belegt] The new base lies
  404,227 − 408,605 = −4,378 dwellings below it. [eigene Auswertung] On the old base, 2022 has a change of 2,602 and
  an outflow of 2,951 − 2,602 = 349. [eigene Auswertung]
- The series of the Regionaldatenbank breaks between 2021 and 2022. The report F I 1 j/25 re-bases 2021 instead:
  table 1 (PDF page 7), footnote 6, „Ab 2021 auf der Basis der Gebäude- und Wohnungszählung 2022.“ Hessen on
  31.12.2021 is 3,125,004 there. The Regionaldatenbank and table 3 of the report F I 1 j/22 keep 3,102,732 on the
  old base. [belegt]
- So the change 2021 to 2022 shows the new base, not a loss of dwellings. The chart does not connect 2021 and 2022.

### Growth over the 10 years 31.12.2015 to 31.12.2025

| Calculation | Formula | Growth |
|---|---|---|
| Published | 415,359 ÷ 380,510 − 1 | 9.16 % |
| Chained over the old base of 2022 | (408,605 ÷ 380,510) × (415,359 ÷ 404,227) − 1 | 10.34 % |
| Completions 2016–2025 | 40,973 ÷ 380,510 | 10.77 % |

[eigene Auswertung]

- The published growth compares a stock on the Zensus 2011 base with one on the Zensus 2022 base.
- The chained growth takes 2015 to 2022 on the Zensus 2011 and 2022 to 2025 on the Zensus 2022. Both stocks of 2022
  are published by the HSL.
- The completions are an upper bound: they ignore every outflow.
- „Rund ein Zehntel“ holds for both. The first lead of the chart said so. The chart of dwellings against population
  replaced it on the same day.

### Outflow of 2025

- The outflow of 2025 is 5. The mean over all 13 years with one base on both ends is 154.54, over the other 12 years
  167.0. [eigene Auswertung]
- The report F I 1 j/25 says why it may be too low (Vorbemerkungen, PDF page 4): since the change of the HBO of
  14.10.2025 (§ 63a) demolitions mostly need no permit. Permits for demolitions were an important source for the
  outflow. The recording of Bauabgänge may be affected, and the comparability is limited. [belegt]
- The city's `BT_Reinzugang.csv` counts 216 dwellings „Abgang durch Abbruch“ in 2025 (2020–2024: 298, 300, 292, 206,
  105). [belegt]
- The ⓘ of the map names the caveat. The check „stock outflow of the last year“ requires it while the outflow of the
  last year is below a third of the mean of the other years.

### The city's Gebäudedatei: another list

Stock of the Gebäudedatei = sum of the 45 Stadtteil rows of each sheet. It equals the row „Gesamt“ of each sheet.

| 31.12. | Stock (city) | Change | Reinzugang | Change − Reinzugang | Stock (HSL) | City − HSL |
|---|---|---|---|---|---|---|
| 2020 | 407,420 | | 4,349 | | 402,210 | 5,210 |
| 2021 | 410,235 | 2,815 | 2,865 | −50 | 406,003 | 4,232 |
| 2022 | 414,063 | 3,828 | 3,313 | 515 | 404,227 | 9,836 |
| 2023 | 417,806 | 3,743 | 3,209 | 534 | 407,457 | 10,349 |
| 2024 | 426,738 | 8,932 | 3,942 | 4,990 | 411,592 | 15,146 |
| 2025 | 430,451 | 3,713 | 3,468 | 245 | 415,359 | 15,092 |

[belegt] Stock and Reinzugang are in the files. [eigene Auswertung] Sums and differences.

- The Gebäudedatei grows by 8,932 dwellings in 2024. Its own Reinzugang (Zugang durch Neu- und Umbau 4,047 minus
  Abgang durch Abbruch 105) is 3,942. About 5,000 dwellings enter the stock without a completion. The files do not
  say why.
- The city's stock lies 5,210 above the HSL in 2020 and 15,092 above it in 2025.
- Decision: the map uses the Fortschreibung of the HSL. It rests on the same building statistic as the columns. The
  Gebäudedatei is not used.

### Population against dwellings

Population = persons with Hauptwohnsitz on 31.12. (Regionaldatenbank 12411-01-01-4, row `%TOTAL%`). Dwellings as in
the first table.

| 31.12. | Population | Change | Dwellings | Dwellings per 1,000 |
|---|---|---|---|---|
| 2011 | 676,533 | | 366,541 | 541.8 |
| 2012 | 687,775 | 11,242 | 368,933 | 536.4 |
| 2013 | 701,350 | 13,575 | 372,039 | 530.5 |
| 2014 | 717,624 | 16,274 | 376,431 | 524.6 |
| 2015 | 732,688 | 15,064 | 380,510 | 519.3 |
| 2016 | 736,414 | 3,726 | 384,609 | 522.3 |
| 2017 | 746,878 | 10,464 | 389,524 | 521.5 |
| 2018 | 753,056 | 6,178 | 393,186 | 522.1 |
| 2019 | 763,380 | 10,324 | 397,709 | 521.0 |
| 2020 | 764,104 | 724 | 402,210 | 526.4 |
| 2021 | 759,224 | −4,880 | 406,003 | 534.8 |
| 2022 | 747,389 | (−11,835) | 404,227 | 540.9 |
| 2023 | 749,596 | 2,207 | 407,457 | 543.6 |
| 2024 | 756,021 | 6,425 | 411,592 | 544.4 |
| 2025 | 760,656 | 4,635 | 415,359 | 546.1 |

[belegt] Population and dwellings are in the source files. [eigene Auswertung] Change and dwellings per 1,000.

- 2011–2021 rest on the Zensus 2011, from 2022 on the Zensus 2022, as for the dwellings. [belegt] (`sources/README.md`,
  regionalstatistik)
- On the old base the HSL gives 773,068 for 31.12.2022 (report A I 2, PDF page 33). [belegt] The balance on PDF page
  9: 759,224 on 1.1.2022 (= the Regionaldatenbank on 31.12.2021), Lebendgeborene 8,014, Gestorbene 6,603,
  Zugezogene 68,759, Fortgezogene 56,922, Zu- oder Abnahme 13,844. [belegt] The Zu- oder Abnahme includes later
  corrections of the moves by the registration offices (footnote 1, PDF page 10). [belegt]
- The new base lies 747,389 − 773,068 = −25,679 persons below the old one. [eigene Auswertung] That is 3.3 % of
  773,068; the base effect of the dwellings is 1.1 % of 408,605. [eigene Auswertung]

Growth 31.12.2015 to 31.12.2025 [eigene Auswertung]:

| Calculation | Dwellings | Population |
|---|---|---|
| Chained over the old base of 2022 | 408,605 ÷ 380,510 × 415,359 ÷ 404,227 − 1 = 10.34 % | 773,068 ÷ 732,688 × 760,656 ÷ 747,389 − 1 = 7.38 % |
| Published | 415,359 ÷ 380,510 − 1 = 9.16 % | 760,656 ÷ 732,688 − 1 = 3.82 % |
| 2015 to 2022 on the old base | 7.38 % | 5.51 % |
| 2022 to 2025 on the new base | 2.75 % | 1.78 % |

- The dwellings grew faster with both calculations, and in both sections of the chain.
- From 2011 to 2015 the population grew faster: 732,688 ÷ 676,533 − 1 = 8.30 % against 380,510 ÷ 366,541 − 1 =
  3.81 % of the dwellings. [eigene Auswertung] Over 2011 to 2025, chained, the population grew more: 16.30 % against
  14.55 %. [eigene Auswertung] Published, the dwellings grew more: 415,359 ÷ 366,541 − 1 = 13.32 % against
  760,656 ÷ 676,533 − 1 = 12.43 %. [eigene Auswertung] So the statement holds only from 2015. The heading names the
  year („Seit 2015 wuchs die Zahl der Wohnungen schneller als die Bevölkerung“).
- K = 732,688 ÷ 380,510 = 1.92554. On an axis of the dwellings from 340,000 to 420,000 the population ÷ K lies from
  351,347 (2011) to 401,481 (2022 on the old base). The right axis runs from 340,000 × K = 654,684 to 420,000 × K =
  808,728. [eigene Auswertung]

### The city's Melderegister: another count

Population of the Melderegister = sum of the 45 Stadtteil rows of each sheet (column „Einwohner/-innen“). The sheets
have no total row. The column „Wohnungen“ holds the stock of the Gebäudedatei of the table above.

| 31.12. | Melderegister | Fortschreibung (HSL) | Melderegister − HSL |
|---|---|---|---|
| 2020 | 758,847 | 764,104 | −5,257 |
| 2021 | 753,626 | 759,224 | −5,598 |
| 2022 | 767,609 | 747,389 | 20,220 |
| 2023 | 770,166 | 749,596 | 20,570 |
| 2024 | 776,843 | 756,021 | 20,822 |
| 2025 | 781,337 | 760,656 | 20,681 |

[belegt] Stadtteil rows and the Fortschreibung are in the files. [eigene Auswertung] Sums and differences.

- The Melderegister has no break: it grows by 13,983 from 2021 to 2022. The Fortschreibung falls by 11,835 at the new
  base.
- Up to 2021 the Melderegister lies about 5,000 below the Fortschreibung, from 2022 about 20,000 above it.
- Decision: the map uses the Fortschreibung of the HSL for the population. It shares the day, the publisher and the
  break with the stock. The Melderegister is not used, and the ⓘ does not name it.

### Side finding: B 483/2025 mixes two lists

B 483/2025 gives all completed dwellings 2019–2024: 3,663, 4,349, 3,914, 2,951, 3,661 and 4,203.

- 2021–2024 equal the completions of the HSL. [belegt]
- 2019 and 2020 do not: the HSL gives 4,641 and 4,675. [belegt]
- 3,663 and 4,349 equal the Reinzugang of the Gebäudedatei in the Statistisches Jahrbuch 2021, table 3.10 (PDF page
  86): 2019 Zugang durch Neubau 3,248 + Umbau 4,505 = Bruttozugang 7,753, minus Abgang durch Umbau 3,974 and durch
  Abbruch 116 = Reinzugang 3,663; 2020 Reinzugang 4,349. [belegt] `BT_Reinzugang.csv` gives 4,349 for 2020 too.
- So B 483/2025 takes 2019 and 2020 from the city's net count and 2021–2024 from the HSL completions. This explains
  the gap that the check „gap of 2019 and 2020“ of the view Neubau guards. [eigene Auswertung]

## Limits

- The Fortschreibung is not a count. Its error grows with the years since its Zensus base.
- The outflow is a rest. It holds every correction of the Fortschreibung, not only Abriss and Umnutzung.
- The outflow of 2025 may miss demolitions (HBO, § 63a). The stock of 2025 may be a little too high.
- City only. The Fortschreibung of the HSL gives no Stadtteile.
- The population of the Fortschreibung is not a count either. The Zensus 2022 lowered it by 25,679.
- The statement „more dwellings than population growth“ depends on the start year. It holds from 2015, not from 2011.
