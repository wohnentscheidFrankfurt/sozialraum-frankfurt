# housing: „Mieteranteil“, „Miete im Bestand“, „Leerstand“

## Shows
`HOU_RENTERS`, `HOU_RENT`, `HOU_VACANT_MARKET`, `HOU_VACANT_ALL`; the counts `HOU_VACANT_MARKET_DWELLINGS`,
`HOU_VACANT_ALL_DWELLINGS` (tooltip line „Leer stehende Wohnungen“); coverage `COV_HOU_*` (check report).
Districts and Stadtteile. Mieteranteil and Miete stand in the topic „Miete“, the vacancy in „Wohnungsbestand“.

## Formula
Mean of the cells of the area (cell by its centre), each weighted by its base:
- Mieteranteil = 100 − Eigentümerquote, weighted by occupied dwellings; „–“ counts as 0 % owners (Zensus: „Genau
  Null oder auf Null geändert“).
- Miete im Bestand: net cold rent per m², weighted by rented dwellings; cells with „–“ do not count.
- Leerstand (`HOU_VACANT_ALL`): vacant dwellings ÷ dwellings in residential buildings without dormitories, weighted
  by dwellings. „–“ does not count as 0 but is filled (below).
- Leerstand marktaktiv (`HOU_VACANT_MARKET`): the same, but only vacant dwellings available within three months.
- Filling of „–“ from the 1-km grid: per 1-km cell, the vacant dwellings the 1-km rate implies
  (rate × dwellings of all 100-m cells in it, inner and edge) minus the vacant dwellings of the cells with a value are
  spread over the „–“ cells, by their dwellings. A negative rest gives them 0. A 1-km cell without a „–“ cell keeps its
  values. The map then averages the inner cells per area. Same for both rates. The filled `vacancy_rate` also weights
  Mieteranteil (occupied dwellings). The Eigentümerquote is not filled: the city value equals the table, the rest is
  negative in 65 of the 216 1-km cells (`research/scripts/qa_vacancy_fill.py`).
- Vacant dwellings (`HOU_VACANT_ALL_DWELLINGS`, `HOU_VACANT_MARKET_DWELLINGS`): sum over the inner cells of the area
  of the filled rate ÷ 100 × dwellings (the same cells, rates and weights as the share). A missing rate or missing
  dwellings count 0; an area without any rate has no count. No city value (the count is not shown for the city).
  The map rounds the count to 10 and writes „unter 10“ below it.
- Both vacancy layers are estimates (tilde in the map).
- Miete im Bestand shows one decimal.
Coverage = share of the base that has a value (for vacancy 99.8 % after filling: cells missing in the file).

## Worked example
The ⓘ of `HOU_VACANT_ALL`, `HOU_VACANT_MARKET` and `HOU_RENTERS` shows the Rechnung as a written sum for one Stadtteil.
The sum is the whole Rechnung: `calc` stays empty. Regel and Unsicherheit stay as they are.
- Stadtteil: one with a high share, fixed in `CALC_EXAMPLE_QUARTERS`
  (`catalog.py`). Innenstadt (all), Bahnhofsviertel (market), Riederwald (renters). A high share gives large, readable
  rows. The step fails with the name of a missing Stadtteil (`require_example_quarters`).
- Vacancy (`vacancy_calc_example`, parts from `vacancy_parts`): vacant dwellings in the cells with a value („in den
  100-m-Feldern“) + vacant dwellings the 1-km grid puts into the „–“ cells = vacant dwellings, the count of the tooltip
  (the tooltip rounds it to 10). ÷ dwellings of the cells with a rate = the share. Where the 1-km part rounds to 0,
  its row and the total row go; the first row then shows the rounded count.
- Renters (`renters_calc_example`, parts from `renter_parts`): occupied dwellings of the cells with an Eigentümerquote
  − owner-occupied dwellings (Eigentümerquote × occupied, per cell) = dwellings not occupied by their owners. ÷ occupied
  dwellings = the share.
- Rows are rounded to whole dwellings. A total row is the rounded value of the build, not the sum of the rounded rows.
  The last row is the value of the map with one decimal; „~“ as the indicator (vacancy yes, renters no).
- The sum leaves out the rule that a field belongs to the area of its midpoint. The Unsicherheit names it (fields on
  a border count wholly to one area).
- The step writes the examples to `housing_calc_examples` (id → payload), from the same inner cells and filled rates
  as `housing_by_quarter`.

## Why
Renters, rent and vacancy describe the burden and the stock of an area. Both vacancy rates are shown, because they count
different things: the market-active rate counts dwellings free within three months. The layer „Wohnfläche je Kopf“
is not shown: the doubt about the grid value could not be resolved (Limits).

## Inputs
`cells_2022` (with the flags `vacancy_rate_dash` and `vacancy_rate_market_dash`: 1 where the 100-m grid shows „–“); the
1-km extracts `GRID_KM_EXTRACTS` (`Leerstandsquote`, `marktaktive_Leerstandsquote`); file
`sources/zensus/Zensus2022_4000W-2002_Frankfurt_2011_2022.csv` (vacancy); files
`sources/zensus/Zensus2022_4000W-0001_Frankfurt_2011_2022.csv` (Eigentumsquote) and
`Zensus2022_4000W-0004_Frankfurt.csv` (Nettokaltmiete), one value for Frankfurt on 15.5.2022 (the file 0001 also holds
the vacancy rate `WHG009$QMU`, 3.1 %);
`reference/check_reference.csv` (1-km grid).

## Output
`housing_by_district`, `housing_by_quarter`, `housing_city`, `housing_checks`, `housing_calc_examples`
(worked example per indicator).

## Checks
- City vacancy against table 4000W-2002 (WARN, ± 1 point).
- City vacancy against `WHG009$QMU` in 4000W-0001, 3.1 % (WARN, ± 0.15 points).
- Both vacancy rates against the 1-km grid (`reference/check_reference.csv`, WARN beyond ± 0.2 points).
- City count of `HOU_VACANT_ALL_DWELLINGS` against table 4000W-2002 (`WHG002$ID0004`, `NUTZ-LEER`, `%TOTAL%`,
  15.5.2022: 12,893; WARN beyond ± 10 %).
- Mieteranteil and Miete against tables 4000W-0001 and 4000W-0004 (± 2 % relative).

## Limits
- The 100-m grid shows less vacancy than the 1-km grid, because it sets small numbers to „–“. The filling brings the
  city to 3.08 % and 1.84 %. Per area it is an estimate: it spreads the rest of the 1-km cell evenly by dwellings.
- A 1-km cell with a negative rest cannot be balanced; the „–“ cells get 0 there. The build has 15 of 216 such cells
  for `vacancy_rate` (45.8 dwellings) and 8 of 216 for `vacancy_rate_market` (47.1 dwellings).
- The city count of the grid is 12,016, 6.8 % below the table (12,893). Both factors lie lower. The grid
  holds 390,491 dwellings against 402,393 occupied and vacant dwellings in the table (−3.0 %). The grid rate is 3.08 %
  against 3.20 % (−4.0 %). It refers to residential buildings without dormitories and matches WHG009 (3.1 %). The
  counts per area therefore lie slightly low; the check allows ± 10 %.
- The weights (all dwellings against residential buildings without dormitories) stay as they are.
- Wohnfläche je Kopf is not shown: the grid lies about a fifth above the Zensus table (47.6 against 38.3 m² for
  Frankfurt), for Germany too. The cause lies in the source and cannot be proven
  (`research/2026-10-12-living-space-grid.md`, `research/results/space_check.txt`).
