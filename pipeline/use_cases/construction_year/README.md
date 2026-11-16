# construction_year: „Altbau vor 1919“, „Nachkriegsbau 1949–1978“

## Shows
`HOU_PRE1919`, `HOU_1949_1978` (shares) and `HOU_PRE1919_DWELLINGS`, `HOU_1949_1978_DWELLINGS` (counts, rounded to 10,
a line of its own in the tooltip of the share by `count_of`: „Altbau vor 1919: ~41,2 %“, below it „Wohnungen: ~3.120“;
the Regel of the share ends with the rounding sentence). The profile shows the share only. Districts and Stadtteile.

## Formula
1. Dwellings in buildings of the class, counted in the Zensus 2011 grid (feature BAUJAHR_MZ, codes 01 and 03).
2. Per 100-m cell: `class_cell = min(class_2011, dwellings_2022)`. A missing 2011 count is 0.
3. Count = Σ `class_cell` over the cells of the area. Share = that count ÷ Σ dwellings of the 2022 grid.
4. Cells without a 2022 cell drop out. Both values are estimates (the map writes „~“).

## Worked example
The ⓘ of `HOU_PRE1919` and `HOU_1949_1978` shows the Rechnung as a written sum for one Stadtteil.
The sum is the whole Rechnung: `calc` stays empty. Regel and Unsicherheit stay as they are.
- Stadtteil: one with a high share, fixed in `CALC_EXAMPLE_QUARTERS`
  (`catalog.py`). Nordend-Ost (before 1919), Altstadt (1949–1978). A high share gives large, readable rows. The step
  fails with the name of a missing Stadtteil (`require_example_quarters`).
- Rows (`construction_calc_example`, parts from `construction_parts`): dwellings of the class in the Zensus 2011 grid
  − dwellings above the dwellings of 2022 in the same 100-m cell (the cap) = dwellings of the class, the count of the
  tooltip (the tooltip rounds it to 10). ÷ all dwellings of 2022 = the share.
- Where the cap rounds to 0, its row and the total row go. The first row then shows the capped count.
- Rows are whole dwellings. The total row is the value of the build, not the sum of the rounded rows. The last row is
  the value of the map with one decimal, „~“ as the indicator.
- The sum leaves out the field sum and the midpoint rule (the Stadtteil is cut from 100-m cells at their midpoints).
  Unsicherheit of the ⓘ states both.
- The step writes the examples to `construction_year_calc_examples` (id → payload), from the same inner cells as
  `construction_year_by_quarter`.

## Why
The map shows where old stock stands that needs energy refurbishment, and where Gründerzeit housing stands.
„Nachkriegsbau 1949–1978“ was built before the first Wärmeschutzverordnung (in force 1.11.1977). „Altbau vor 1919“ is
the class closest to the Gründerzeit. Dwellings count, not buildings: a large block from 1965 would else count as much
as a single-family house. The share divides by the dwellings of 2022, because the 2011 grid misses everything built
since. The cap per cell removes dormitories: the 2011 grid counted them as dwellings, the 2022 grid does not.
Example cell `CRS3035RES100mN3002900E4222800` (Hausen): 723 dwellings in 2011, 717 of them 1949–1978, 16 in 2022.
Without the cap Hausen showed 86,2 % 1949–1978, the top value of the map. With it: 61,7 %.
The tooltip rounds the counts to 10, because the 2011 grid changes small values for secrecy.

## Inputs
`cells_2022`, `cells_2011_dwellings`; file `sources/zensus/Zensus2022_4000W-1008_Frankfurt_2011_2022.csv`.

## Output
`construction_year_by_district`, `construction_year_by_quarter`, `construction_year_city`, `construction_year_checks`,
`construction_year_calc_examples` (worked example per class).

## Checks
- Grid 2011 against table 4000W-1008 per class (tolerance 6 % before 1919, 2 % 1949–1978, 1 % in total).
- City share (capped) against the table 2022: 16,4 % against 16,6 % before 1919, 45,6 % against 47,1 % 1949–1978. The
  tolerance is 2,0 points, because new dwellings in old buildings since 2011 are missing in the estimate.
- The grid checks use the uncapped 2011 grid. They test the reading of the grid.

## Limits
- Dwellings demolished since 2011 still count, as long as the cell has dwellings in 2022.
- New dwellings in old buildings since 2011 (conversions, attics) are missing. The shares lie a little low.
- The Zensus 2022 has the year of construction only for buildings, not for dwellings. A building share gives 39,8 %
  instead of 47,1 % for 1949–1978 and is not used.
- A cell on an area border counts wholly to one area. In small districts that can move the value.
- After complete destruction the Zensus counts the year of rebuilding (Altstadt mostly 1949–1978).
- Before 1919 also holds buildings before 1870.
