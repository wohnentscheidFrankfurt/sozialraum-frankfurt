---
title: "What the ranges of the ownership layers are made of"
---

As of 12 Oct 2026. Script: `analyses/uncertainty_scenarios.py`. Result: `analyses/results/uncertainty_scenarios.txt`
(build of 12 Oct 2026). Decision: `docs/decisions/2026-10-12-uncertainty-in-points.md`.

# 1. Result in short

- **One rule behind three formulas, with two additions for ABG and NH.** The counted part has no range. The estimated
  part gets the error the estimate had in 9 of 10 Stadtteile of the backtest on 2011. ABG and NH add the difference of
  two variants of the change where it is larger, and the secrecy gap 2011. [eigene Auswertung]
- **ABG and NH: most of the range is no estimate error of the backtest.** Half ranges added up: 4,148 dwellings.
  757 come from the backtest (16 % of the change), 392 from the difference of the two variants (larger in 10 of 45
  Stadtteile, among them Bonames with 227 of 255), 2,999 (72 %) from the unfilled secrecy gap 2011: public dwellings of
  table 4000W-1011 that the grid of 2011 does not locate. In 42 of 45 Stadtteile the gap is the larger part.
  [eigene Auswertung]
- **Half ranges in percentage points per Stadtteil:** ABG and NH ±0.6 (Bornheim) to ±8.8 (Bonames); Genossenschaften
  ±0 to ±2.1 (Riederwald); Private Unternehmen ±3.5, Privatpersonen und WEG ±5.4, Bund oder Land ±1.4, Organisationen
  ohne Erwerbszweck ±2.0 everywhere. [eigene Auswertung]
- **Counts agree, shares do not.** ABG and NH: map 69,219 dwellings, table 4000W-2002 69,558. As a share: map 18.27 %,
  table 17.27 %. The Genossenschaften: 13,196 against 12,932; 3.48 % against 3.21 %. The map divides by 378,958
  dwellings with an owner in the grid, the table by 402,827 dwellings (sum of the classes; the table prints 402,826). [belegt: `sources/05 Eigentümerstruktur/Zensus2022_4000W-2002_Frankfurt.csv`]
- **The table share of the Genossenschaften lies outside the range of Frankfurt** (difference 0.27 points, half range
  ±0.23). ABG and NH just inside (1.00 against ±1.09). [eigene Auswertung]

# 2. Open

- Whether the secrecy gap 2011 belongs into the range of ABG and NH, or only into their value. [offen]
- The denominator of the shares: the counts of ABG, NH and Genossenschaften reach the table total, the denominator
  stays at the grid. The four other groups get the rest, so they come out lower than the table. [offen]
