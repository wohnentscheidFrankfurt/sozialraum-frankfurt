# coops: „Genossenschaften“

## Shows
`OWN_COOP` (share, estimated, shown with a tilde; the share is computed in `ownership_shares` with the common
denominator). Stadtteile only; districts have no value.

## Formula
Per cell, „old“ = cell with coop dwellings counted in 2011:
1. (a) counted 2011: the coop dwellings of 2011 where old.
2. (b) gap 2011: dwellings without owner in 2011 × coop share of the cell in 2022 (`dw_coop ÷ dwellings`), where old
   and the cell has buildings with an owner in 2022.
3. (c) estimate 2022 (`dw_coop` of `ownership_cells`) where not old.
Per Stadtteil: value = a + b + c. Half range = 34 % of b + c; the counted part has none.
The ⓘ names the largest half range in percentage points over the Stadtteile.

Worked example (Rechnung of the ⓘ, Riederwald, `coop_calc_example`): a + b + c (row c only where it is not 0) =
value; ÷ all dwellings = share. The sum stands alone, with no note: a note that repeats the rows in prose doubles
the reading. What the ⓘ leaves out:
- Row b exists because the Zensus 2011 names no owner for part of the dwellings, for data protection.
- Row c is 0 in Riederwald. Elsewhere the map estimates the dwellings from the buildings of 2022 where no coop was in
  2011.
- The tooltip rounds the count to 50. Riederwald: ~850 in the tooltip, ~868 in the sum.

## Why
The coop stock barely changed after 2011 (table 4000W-1011: −3.4 %); 2011 counts dwellings, 2022 only buildings. So
the value starts from the count of 2011. A change factor would measure what the 2022 grid hides, not real change
(Nieder-Eschbach: factor 0.00 for 262 coop dwellings of 2011). Part (c) keeps the coop buildings the 2022 grid counts
in cells without a coop in 2011; dropping it would ignore counted buildings. The half range of 34 % is the error of
the estimate per Stadtteil in 9 of 10 Stadtteile of the backtest on 2011.

## Inputs
`cells_2022`, `cells_2011_dwellings`, `ownership_cells`; `sources/zensus/Zensus2022_4000W-2002_Frankfurt_2011_2022.csv`.

## Output
`coops_quarters` (counted_2011, gap_2011, estimate_2022, coop_value, coop_half per Stadtteil), `coops_checks`.

## Checks
- Frankfurt against table 4000W-2002 (Wohnungsgenossenschaft), ± 3 %.
- Value and range are not negative.
- Agreed tolerance: in 9 of 10 Stadtteile with at least 200 coop dwellings the half range is at most 15 % of the
  value (WARN).

## Limits
- Sales and demolition after 2011 are not visible; city-wide the stock fell by 3.4 %.
- The 2011 grid hides 2,780 coop dwellings; (b) locates 45 % of them. The rest may sit in (c). Not provable.
- The range is a budget from a backtest on 2011, not measured on 2022. Source: `research/results/formula_review.txt`.
