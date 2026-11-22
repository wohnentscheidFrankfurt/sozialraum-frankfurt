# rent_burden: „Miete“

## Shows
No layer and no indicator. The view „Miete“ with two figures (fixed links `miete`, `miete/warmmiete-und-lohn`,
`miete/warmmiete-und-einkommen`; the keys `link` of `WAGE_TEXTS` and `LOW_INCOME_TEXTS`).

Figure S1 (`WAGE_TEXTS`) is a worked example: the warm rent of one flat of `FLAT_M2` = 55 m² as a share of the net
wage of three model persons who live alone and work full time. The persons (`PERSONS`) earn the Mindestlohn, the median
wage of the residents („mittlerer Lohn“) and a wage at the pension ceiling („hoher Lohn“). The figure shows the latest
survey year of the Mietspiegel only (`RENT_TO`, 2025; Mietspiegel 2026) as wage bars: per person a frame as wide as
the net wage in euros, and in it the red block of the warm rent, equally wide in every row. A switch shows new or older
contracts of the Mietspiegel. The heading (`WAGE_TEXTS["title"]`) says that the share at the Mindestlohn is about three
times the share at the high wage. The lead (`WAGE_TEXTS["lead"]`) names what is left after the warm rent at the
Mindestlohn and at the high wage, new contract. The tooltip of a row names contract, person, warm rent, net wage, share
and what is left.

Figure S2 (`LOW_INCOME_TEXTS`) shows adult tenants in three groups of household net income (under 2,000 €, 2,000 to
under 3,200 €, 3,200 € and more). Each group is one bar, split into four burden classes (under 30 %, 30 to under 40 %,
40 to under 50 %, 50 % and more). The label of each bar names the median burden of the group in whole percent. The
heading (`LOW_INCOME_TEXTS["title"]`) says that the warm rent of the lowest group is about half its income. The lead
(`LOW_INCOME_TEXTS["lead"]`) names the share of the lowest group among the adult tenants and the median of the highest
group.

Each figure has one ⓘ (`info`: Quelle, Stand, Rechnung, Regel, Unsicherheit) and one source line (`source`). The
footer of the map lists the sources of `SOURCES` in `catalog.py`, after those of `new_construction`.

The table computes every survey year (`rent_burden_wage`). The figure shows 2025; 2017 stands here for comparison.

| Share of the net wage, new contract | 2017 | 2025 |
|---|---|---|
| Mindestlohn | 65.6 % | 61.9 % |
| mittlerer Lohn | 31.3 % | 31.4 % |
| hoher Lohn | 20.7 % | 21.1 % |

| Income group (2024+2025) | Share of the adult tenants | Median burden |
|---|---|---|
| under 2,000 € | 16.7 % | 53.3 % |
| 2,000 to under 3,200 € | 23.6 % | 36.1 % |
| 3,200 € and more | 59.7 % | 23.9 % |

## Formula
S1, per survey year, person and contract (`wage_table`):
1. Warm rent = (net cold rent of the Mietspiegel + Betriebskosten + Heizkosten, each € per m² and month) × 55 m². The
   net cold rents are the means of new and older contracts of `new_construction_rents`. The Nebenkosten are the actual
   running costs per m² of renting households in the Grundsicherung, June of the survey year
   (`read_nebenkosten`).
2. Gross wage per month: Mindestlohn (`MINDESTLOHN`, € per hour on the survey day) × 40 × 52 ÷ 12; the median gross
   wage of full-time employees living in Frankfurt on 31.12. of the survey year (`read_median_wage`); the pension
   ceiling of the year (`WageRules.ceiling_rv`).
3. Net wage = gross − employee contributions (pension, unemployment, health with the average Zusatzbeitrag, care with
   the childless surcharge, each up to its ceiling) − Lohnsteuer − Soli. Steuerklasse I, no children, no church tax.
   The Lohnsteuer follows the Programmablaufplan of the BMF (`model.py`). The rules of each survey day are typed
   constants with their law (`WAGE_RULES` in `sources.py`).
4. Share = warm rent ÷ net wage × 100. Left = net wage − warm rent. Left without inflation = left × 100 ÷ price index
   (2017 = 100, VPI Hessen of the survey month, from `new_construction_rents`).
