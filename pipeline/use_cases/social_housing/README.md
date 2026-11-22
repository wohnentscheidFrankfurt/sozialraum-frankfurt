# social_housing: „Sozialwohnungen“

## Shows
`SH_SHARE` (Sozialwohnungen), `SH_COUNT` (count, no layer; `count_of`, no rule of its own). The profile shows the
share only. The tooltip of `SH_SHARE` names the count in a line of its own: „Sozialwohnungen: 6,6 %“, below it
„Wohnungen: 1.754“ (exact, as in table 1.2).
Stadtteile only. Topic „Wohnungsbestand“. A district shows the share of its Stadtteil, after the Stadtteil note.

## Formula
1. Social dwellings per Stadtteil: table 1.2 of the annual report „Kommunale Wohnraumversorgung“. The airport row
   goes to Sachsenhausen-Süd; dwellings outside Frankfurt do not count.
2. Share = social dwellings ÷ all dwellings of the Stadtteil (city building file, same day, dormitories included).
3. Frankfurt: the same over all Stadtteile.

## Why
The annual report of the city counts social dwellings per Stadtteil. The share divides by the city's count of all
dwellings on the same day, dormitories included, not by the Zensus grid: the grid lacks dormitories and everything
built since 2022.

Table 1.4 (restrictions that end) is not used. It lists only ends that are known, a lower bound.
Many bindings are extended (2025: 604 ends, 188 dwellings left the binding).

## Worked example
The ⓘ of `SH_SHARE` shows the Rechnung as a written sum for one Stadtteil. The sum is the whole Rechnung: `calc` stays
empty.
- Stadtteil: fixed in `CALC_EXAMPLE_QUARTERS` (`catalog.py`), Bonames, a Stadtteil with a high share. A high share
  gives large, readable rows. The step fails with the name of a missing Stadtteil (`require_example_quarters`).
- Rows (`social_housing_calc_example`): social dwellings ÷ all dwellings of the Stadtteil, with dormitories = the
  share. No row is an estimate.
- Rows are whole dwellings. The last row is the value of the map with one decimal.
- The sum leaves out the exclusions of the count (dwellings outside the stock, higher income, contract only). The Regel
  of the ⓘ states them.
- The step writes the example to `social_housing_calc_examples` (id → payload), from the same numbers as
  `social_housing_by_quarter`.

## Inputs
No dataset. Files `sources/frankfurt/parlis/` (annual report, `ANNUAL_REPORT_PDF`),
`sources/frankfurt/statistics/` (dwelling stock), Stadtteile in `sources/frankfurt/geodata/`,
`reference/check_reference.csv`, `reference/monitoring_city_values.csv`.

## Output
`social_housing_by_quarter`, `social_housing_city`, `social_housing_calc_examples`, `social_housing_checks`.

## Checks
- Rows plus outside equal the total row of table 1.2.
- Total of table 1.2 and the city's dwelling count against the reference (a new report fails here).
- The numbers in the ⓘ (outside Frankfurt, higher incomes, 2,294 dwellings secured by contract only, report p. 5)
  against the report.
- The page of table 1.2 says „Jahresbericht <year>“ (`check_report_year`); a new report stops the build.
- City share against the Monitoring 2022 (WARN, ± 1.5 points).

## Limits
- From 2025 on only dwellings that are actually subsidised count; the totals of 2021 to 2024 are not comparable.
- The map shows social housing only from the annual report. The share of the monitoring serves only as a check.
- A table of the report is found by its heading, last hit: the first hit is the table of contents.
- A new report: see the section "New annual report" below.

## New annual report

- A new report goes into `ANNUAL_REPORT_PDF` in `pipeline/config.py`.
- Then update every place that names the year. The step `social_housing` checks only that the page of table 1.2 says
  „Jahresbericht <year>“ for `SH_AS_OF`. It does not see the other texts, so the build stays green with stale labels.
- In `pipeline/use_cases/social_housing/catalog.py`: `SH_DATE` and `SH_AS_OF`, `SH_REPORT_NO` ("(B 223/2026)", the
  number of the report, visible in the ⓘ); `SH_OUTSIDE_STOCK`, `SH_HIGHER_INCOME`, `SH_CONTRACT_ONLY` (the build
  checks them against the report). In `texts.de.yaml`: the rule of `SH_SHARE` ("Ab 2025"); the titles carry no year.
  The sheet year of `DWELLING_STOCK_XLSX`; `sh_report_stock` and `sh_dwellings_city` in `reference/check_reference.csv`.
- In `pipeline/use_cases/social_housing/README.md`: the counting rule from 2025 ("From 2025 on", "2021 to 2024").
- In `web/map.html`: the help says "2011 bis 2026"; change the end year when the newest data is newer.
- The source line of the report (`report_source` in `texts.de.yaml`), the as-of date „Ende 2025“ (`end_of`), both footer
  entries (`SOURCES` in the same catalog), the years in the check report and the year "Wohnungsamt" in the cover note
  come from `SH_DATE`. They need no edit.
- After the change,
  `rg -n "2025" pipeline/use_cases/social_housing/ web/map.html`
  must show only the new years, outside this section and except for the survey 2025 ("Leben in Frankfurt 2025", "Umfrage
  2025").
- A later code change should let the error message of `check_report_year` name the files.
- From the 2025 report on a new counting rule applies: only dwellings that are actually subsidised.
