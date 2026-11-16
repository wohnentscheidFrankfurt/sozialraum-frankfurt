# ownership_cells: „Eigentum je 100-m-Feld“

## Shows
No layer of its own. The estimate per cell feeds `ownership_shares`. `public_housing` computes its own estimate.
The overlay „Eigentum je 100-m-Feld“ colours each cell by the group with the most estimated dwellings, in the
colours of the view „Trend“ (`pipeline/shared/core/palette.py`). Its tooltip
starts with „Die meisten Wohnungen gehören <group in the dative> (geschätzt).“ (`GROUP_DATIVE` in `catalog.py`),
then shows counts only: the buildings 2022 per group, or the dwellings 2011 where the cell has no owner in 2022.

## Formula
1. Per ownership type: dwellings per building in Frankfurt = dwellings (table 4000W-2002) ÷ buildings in the grid.
2. Per cell: buildings per type × that factor, scaled to the dwellings of the cell.
3. Cells without a building with a known owner in 2022 get the dwellings per type of 2011, at most as many as in
   2022. „Bund oder Land“ 2011 counts as municipal there: the Zensus 2022 counts the Nassauische Heimstätte as
   municipal.
4. Dwellings without a type stay `dw_unassigned`.

## Why
The grid of 2022 counts the ownership type per building, so a block of 80 dwellings would count like a single-family
house. The estimate therefore converts buildings into dwellings. The grid of 2022 hides the values 1 and 2, so a cell
with only one or two large houses has no ownership type; it gets the dwellings of 2011. In the tooltip of the overlay
every number is a count, only the colour is estimated. Per cell the estimate is less sure than per Stadtteil, and
numbers per street get quoted.

## Inputs
`cells_2022`, `cells_2011_dwellings`; file `sources/zensus/Zensus2022_4000W-2002_Frankfurt_2011_2022.csv`.

## Output
`ownership_cells` (per cell `dw_<type>`, `dw_unassigned`, `dw_from_2011`, `dw_nh_2011`),
`ownership_grid_cells` (rows of the overlay: south, west, height, width as integers in degrees × 100000, colour group,
flag, counts per group; flag 0 = buildings 2022, flag 1 = the cell has no owner in 2022 and the counts are dwellings
2011), `ownership_cells_checks`.

## Checks
- Ownership: assigned plus unassigned equals the dwellings of the grid (± 1).
- Ownership: no ownership type, at most 5 % of the dwellings (WARN).

## Limits
- The factor „Wohnungen je Gebäude“ of a type divides by the buildings of the type in the 100-m grid (`grid_factors`).
  Table 3000G-2007 counts more buildings, for example 577 against 528 for Bund oder Land. The factor is therefore
  higher than a factor from that table. It stays on the grid: the grid is what the map divides, and another factor
  would not reproduce the shares.
- Per cell the estimate is uncertain. Backtest 2011: main group right in 96 % of the cells, where ABG and NH lead in
  74 % (`research/results/formula_review.txt`).
- Large buildings of small groups are missed (Hausen 2011: 715 dwellings of an Organisation ohne Erwerbszweck,
  estimated 7).
- Many cells hold exactly 10 estimated dwellings, and their sum can differ in the last digit of a float. The overlay
  compares the sum rounded to 6 decimals (`THRESHOLD_DECIMALS` in `model.py`), so such a cell is always shown and
  float noise does not decide.
- Cells without owner 2022 show the classes of 2011: the NH is „Bund oder Land“ there, while the colour counts it as
  public.
