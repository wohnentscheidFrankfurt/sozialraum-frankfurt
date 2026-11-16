# Household types in Frankfurt 2011–2025

31 Oct 2026. Question: is there a period between 2011 and 2025 in which we can break down the change of single
households and other household types? Which sources give it?

Answer: yes. The Melderegister of the city gives every household type per Stadtteil for every year from 2012 to 2024,
and household sizes from 2010 to 2025. The Zensus gives the city as a whole for 2011 and 2022. The two sources do not
tell the same story, so they must never stand in one series.

## Sources

- `sources/frankfurt/statistics/haushaltsstruktur.csv`: households by type per Stadtteil, 31.12.2012–2024.
- `sources/frankfurt/statistics/haushalte_nach_groesse.csv`: households by size per Stadtteil and city, 31.12.2010–2025.
- `sources/frankfurt/statistics/kinder_in_haushalten.csv`: households with children per Stadtteil, 31.12.2012–2024.
- `sources/frankfurt/statistics/bevoelkerung_in_haushalten_stadtbezirke_.csv`: households (total only) per
  Stadtbezirk, 31.12.2010–2025.
- `sources/frankfurt/statistics/Statistisches Jahrbuch 2021.pdf`, tables 2.26–2.30 (PDF pages 54–56, printed 40–42):
  Melderegister 2011–2020 for the city, with 2011 and single households by age.
- `sources/zensus/Zensus2022_5000H-1001_Frankfurt_2011_2022.csv`, `…5000H-1005…`, `…5000H-2001…`: Zensus 2011 and
  2022 for the city.

Provenance and traps of each file are in `sources/README.md`.

Not usable: the column „Haushalte“ of `Demographische Kennzahlen (Stadtbezirke).xlsx` is wrong in 2018, 2023 and 2025
(see `sources/README.md`). The Zensus 100 m grid has household types only for 2011. I found no 2022 grid with
household types [offen].

## Checks

- The city sums of `haushaltsstruktur.csv` equal table 2.29 of the Jahrbuch in every year 2012–2020. [belegt]
- The Stadtteile of `haushalte_nach_groesse.csv` add up to its row `insgesamt` in every year and column. Its totals and
  single households equal `haushaltsstruktur.csv` in every Stadtteil and year. Its single households 65 and older
  equal table 2.28 of the Jahrbuch for 2011–2020. [belegt]
- `kinder_in_haushalten.csv` agrees with `haushaltsstruktur.csv` for Paare mit Kindern in every row. For
  Alleinerziehende 8 of 585 rows differ by 1, all in small Stadtteile. [belegt]
- The Zensus sizes add up to the total in 2011 (354,756). In 2022 they add up to 386,590, the total is 386,587. The
  margins of 5000H-2001 equal 5000H-1001 and 5000H-1005. [belegt]

## Melderegister, city, 2012 against 2024

| Type | 2012 | 2024 | Change |
|---|---:|---:|---:|
| Einpersonenhaushalte | 209,130 | 227,046 | +17,916 (+8.6 %) |
| Paare ohne Kinder bis 17 | 67,977 | 75,517 | +7,540 (+11.1 %) |
| Paare mit Kindern bis 17 | 51,727 | 61,609 | +9,882 (+19.1 %) |
| Alleinerziehende | 15,693 | 17,022 | +1,329 (+8.5 %) |
| sonstige Mehrpersonenhaushalte | 41,792 | 41,204 | −588 (−1.4 %) |
| Total | 386,319 | 422,398 | +36,079 (+9.3 %) |

[eigene Auswertung]

Single households stay at about 54 percent of all households. The share was 53.5 % in 2011 (Jahrbuch) and 54.1 % in
2025 (230,521 of 426,293, `haushalte_nach_groesse.csv`). [eigene Auswertung]

## Zensus, city, 2011 against 2022

| Type | 2011 | 2022 | Change |
|---|---:|---:|---:|
| Einpersonenhaushalte | 170,527 | 205,090 | +34,563 (+20.3 %) |
| Paare ohne Kind(er) | 75,883 | 65,756 | −10,127 (−13.3 %) |
| Paare mit Kind(ern) | 66,967 | 71,617 | +4,650 (+6.9 %) |
| Alleinerziehende Elternteile | 23,953 | 25,928 | +1,975 (+8.2 %) |
| Mehrpersonenhaushalte ohne Kernfamilie | 17,424 | 18,200 | +776 (+4.5 %) |
| Total | 354,756 | 386,587 | +31,831 (+9.0 %) |

[eigene Auswertung]

The share of single households rises from 48.1 % to 53.1 %. Single households grow more than all households
together. [eigene Auswertung]

## Why the two sources differ

- Level: in 2011 the Melderegister counts 201,992 single households, the Zensus 170,527. The Melderegister builds
  households from the register (Haushaltegenerierung) and includes secondary residences. Couples who are not married
  and shared flats are not always linked, so some of them count as single households. [unsicher]
- Trend: the Melderegister share stays flat (53.5 % in 2011, 53.3 % in 2022). The Zensus share rises by 5 points. The
  cause is not known. [offen]
- Children: the Melderegister counts children up to 17 only. A couple with an adult child is a „sonstiger
  Mehrpersonenhaushalt“ there. The Zensus counts children of any age. So „Paare mit Kindern“ is not comparable
  between the sources. [belegt, definitions in the headings of the sources]
- Rule: use the Melderegister for the trend per Stadtteil and the Zensus for the city level. Never mix them in one
  series.

## Breaks in the Melderegister

- 2015: single households +10,410, Alleinerziehende +2,443. By 2019 single households fall again to 214,631, the
  Alleinerziehende in 2017 to 16,572. [belegt]
- 2022: Alleinerziehende +1,228, in 2023 back to 16,915. [belegt]
- Both jumps fall in years of large refugee arrivals (2015, Ukraine 2022). This is a guess, not checked. Year-on-year
  changes across 2015–2017 and 2022–2023 need care. The Bürgeramt, Statistik und Wahlen could explain them. [unsicher]
- 2025: single households 65 and older are not plausible (see `sources/README.md`). [belegt]

## Stadtteile: share of single households, 2012 against 2024

Largest falls and rises in percentage points:

| Stadtteil | 2012 | 2024 | Points |
|---|---:|---:|---:|
| Gallus | 60.0 % | 54.7 % | −5.3 |
| Bockenheim | 60.4 % | 56.8 % | −3.7 |
| Niederrad | 57.5 % | 53.9 % | −3.6 |
| Westend-Süd | 62.4 % | 59.3 % | −3.1 |
| Nordend-West | 63.0 % | 60.4 % | −2.6 |
| Bergen-Enkheim | 43.8 % | 47.1 % | +3.3 |
| Eckenheim | 51.2 % | 54.9 % | +3.7 |
| Sindlingen | 46.7 % | 50.4 % | +3.7 |
| Bonames | 44.7 % | 49.8 % | +5.1 |
| Frankfurter Berg | 34.2 % | 39.4 % | +5.2 |

[eigene Auswertung] The inner city, with many single households, moves towards the mean. The outer Stadtteile with few
single households move up. In Gallus the number of single households still grows (10,246 to 13,666), but other
households grow faster (Europaviertel). The reason is a guess. [unsicher]

The shares describe areas, not households (ecological fallacy).