5. The same table once more with the Nebenkosten of the Betriebskostenspiegel of the Mietspiegel
   (`read_mietspiegel_costs`) gives the sensitivity of the ⓘ. The reports of 2024 and 2026 print no sum. There the sum
   of 2021 moves by the own sum of the ten items of the year (an estimate).
6. `wage_facts` counts `RENT_TO` only: the ratio of the Mindestlohn share to the high-wage share over both contracts;
   the gap to the Mietspiegel variant over the cells of the year and per person.
7. `wage_view`: per contract and person of `RENT_TO` the texts of the drawing and the tooltip, in whole euros and whole
   percent with „~“. It stops if a share reaches 100 %: the block would leave its frame.
8. The ⓘ of S1 shows two written sums at the Mindestlohn, new contract (`CALC_PERSON`, `CALC_CONTRACT`): the net wage
   (`net_sum`: gross − contributions − Lohnsteuer − Soli; a part that rounds to 0 is left out) and the share
   (`share_sum`: net cold rent + Nebenkosten per m², × 55, ÷ the net wage). `wage_table` keeps these parts as columns.
   The rows are rounded, so they need not add up to the last euro: (13.95 + 4.11) × 55 = 993.30, the row shows the
   build value ~993 €. The high wage: 8,050 − 1,457 − 1,866 − 24 = 4,703 matches, the median 5,074 − 1,093 − 817 =
   3,164 against ~3,163 €. No note on the map (`docs/texts.md`, Written sums). The ⓘ of S2 shows the written sum of the
   map indicator `LIF_RENT_BURDEN_RATIO` as it comes from `survey`.

S2 (`low_income_facts`, `group_table`):
1. The burden ratio of each tenant of Leben in Frankfurt 2024 and 2025, pooled: `burden_ratios` of the use case
   `survey` (warm rent from the midpoints of the rent and cost classes ÷ household income from the midpoint of the
   equivalised income class × equivalence scale).
2. Groups by household income at `INCOME_LIMITS` (2,000 and 3,200 €). Per group: the share of the weight of all
   tenants, the weighted median ratio, the share of the group's weight in each class of `CLASSES`. The weights count
   adults. A group under `MIN_CASES` cases stops the step.
3. Sensitivity of the median and the share of the lowest group: the income placed at 0.4, 0.5, 0.6 and 0.7 of its
   closed class (`POSITIONS`) and the open lowest class at 600, 750 and 800 € (`OPEN_LOW_VALUES`).
4. Bounds of the share of the lowest group (`group_bounds`): the class bounds × the equivalence scale against 2,000 €.
   Surely under: the upper bound lies at or under the limit. At most under: the lower bound lies under it.
5. The ⓘ compares with the Mikrozensus 2018 for Frankfurt (Bruttokaltmiete ÷ household net income, mean;
   `MIKROZENSUS_2018` in `sources.py`).

## Why
- S1 is a model person, not a measured household. It answers one question: what does the same flat cost a person at
  the Mindestlohn, at the median and at a high wage? Rent, Nebenkosten, wages, taxes and prices are all published, so
  each step can be checked.
- S1 shows one year. From 2017 to 2025 the shares of new contracts barely moved (median +0.1, high wage +0.4,
  Mindestlohn −3.7 points), so a time axis carried no message. The table and the checks of the tax model keep every
  survey year.
- The Nebenkosten come from the Bundesagentur für Arbeit. It is the only series with Betriebskosten and Heizkosten per
  m² for Frankfurt in every survey year. It counts households in the Grundsicherung. The Betriebskostenspiegel of the
  Mietspiegel gives lower levels and serves as the sensitivity (in 2025 1.39 to 4.09 points lower, so 1 to 4; at the
  Mindestlohn the most).
- The median wage is the one by Wohnort on 31.12. of the survey year. Wohnort: the persons live in Frankfurt and pay
  its rents. 31.12.: the Entgeltstatistik counts on this day. The series by Wohnort lacks 31.12.2018 to 2020, so a
  mean around mid-year exists only for 2017, 2023 and 2025.
- The high wage lies at the pension ceiling. It is a legal value of every year. In Hessen 2025 it lies between the
  88th and the 89th percentile of full-time employees, so a little over 11 % earn more (`CEILING_ABOVE`). No such
  table exists for Frankfurt.
