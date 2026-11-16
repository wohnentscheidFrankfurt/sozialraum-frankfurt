# public_housing: „ABG und Nassauische Heimstätte“

## Shows
`OWN_PUBLIC` (share, estimated, shown with a tilde; the share is computed in `ownership_shares` with the common
denominator). Stadtteile only. The data keep the range. The count of dwellings lives in `ownership_shares` as
`OWN_PUBLIC_DWELLINGS` (equals `public_value`).

## Formula
1. Base: dwellings counted 2011. „Kommune“ is the ABG. „Bund oder Land“ counts as NH where the cell is municipal in
   2022 or has no owner in 2022.
2. Secrecy gap 2011: dwellings without owner get the municipal share of their cell in 2022.
3. Change up to 2022 per Stadtteil: base × (estimate 2022 ÷ estimate 2011), both with buildings per owner and size
   (`estimate_by_size`), over the cells with public stock in 2011.
4. Cells with public stock in 2011 and no owner in 2022: the base, scaled down where the cell has fewer dwellings in
   2022 than in 2011.
5. Cells without public stock in 2011: estimate 2022. ABG new buildings of the research up to 2021 count where the
   grid shows fewer.
6. Range: 16 % of the estimated change plus the rest of the secrecy gap. The first part is at least the difference
   to an additive formula: base + (estimate 2022 − estimate 2011).

Worked example (Rechnung of the ⓘ, Niederrad, `public_calc_example`): count 2011 (ABG + NH) of the cells with an
owner in 2022 (`scaled_2011`) × factor of the change (2 decimals) = subtotal; + dwellings of 2011 whose cell has no
owner in 2022; + dwellings at new sites since 2011; = value; ÷ all dwellings = share. The subtotal is the scaled count
of the build (`abg_scaled` + `nh_scaled`). The new sites are the cells of step 5 and the ABG new buildings of the
research (`new` + `research_new`). The row without owner is the value minus the other rows, so the sum closes.
Niederrad has large fills: the reader sees why the sum needs them. Riederwald, with the highest share, has only 8
dwellings without owner and 12 at new sites. Without the fills, 13 of 45 Stadtteile change the class of the map;
Kalbach-Riedberg loses 13 points, Niederrad 9.5 (`research/2026-10-22-public-housing-fills.md`).
The sum stands alone, with no note: a note that repeats the rows in prose doubles the reading. What the ⓘ leaves out:
- The count 2011 holds the filled secrecy gap (step 2), so it has a „~“. Niederrad: 258 of the 3,336 dwellings.
- The factor comes from the buildings 2011 and 2022 (step 3). Niederrad: 0.9098, so 3,336 × 0.91 (3,036) is not the
  subtotal 3,035.
- The row without owner holds the cells of step 4 (741) and the municipal share of the secrecy gap (3).
- „Neue Standorte“ are cells without public stock in 2011. In Frankfurt 1,733 of the 2,714 dwellings of step 5 lie
  in cells without dwellings in 2011, so they are new buildings. 981 lie in cells with dwellings in 2011: the Zensus
  hid their owner (704) or the owner changed. Niederrad: 301 of 320 in cells without dwellings in 2011.
- The tooltip rounds the count to 50. Niederrad: ~4,500 in the tooltip, ~4,504 in the sum. For the map that is
  fine: it sorts areas for housing policy, roughly.

## Why
The estimate per cell missed public ownership per district by about 30 % in 9 of 10 areas
(`research/2026-10-10-abg-estimate-accuracy.md`). The count of 2011 times the change up to 2022 is much closer
(`research/2026-10-10-abg-combined-sources.md`). So the map shows ABG and Nassauische Heimstätte together and only per
Stadtteil. The change factor fits ABG and NH, but not the Genossenschaften: their stock really changed after 2011
(municipal +33 %: NH moved, new buildings), and only 9 % of their dwellings of 2011 lie in cells without a municipal
building in 2022 (coops: 29 %). The error in Bonames is accepted: its range shows the doubt, and a special rule would
make the formula longer.

## Inputs
`cells_2022`, `cells_2011_dwellings`, `cells_2011_buildings`; files in `sources/zensus/`: tables 3000G-2007, 4000W-2013,
4000W-1011, 4000W-2002; `sources/other/ABG-Holding-Karte.geojson`; `reference/check_reference.csv`.

## Output
`public_housing_quarters` (working columns per Stadtteil, with `public_value` and `public_half`),
`public_housing_checks`.

## Checks
- Frankfurt against table 4000W-2002 (Kommune), ± 3 %.
- ABG against the group report 31.12.2022 (WARN, ± 10 %); Gallus against the ABG chronicle 2015 (WARN, ± 15 %).
- The secrecy fill covers 80 to 110 % of the municipal gap of the 2011 grid (WARN).
- Value and range are not negative.
- Agreed tolerance: in 9 of 10 Stadtteile with at least 200 dwellings the half range is at most 15 % of the value.
  ABG and NH meet it in 35 of 41 Stadtteile. The user accepted that share (`ACCEPTED_AREAS`). The check is OK down
  to that share and warns below. A check that always warns would hide a new warning.

## Limits
- Bonames: factor 2.76 although the dwellings stay the same; range ± 48 %.
- Sales between ABG, NH and the Bund after 2011 are not visible.
- The range is a budget, not measured on 2022. Of 4,148 dwellings added up: 757 from the backtest, 392 from
  the difference to the additive formula, 2,999 (72 %) from the unfilled secrecy gap 2011. The ⓘ names the
  smallest to largest half range and the secrecy gap as its main cause.
  (`research/2026-10-12-uncertainty-of-ownership.md`, `research/results/uncertainty_scenarios.txt`).
