# Wages against rents in Frankfurt, 2017–2025

31 Oct 2026. Question: did wages keep up with the rents of the Frankfurter Mietspiegel between 2017 and 2025, with and
without inflation?

Answer: wages in Hessen rose by 30.1 %, prices in Hessen by 25.0 %, the rents of new contracts in Frankfurt by 36.6 %
and the rents of older contracts by 16.3 %. Without inflation wages rose by 4.1 %, new contracts by 9.3 %. Older
contracts fell by 6.9 %. The rents are sample means of four surveys, not the rent of all flats. The wages are those of
Hessen, not of Frankfurt.

## Sources

- Frankfurter Mietspiegel 2018–2026 with their reports, in `sources/frankfurt/offices/` (file names in
  `sources/README.md`). The means of the two groups and the survey days are in the pinned phrases of `RENT_SOURCES` in
  `pipeline/use_cases/new_construction/catalog.py`.
- `sources/hessen/statistics/mi2_j25.pdf`: HSL, Verbraucherpreisindex in Hessen (M I 2 j/25), table 3, 2020 = 100.
- `sources/hessen/statistics/pm_verdienste_q3_2025_statistikhessen.xlsx`: HSL press table, Nominallohnindex Hessen,
  2022 = 100, per quarter.
- `sources/frankfurt/statistics/bevoelkerung_in_haushalten_stadtbezirke_.csv`: persons in households and households,
  Melderegister, for the size of a household.
- The dwellings and the population of the HSL (`sources/regionalstatistik/`, `sources/hessen/statistics/`) for the
  comparison with the stocks.

## Values

[belegt] for the rents and the survey days (page numbers are PDF pages), [belegt] for the indices.

| | 2017 | 2021 | 2023 | 2025 | Where |
|---|---:|---:|---:|---:|---|
| Rent, new contracts, €/m² | 10.21 | 11.56 | 13.05 | 13.95 | report 2022 p. 90 (labels of figure 21), p. 89; report 2024 p. 29; documentation 2026 p. 102 |
| Rent, older contracts, €/m² | 8.69 | 9.14 | 9.43 | 10.11 | same |
| Survey date | June 2017 | 1.7.2021 | 1.7.2023 | 1.7.2025 | report 2018 p. 5; brochures 2022 p. 6, 2024 p. 6, 2026 p. 5 |
| VPI Hessen at the survey month (2020 = 100) | 97.2 | 103.1 | 116.6 | 121.5 | M I 2 j/25, table 3 |
| Wages Hessen, mean of quarters 2 and 3 (2022 = 100) | 88.8 | 95.45 | 104.15 | 115.5 | HSL press table |

The prices of the years in between are the VPI of July: 2018 99.2, 2019 100.6, 2020 99.6, 2022 109.9, 2024 118.7. The
wages of the years in between: 2018 91.95, 2019 94.4, 2020 92.0, 2022 98.05, 2024 110.5.

The values of 2017 stand only in the labels of figure 21 of the report 2022 („€8,66 €9,36 €10,29 €8,06 €8,69 9,14
€9,48 €10,21 11,56“: all, older and new contracts in 2013, 2017 and 2021). The text of p. 89 prints the growth 2017 to
2021: older +5.2 %, new +13.2 %. It matches the labels. The documentation 2026 p. 102 prints +7.2 % (older) and
+6.9 % (new) against 2023. It matches too. [belegt]

## Index, 2017 = 100

Each rent is its value divided by the value of 2017. Without inflation the index is divided by the price index of its
survey month. [eigene Auswertung]

| 2025 | In Euro | Without inflation |
|---|---:|---:|
| Rent, new contracts | 136.6 | 109.3 |
| Wages | 130.1 | 104.1 |
| Prices | 125.0 | 100 |
| Rent, older contracts | 116.3 | 93.1 |

Per survey year:

| | 2017 | 2021 | 2023 | 2025 |
|---|---:|---:|---:|---:|
| New contracts, in Euro | 100 | 113.2 | 127.8 | 136.6 |
| New contracts, without inflation | 100 | 106.7 | 106.5 | 109.3 |
| Older contracts, in Euro | 100 | 105.2 | 108.5 | 116.3 |
| Older contracts, without inflation | 100 | 99.2 | 90.5 | 93.1 |
| Prices | 100 | 106.1 | 120.0 | 125.0 |
| Wages, in Euro | 100 | 107.5 | 117.3 | 130.1 |
| Wages, without inflation | 100 | 101.3 | 97.8 | 104.1 |

- The new contracts 2023 without inflation: 13.05 ÷ 10.21 ÷ (116.6 ÷ 97.2) × 100 = 106.5498, shown as 106.5.
- Wages without inflation per year 2017–2025: 100, 101.5, 102.7, 101.1, 101.3, 97.7, 97.8, 101.9, 104.1.
- Older contracts fell without inflation mostly 2021 to 2023 (99.2 to 90.5), when prices rose by 13 %. Wages fell 2021
  to 2023 too (101.3 to 97.8).
- Stocks on 31.12.2025 against 31.12.2017: dwellings +6.6 % as published, +7.8 % chained over the Zensus 2022;
  population +1.8 % as published, +5.3 % chained. Both rents of new contracts grew faster than the dwellings in every
  calculation. [eigene Auswertung]
- Persons per household: 768,537 ÷ 416,615 = 1.8447 in 2017, 786,325 ÷ 426,293 = 1.8446 in 2025. [belegt]

## Traps

1. **Wages of a quarter differ a lot.** The survey days lie on the border of quarter 2 and quarter 3, and special
   payments move the quarters. Quarter 2 alone gives +28.3 % from 2017 to 2025, quarter 3 alone +32.0 %, the mean of
   both +30.1 %. The map takes the mean. [belegt]
2. **Six years against four.** The Mietspiegel counts rents of the last four years in 2017 and of the last six years
   from 2021. A longer period takes in more older rents. This pulls both means down, so the step from 2017 to 2021 is
   rather too small. The size is not known. [unsicher]
3. **Unchanged older contracts are missing.** The older contracts of the Mietspiegel are those that had a rent change
   in the period. Contracts without a change are not in it. [belegt]
4. **The mean is not the average rent of all flats.** See `research/2026-10-31-real-rents.md`, trap 1. [belegt]
5. **Wages of Hessen, not of Frankfurt.** The HSL press table gives Hessen only. Wages in Frankfurt may differ. [offen]
   The index covers branches B to S until 2021 and A to S from 2022 (footnote of the table), and it includes special
   payments. [belegt]
6. **Mid-year against 31.12.** Rents, prices and wages count in the middle of a year, the stocks on 31.12. The map puts
   them in the same slot of each year. A stock counts half a year later than a price of its slot. [belegt]
7. **2023 is an adjustment sample.** The Mietspiegel 2024 rests on an Anpassungsstichprobe with the survey day 1.7.2023,
   not on a survey like 2017, 2021 and 2025. [belegt, brochure 2024 p. 6]
8. **The VPI of Hessen, not of Frankfurt.** There is no price index for Frankfurt. [belegt]

## Check in the build

The build reads all values itself and stops on a changed format. The check „rents growth rates of the reports“ compares
the printed growth rates with the values read, „rents survey dates“ the survey months with the dates of the tooltips,
and „rents lead households“ the size of the households. They are in the section Checks of
`pipeline/use_cases/new_construction/README.md`.