- 55 m² is the midpoint of the median class 50 to 60 m² of one-person tenant households in the survey 2024+2025.
- The median label of S2 is rounded to whole percent (53 %), not to steps of 5 like the map tooltip of the survey
  areas (55 %). The city value pooled has a 90 % interval of 52 to 55 %. The steps of 5 serve the survey areas, whose
  intervals are about ±5 points (`survey` README, Why). The small gap between the two numbers gets no note on the
  map (`docs/data-rules.md`, Rounding and coarse breakdowns).
- The ⓘ of S2 names no sampling error. Its range by the position of the income in its class (48 to 55 %) is wider
  than the 90 % interval of the sample (median 52 to 55 %, share of the lowest group 16 to 18 %; bootstrap, 400
  draws, `research/scripts/low_income_burden.py`) and contains it.
- No split by employment in S2: the medians of employed and not employed tenants are similar (51.7 against 55.0 %).
- Evidence, all numbers and every statement: `research/2026-11-01-warm-rent-and-income.md`.

## Inputs
Datasets: `new_construction_rents` (net cold rents of new and older contracts, price index), `survey_respondents`
(the respondents of both surveys), `survey_city` (the published median burden of all tenants, row
`LIF_RENT_BURDEN_RATIO`, for a check), `survey_calc_examples` (the written sum of `LIF_RENT_BURDEN_RATIO`, shown again
in the ⓘ of S2). Files in `sources/` and `reference/`, with their names in
`pipeline/config.py`:
- `BA_KDU_XLSX`: Kosten der Unterkunft (SGB II) of the Bundesagentur für Arbeit, Frankfurt, June of each survey year,
  sheet „Tabelle 1b HH Miete“ (`sources/arbeitsagentur/kdu-06412-0-<YYYY>06-xlsx.xlsx`). A survey year without its file
  stops the step. So does a file whose head names another region or another month than June of the survey year.
- `BA_WAGES_2017_XLSM`: Entgeltstatistik 31.12.2017, sheet 16.2 (median by Wohnort).
- `BA_WAGES_SERIES_XLSX`: Entgeltstatistik, sheet 9.2, the median by Wohnort 31.12.2021 to 31.12.2025.
- `MIETSPIEGEL_2018_REPORT_PDF`, `MIETSPIEGEL_2022_REPORT_PDF`, `MIETSPIEGEL_2024_REPORT_PDF`,
  `MIETSPIEGEL_2026_REPORT_PDF`: the Betriebskostenspiegel of the survey years 2017, 2021, 2023, 2025
  (`MIETSPIEGEL_COSTS` in `sources.py`, values typed by hand with their page).
- `HSL_WAGE_DISTRIBUTION_PDF`: HSL N I 9 j/25, table 2.2.4, P88 and P89 of the gross wage in Hessen, April 2025
  (`HESSEN_QUANTILES`, for a check).
- `HOUSING_MARKET_REPORT_2019_2020_PDF`: Wohnungsmarktbericht 2019/2020, figure 41, Mikrozensus 2018.
- `BMF_WAGE_TAX_CSV` (`reference/bmf_wage_tax.csv`): Lohnsteuer and Soli of the Lohnsteuerrechner of the BMF (2021,
  2023, 2025) and the Einkommensteuer of the Einkommensteuerrechner (2017), for a check.
- `WAGE_RULES` and `MINDESTLOHN` in `sources.py`: the legal rules of each survey day.

## Output
`rent_burden_wage` (S1: one row per survey year, person and contract: net cold rent and Nebenkosten per m², warm rent,
gross wage, contributions, Lohnsteuer, Soli, net wage, share, left, left without inflation), `rent_burden_groups` (S2:
one row per income group: share, median, the four classes, cases), `rent_burden_view` (payload of the view: `wage` from
`wage_view`, the wage bars of `RENT_TO`, `low_income` from `bars_view`; the map step puts it under the payload key
`rent_burden`), `rent_burden_checks`. The step logs one line per figure: the shares of 2025, and the share, bounds and
median of the lowest group.

