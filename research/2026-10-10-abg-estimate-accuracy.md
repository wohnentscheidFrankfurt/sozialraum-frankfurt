---
title: "How exact is the estimate of ABG and public housing per area?"
---

As of 10 Oct 2026. Plan: `docs/plans/2026-10-10-abg-estimate-accuracy.md`. Scripts: `analyses/abg_accuracy_extract.py`,
`analyses/abg_accuracy.py`. Results: `analyses/results/abg_accuracy_*.csv`.

Tolerance agreed with the user before the test: a value is shown as a number if in 9 of 10 areas (areas with at least
200 dwellings of the group) the estimate lies at most 15 % from the count, and at most 3 share points in all areas.

# 1. Result in short

- **No estimate passes the tolerance.** This holds for the ABG and for ABG and NH together, per district and per
  Stadtteil.
- **ABG per Stadtteil: 27 % in 9 of 10 Stadtteile** with the best method. Far above 15 %. The split ABG/NH adds an
  error on top that the test cannot measure.
- **ABG and NH together per Stadtteil: 15.5 % (E1) to 16 % (E2), at most 4.1 share points.** Just above the
  tolerance.
- **Per district everything stays at about 30 %.** Better methods do not help there.
- **Classes work.** With four classes (under 5 %, 5–15 %, 15–30 %, 30 % and more) the estimate hits the right class in
  89 % of the Stadtteile for ABG and NH together. No Stadtteil is off by more than one class.
- **The 2022 grid loses municipal dwellings.** All methods find fewer municipal dwellings than the city count of the
  Zensus (61,391 to 63,370 against 69,558). The map gets 67,342 because it fills cells without an owner from 2011.
- **Nobody publishes a number per Stadtteil.** The city's own analysis of the census 2022 (statistik.aktuell 13/2024)
  gives only the city value (10.7 % of the residential buildings).

# 2. The test

- The 2022 grid counts buildings per owner, not dwellings. In 2011 the grid counts both. So every method can run on
  the buildings of 2011 and be compared with the counted dwellings of 2011. [eigene Auswertung]
- 2011 "Kommune" stands for the ABG: the NH was "Bund oder Land" then. "Kommune" plus "Bund oder Land" stands for ABG
  and NH together.
- The test measures the error of the method. It does not measure the split ABG/NH, nor the gaps of the 2022 grid.
- Both sides of the test come from the grid. The test uses the 6,288 cells with buildings per owner in 2011. All
  inner cells of the 2011 grid hold 64,729 public dwellings (Kommune + Bund oder Land); table 4000W-1011 counts
  72,650. The 11 % that secrecy hides are not in the test. (Corrected on 10 Oct: first written as 17 %, from the
  6,288 cells only; see `2026-10-10-abg-combined-sources.md`.)
- The counts of 2011 are not exact either. Secrecy changes small numbers. District 373 (about 190 dwellings) shows 13
  municipal dwellings but municipal buildings for almost all of them. That outlier is 89 share points.

Methods:

- **E0**, the method of the map: buildings per owner × dwellings per building of that owner in Frankfurt, scaled to
  the dwellings of the cell.
- **E1**: also uses the buildings per number of dwellings (1, 2, 3–6, 7–12, 13 and more) in the cell, with the city
  table of owner × size (3000G-2007, 4000W-2013).
- **E2**: as E1, plus the dwellings per building of the cell in the classes 3–6, 7–12 and 13 and more
  (Gebäudetyp-Größe).

# 3. Error in 9 of 10 areas

Areas with at least 200 dwellings of the group. "Share points": largest error of all areas.

| Group | Level | E0 | E1 | E2 | Share points (E2) | Right class (E2) |
|---|---|---|---|---|---|---|
| ABG (2011: Kommune) | district | 27 % | 28 % | 28 % | 89 (district 373) | 89 % |
| ABG (2011: Kommune) | Stadtteil | 38 % | 27 % | 27 % | 4.1 | 93 % |
| ABG and NH | district | 31 % | 30 % | 30 % | 89 (district 373) | 85 % |
| ABG and NH | Stadtteil | 26 % | 15.5 % | 16 % | 4.1 | 89 % |
| Genossenschaften | district | 43 % | 24 % | 24 % | 7.3 | 90 % |
| Genossenschaften | Stadtteil | 40 % | 32 % | 33 % | 5.3 | 96 % |

[eigene Auswertung]

- Size classes help per Stadtteil, not per district. The remaining error comes from cells where municipal and private
  large buildings stand side by side. The grid gives no hint which of them has more dwellings.
- The Genossenschaften layer has the same problem. Its ⓘ gives no accuracy today.

# 4. 2022

- Municipal dwellings in Frankfurt: E0 63,370, E2 61,391, map 67,342, table 4000W-2002 69,558. [eigene Auswertung;
  belegt: 4000W-2002]
- Public dwellings of 2011 in cells that have buildings in 2022 but no municipal one: 5,076. They are sold, or the
  2022 grid hides one or two municipal buildings (no counts 1 and 2). [eigene Auswertung]
- A mix of counted 2011 dwellings and the change up to 2022 was tried and dropped. It gives only 56,371 municipal
  dwellings in Frankfurt.

# 5. What follows

- ABG and NH as separate numbers cannot be defended. Neither per district nor per Stadtteil.
- ABG and NH together per Stadtteil miss the tolerance only by a little. In four classes they are right in 9 of 10
  Stadtteile.
- The candidates work per district ("Lücke bei ABG und NH", "Genossenschafts-Lücke"). A change of the ownership
  layers reaches them.
