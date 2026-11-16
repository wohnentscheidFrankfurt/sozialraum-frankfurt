---
title: "Count of 2011 × change up to 2022: how exact is ABG and public housing per Stadtteil?"
---

As of 10 Oct 2026. Plan: `docs/plans/2026-10-10-abg-combined-sources.md` (addendum 6: idea of the user). Script:
`analyses/abg_combined.py`. Results: `analyses/results/abg_combined_*.csv`. Previous finding:
`findings/2026-10-10-abg-estimate-accuracy.md`.

# 1. Result in short

- **The combination works for public housing (ABG and NH together).** In 27 of 41 Stadtteile the range is at most
  ±15 %. These Stadtteile hold 76 % of the public dwellings. [eigene Auswertung]
- **It still misses the tolerance.** The tolerance asks for 9 of 10 Stadtteile; the result is 2 of 3.
- **The ABG alone stays uncertain.** Only 16 of 37 Stadtteile are within ±15 %. Where the NH is large, a small ABG
  stock has a wide range.
- **The checks agree well.** Frankfurt: 69,236 public dwellings against 69,558 in table 4000W-2002 (−0.5 %). ABG
  52,403 against 54,122 in the annual report (−3.2 %; the group also owns dwellings outside Frankfurt). Gallus: ABG
  5,624 ± 251 against "rund 5.700" in the chronicle of 2015. [eigene Auswertung; belegt]
- **The research helps for new buildings, not for the old stock.** Research numbers plus estimate for the rest are
  worse than the estimate alone (55 % against 27 % in 9 of 10 Stadtteile). For new buildings up to 2021 the research
  adds 1,709 ABG dwellings the grid does not show (Riedberg, Lyoner Quartier, Unterliederbach, Höchst, Nied).

# 2. Method (estimate D)

1. **Base 2011 from the count.** The Zensus 2011 counts dwellings per owner in every cell. "Kommune" 2011 is the ABG.
   "Bund oder Land" 2011 counts as NH where the cell is municipal in 2022 or has no owner in 2022 (rule of the map).
2. **Secrecy gap of 2011, filled from 2022.** The 2011 grid hides the owner of 21,850 dwellings. Table 4000W-1011
   counts 5,047 more municipal dwellings than the grid (52,189 against 47,142), and 7,921 more public ones. The
   dwellings without an owner get the municipal share of their cell in 2022. That fills 4,916 dwellings: 97 % of the
   municipal gap. So the gap can be located. [eigene Auswertung]
3. **Change up to 2022 as a factor per Stadtteil** (idea of the user): base × (estimate 2022 ÷ estimate 2011), both
   with method E2 over the cells with public stock in 2011. The error of the method largely cancels.
4. **Cells without a public count 2011:** estimate E2 2022 (2,712 dwellings). Plus new ABG buildings of the research
   up to 2021 where E2 finds fewer dwellings in their new cells (1,709).
5. **Range per Stadtteil**, a budget, not a measured error: 16 % of the estimated change (at least the difference to
   the additive variant), plus the rest of the secrecy gap (3,005, mostly "Bund oder Land" that did not become
   municipal), spread by the dwellings without an owner that were not filled. For the ABG also half of the new
   dwellings without a research site (ABG or NH).

# 3. The research sites against the count of 2011 (step 1)

| Status | Sites | Dwellings |
|---|---|---|
| confirmed (count around the site ≥ 85 % of its number) | 21 | 4,506 |
| above the count | 14 | 9,167 |
| not found | 5 | 551 |
| no location ("O") | 4 | 2,037 |

- "Above the count" are mostly large estates: Karl-Kirchner-Siedlung, Bornheimer Hang, Römerstadt, Westhausen,
  Friedrich-Ebert-Siedlung. A radius of 350 m around one point does not cover them, and some points lie off (known
  since 8 Oct). Their numbers are also numbers of construction. So they cannot replace the count. [eigene Auswertung]

# 4. Stadtteile

Range at most ±15 % (public, with value): Bornheim 5,164, Gallus 5,736, Heddernheim 3,675, Schwanheim 3,116,
Griesheim 2,614, Ginnheim 2,403, Sachsenhausen-Nord 2,335, Ostend 2,178, Praunheim 2,169, Unterliederbach 2,149,
Bockenheim 2,045, Fechenheim 2,019, Nied 2,011, Preungesheim 1,729, Sachsenhausen-Süd 1,646, Riederwald 1,527,
Zeilsheim 1,425, Nordend-Ost 1,375, Kalbach-Riedberg 1,305, Sossenheim 1,088, Seckbach 977, Eschersheim 891,
Westend-Nord 813, Altstadt 768, Nieder-Eschbach 427, Gutleutviertel 399, Berkersheim 257.

Wider than ±15 %: Innenstadt (±53 %), Bonames (±48 %), Westend-Süd (±37 %), Hausen (±36 %), Rödelheim (±28 %),
Dornbusch (±23 %), Eckenheim (±22 %), Niederursel (±21 %), Oberrad (±21 %), Höchst (±18 %), Niederrad (±18 %),
Sindlingen (±18 %), Nordend-West (±17 %), Bergen-Enkheim (±16 %). Reasons: a large estimated change (factor 0.62 in
Innenstadt, 2.75 in Bonames, 0.74 in Rödelheim) or a large rest of the secrecy gap.

All values and ranges: `analyses/results/abg_combined_quarters.csv` (columns `public_central`, `public_half`,
`abg_central`, `abg_half`).

# 5. Limits

- The range is a budget from documented parts. It is not tested against a count of 2022; none exists per Stadtteil.
- The factor assumes the error of the method is the same in 2011 and 2022. That holds where the buildings changed
  little. Large factors mark the Stadtteile where it may not hold.
- 9,853 dwellings were added from 2011 to 2022 in cells without public stock in 2011 and without an owner in 2022.
  Some of them may be public. Only the research sites are counted there.
- Sales and purchases between ABG, NH and the Bund after 2011 are not visible (Fischstein, Hansapark: open since
  8 Oct).

# 6. Correction of the previous finding

The backtest of `2026-10-10-abg-estimate-accuracy.md` used only the 6,288 cells with buildings per owner in 2011.
There the grid holds 60,061 public dwellings, so the gap looked like 17 %. All inner cells hold 64,729 (47,142
municipal + 17,587 Bund oder Land). The gap is 7,921 (11 %).

# 7. Addendum (11.10.2026): the range in the build

The script of this finding had two slips in the range (spec `2026-10-10-public-housing-quarters-design.md`,
addendum 11). The pipeline follows the spec. The values stay the same; the ranges get narrower:

- ABG and NH together: in 35 of 41 Stadtteile at most ±15 % (not 27). These Stadtteile hold 94.5 % of the public
  dwellings in the 41 Stadtteile with at least 200 (94.3 % of all). 9 of 10 Stadtteile: at most ±16.2 %.
- Wider than ±15 %: Bonames (±48 %), Westend-Süd (±33 %), Innenstadt (±28 %), Nordend-West (±17 %), Rödelheim
  (±16 %), Bergen-Enkheim (±16 %).
- The tolerance of 9 of 10 at ±15 % is still missed narrowly (35 of 41 = 85 %).

Source of these numbers: `interim/public_housing_quarters.csv` of the build of 11.10.2026 (columns `public_value`,
`public_half`).
