# ownership_shares: „Genossenschaften“, „Private Unternehmen“, „Privatpersonen und WEG“, „Bund oder Land“, „Organisationen ohne Erwerbszweck“

## Shows
The five groups `OWN_COOP`, `OWN_COMPANY`, `OWN_PERSON`, `OWN_STATE`, `OWN_NONPROFIT` and `OWN_PUBLIC`, each with
`_LOW` and `_HIGH`; `COV_OWN`; per Stadtteil only (Why). Districts get only the building counts `BLD_*`. Texts of
`OWN_PUBLIC` in `public_housing`, of `OWN_COOP` in `coops`. Frankfurt: the shares without range.
Per Stadtteil also the dwellings of each group (`<group>_DWELLINGS`, `_LOW`, `_HIGH`: share ÷ 100 × all dwellings,
not rounded). The map tooltip of each ownership layer shows the count of its group; the ⓘ of the layer explains it
(`tip_dwellings_*` in `shared/core/texts.de.yaml`). The map payload keeps `<group>_DWELLINGS` and `_HIGH` unrounded;
the browser rounds to 50. The exports round all three columns to 50.
The Rechnung of each of the six groups shows a worked example as a written sum, for one fixed Stadtteil per group
(`CALC_EXAMPLE_QUARTERS` in `catalog.py`; one with a high share, see `docs/texts.md`). The rows are rounded numbers
of the build.
The tooltip row of a layer adds the rounded count of the Stadtteil. The tooltip adds the coverage sentence where the
coverage is under 90 %.

## Formula
1. All dwellings of a Stadtteil = `dwellings` of `cells_2022`, summed over its cells. This is the one denominator of
   all six groups. `COV_OWN` uses the same denominator.
   Known dwellings = sum of the estimate per cell (`ownership_cells`, `estimated_dwellings`), without the dwellings
   without owner type. They are only the weight of the four other groups.
2. `OWN_PUBLIC` = dwellings of ABG and NH (`public_housing`) ÷ all. `OWN_COOP` = Genossenschaften (`coops`) ÷ all.
3. Rest = all − ABG and NH − Genossenschaften. The four other groups split the rest in proportion to their estimate.
   So the dwellings without owner type go to the four other groups, in proportion.
4. Share = dwellings of the group ÷ all.
5. Range = share ± half range, bounded to 0 to 100. ABG, NH and Genossenschaften: the half range of their use case ÷
   all. The four other groups: fixed points (`HALF_POINTS`: 3.5, 5.4, 1.4 and 2.0).
   The ⓘ names the backtest: in 40 of 45 Stadtteile within the half range (`BACKTEST_HITS`, `BACKTEST_AREAS`).
6. Dwellings of a group = share ÷ 100 × all dwellings. ABG and NH equal `public_value` of `public_housing`,
   Genossenschaften equal `coop_value` of `coops`. Half range in dwellings: `public_half`, `coop_half`; the four other
   groups `HALF_POINTS` ÷ 100 × all. `_LOW` is clipped at 0, `_HIGH` is not bounded.
   The map writes „k. A.“ without a value, „unter 200“ where `_HIGH` is under 200, „~“ and the value rounded to 50
   where the half range is at most one third of the value, else „unsicher“ (in this order).
7. `COV_OWN` = dwellings with an estimated owner ÷ all dwellings. `BLD_*` = counted buildings 2022.
8. Frankfurt: the same over all cells of the Stadtteile, with the sums of ABG, NH and Genossenschaften over all
   Stadtteile.
9. Worked example of a group (`other_calc_example`, `coop_calc_example`, `public_calc_example`): the buildings of the
   Stadtteil × dwellings per building of the type (`grid_factors`) = dwellings after the average. × adjustment factor =
   dwellings in the 100-m fields. + dwellings from 2011. = dwellings of the group. ÷ all dwellings („alle Wohnungen“) =
   share. The adjustment factor is (dwellings of the group − row of 2011) ÷ product, with 2 decimals. For the four other
   groups it also holds their part of the dwellings without owner type. Genossenschaften and ABG and NH show their own
   rows. ABG and NH: count of 2011 × factor of the change = subtotal; + dwellings of 2011 without owner in 2022; + new
   sites since 2011; = dwellings 2022 (`public_housing` README). A result row shows the value of the build, rounded,
   with „~“. There is no arithmetic check. The step fails with the name of a missing example Stadtteil
   (`require_example_quarters`). The sum is the whole Rechnung of the ⓘ: no note under it, no sentence on the tooltip,
   `calc` stays empty. A reader can redo a sum, not a prose Rechnung. What the ⓘ leaves out: ABG, NH and
   Genossenschaften are computed apart (step 2); the four other groups split the rest by their estimate (step 3), and
   the adjustment factor holds that split. The tooltip rounds the count to 50, so it can differ from the sum.