## Checks
Every check is `FAIL`. Each statement of a heading, a lead and an ⓘ has one (`docs/data-rules.md`, Checks).
The checks are numeric and run once, with the phrases of the source language. The texts of every language take the
phrases by reference (`{@phrases.factor}`), so no check reads a text.
- net wage against BMF: the own Lohnsteuer and Soli of nine cases (2021, 2023, 2025) equal the Lohnsteuerrechner of the
  BMF to the cent. Every year of `WAGE_RULES` but 2017 needs a row for each person. The gross of each row must be the
  gross of the model, to the cent. The file names the high wage `ceiling`; the reader maps it to `high`.
- net wage tariff 2017: the own tariff and Soli of three taxable incomes equal the Einkommensteuerrechner 2017.
- rent wage heading: the Mindestlohn share ÷ the high-wage share lies within `FACTOR_RANGE` (2.5 to 3.5) in both
  contracts of `RENT_TO` (2.93).
- rent wage sensitivity: the gap to the Mietspiegel Nebenkosten in `RENT_TO`, rounded, spans `SENSITIVITY_POINTS` (1 to
  4 points), and is largest at the Mindestlohn.
- The lead has no check: its euros are the values of the table.
- rent wage ceiling: the pension ceiling of 2025 lies between P88 and P89 of Hessen, so `CEILING_ABOVE` lies within
  the percent above.
- rent wage measured: the published city value of `LIF_RENT_BURDEN_RATIO` in `survey_city` equals `MEASURED`.
- low income heading: every median of the lowest group over all sensitivities lies within 50 ± `ABOUT_HALF` (7.5)
  points.
- low income lead: the median of the highest group lies within `ALMOST_QUARTER` (20 to under 25 %).
- low income share: the share of the lowest group lies between its bounds. Under every sensitivity of step 3 it
  rounds to at most `ABOUT_SHARE` (1) whole percent from the main case (16.2 to 17.0 %, so 16 to 17).

The readers stop the build when a typed value is not in its source: every item and sum of `MIETSPIEGEL_COSTS` on its
page, P88 and P89 on page 36 of HSL N I 9 j/25, the whole row of the Mikrozensus 2018 in its order on page 63 of the
Wohnungsmarktbericht.

## Limits
- S1 is a model person. Households average 1.85 persons, and many have two incomes. The model says nothing about real
  households; the measured values do (the ⓘ names the published median of all tenants).
- Full-time employees only. Part time, Minijobs, civil servants and the self-employed are not in the median.
- The Nebenkosten of the BA are those of households in the Grundsicherung; the Mietspiegel gives lower levels. Heating
  rose by 62 % in the BA series from 2017 to 2025 and stayed flat as an item of the Mietspiegel.
- The Mietspiegel Nebenkosten of 2023 and 2025 are an estimate: the reports print no sum.
- The Mietspiegel counts contracts of the last 4 years in 2017 and of the last 6 years from 2021
  (`docs/data-rules.md`, Index of several series). The longer window lowers the means of 2021 to 2025, size unknown.
  The warm rent of 2025 is therefore a little too low.
- Selection: who moves in earns more; who cannot pay does not move or leaves the city.
- The survey weights count adults, not households. Per household the lowest group holds about 22 % of the tenant
  households instead of 16.7 % of the adults.
- The survey gives household income only in classes. The burden of S2 rests on the class midpoint. With the income
  placed elsewhere in its class the median of the lowest group lies between 48.5 and 55.4 %.
- Households whose rent the Jobcenter pays cannot be marked in the microdata. The lowest group may read too high.
- The Mikrozensus 2018 measures the Bruttokaltmiete without heating, as a mean, in nominal classes. It is a
  comparison in the ⓘ, never a line of the chart.
- The sensitivities with the median at Arbeitsort, the mean around mid-year and the flat of 50 or 60 m² run only in
  `research/scripts/warm_rent_wage.py`, not in the build. The finding gives their results.
- The check of the Mietspiegel costs finds each typed number on its page, not in its row or column. A number that
  stands twice on the page passes even if typed into the wrong item. The sums of 2018 and 2022 are typed, so the
  estimate of 2023 and 2025 rests on typed items.
- The check of the ceiling finds P88 and P89 on their page, not in their row. It holds for 2025 only; the Regel of the
  ⓘ names the share of 2025. No table of the distribution exists for Frankfurt or before 2022.
- The Vorsorgepauschale of 2017 has no check of its own; the Lohnsteuerrechner of the BMF starts with 2021. The
  contributions are part of neither calculator. Their rates and ceilings are the legal values of `WAGE_RULES`.