## Why
The shares answer where Genossenschaften and private companies own dwellings. They count dwellings, not buildings
(`pipeline/use_cases/ownership_cells/README.md`).
- Per Stadtteil only: the backtest on 2011 errs more per district (private companies ±60 % against ±49 % per
  Stadtteil). One rule holds for all ownership groups.
- Fixed half ranges in points for the four other groups: one simple rule. It held the counted value in 40 of 45
  Stadtteile for each group. Relative ranges would read ±42 % and more for small groups.
- The layer „Private Unternehmen“ stays despite its range: it is the only view of companies per Stadtteil. It counts
  dwellings, not houses: companies own 8 % of the houses but 19 % of the dwellings.
- The denominator is all dwellings, because ABG, NH and Genossenschaften are near-complete counts. Divided by the
  dwellings with a known owner, their shares would be too high. So count and denominator cover the same dwellings.
- The four other groups take the dwellings without owner type in proportion. Table 4000W-2002 shows them short, and a
  split in proportion is the neutral assumption. One group as the rest would carry all errors (up to 28 % per
  Stadtteil).
- The examples in the ⓘ of `OWN_COMPANY` make the group imaginable: Vonovia, the GWH and two funds. Deutsche Wohnen
  is not named apart: it belongs to Vonovia, and the 16,000 dwellings of Vonovia include its stock. No number comes
  from a party document.

## Inputs
`cells_2022`, `ownership_cells`, `public_housing_quarters`, `coops_quarters`; files `sources/frankfurt/geodata/`
(Stadtteile), `sources/zensus/Zensus2022_4000W-2002_Frankfurt_2011_2022.csv` and the sources of the examples in the ⓘ of
`OWN_COMPANY` (`EXAMPLES` in `catalog.py`; paths in `pipeline/config.py`, read by `shared/readers/html.py`).

## Output
`ownership_shares_by_district`, `ownership_shares_by_quarter`, `ownership_shares_city`, `ownership_ranges`
(smallest and largest half range per group, points), `ownership_shares_checks`, `ownership_calc_examples`
(`{indicator_id: payload}` of the worked examples). `ownership_shares_by_quarter` holds the columns
`<group>_DWELLINGS`, `_LOW` and `_HIGH` for the six groups. The city has no counts.

## Checks
- The shares per Stadtteil add up to 100 % (± 0.1).
- The rest after ABG, NH and Genossenschaften is not negative in any Stadtteil.
- The range in the data is the value ± the half range of `ownership_ranges`, bounded to 0 to 100 (FAIL).
- `check_dwellings`: the counts per group give the shares again (100 × count ÷ sum of the six counts, ± 0.1 points;
  FAIL).
- `check_dwellings_total`: the six counts add up to all dwellings of each Stadtteil (± 0.5 dwellings; FAIL).
- City share of each group against table 4000W-2002 (WARN, ± 2 points).
- The share of table 4000W-2002 lies within the city value ± the half range of Frankfurt (WARN). In the current
  build all six groups lie inside. Genossenschaften 3.38 against 3.21 (± 0.23), ABG und NH 17.73 against 17.27
  (± 1.06).

- Every example in the ⓘ of `OWN_COMPANY` (`EXAMPLES` in `catalog.py`) stands in its source: Vonovia with its number and
  date in its press release (the number stands only in the phrase of `EXAMPLES`, not in the ⓘ), GWH in F 3283/2025,
  Helaba in the GWH annual report 2022, Industria Wohnen and Hamburg Trust in saved web pages (FAIL).

## Limits
- The counts of the four other groups follow from the shares and inherit their fixed half range in points. In large
  Stadtteile that is many dwellings (Gallus, private companies ± 804).
- The ranges hold the error of the split. The dwellings without owner type (11,533 of 390,491) add an error the
  backtest cannot measure. The backtest uses the 2011 cells with a known owner only, where all dwellings and the known
  dwellings are the same set.
- Where the rounded coverage (`COV_OWN`) is under 90 %, the tooltip and the profile say so: „Nur N % der Wohnungen
  sind einer Eigentumsform zugeordnet.“ This holds for Bahnhofsviertel, Niederursel and Gallus.
- The grid holds 3 % fewer dwellings than table 4000W-1008 (390,491 against 402,826). This gap is accepted.
- Bonames shows no ABG and NH count: 532 ± 255 reads „unsicher“.
- The ranges are budgets from a backtest on 2011, not measured on 2022 (`research/results/formula_review.txt`).
- The two funds are examples from 2014 and 2019; whether they
  still hold the buildings is not checked. The Zensus class of the GWH is reported by the owner; by the definition
  it is a privatwirtschaftliches Wohnungsunternehmen (private law, Länder under 50 % of the Helaba).
- Large buildings of small groups are missed: Hausen, Organisationen ohne Erwerbszweck 715 dwellings in 2011,
  estimated 7.
