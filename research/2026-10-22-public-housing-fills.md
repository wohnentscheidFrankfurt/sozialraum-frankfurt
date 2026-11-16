---
title: "ABG and Nassauische Heimstätte: what the fills add"
---

As of 22 Oct 2026. Script: `research/scripts/public_housing_fills.py`. Result:
`research/results/public_housing_fills.txt` (build of 22 Oct 2026, branch `public-calc-two-fills`).

# 1. Question

The ⓘ of „ABG und Nassauische Heimstätte“ showed Riederwald: count 2011 × factor, plus 13 dwellings as
„Ergänzungen“ (0.5 points). Could the map drop the fills and use the count 2011 × factor of the Zensus alone, with
the research only for new areas the Zensus does not show?

# 2. Result in short

- **The fills are not small.** In Frankfurt they are 8,420 of 69,219 dwellings (12 %): 3,872 in cells with public
  stock in 2011 and no owner in 2022, 2,714 in new cells with municipal buildings in 2022, 1,708 from the research of
  ABG new buildings, 125 from the secrecy gap 2011. [eigene Auswertung]
- **Without them the map moves much.** Count 2011 × factor alone (variant A): 13 of 45 Stadtteile change the class.
  Kalbach-Riedberg loses 13.2 points (14.3 % to 1.1 %), Niederrad 9.5, Höchst 8.2. Niederrad falls from rank 5 to 16,
  Kalbach-Riedberg from 26 to 42. The half ranges are 1 to 2 points. [eigene Auswertung]
- **Without the research alone (variant B)** 6 Stadtteile change the class. Kalbach-Riedberg loses 5.2 points,
  Höchst 4.1, Unterliederbach 3.5, Niederrad 2.6. [eigene Auswertung]
- **The formula already uses the research only where the Zensus says too little:** in cells without public stock
  in 2011 or without owner in 2022, and only where the grid shows fewer dwellings. [eigene Auswertung]
- **Riederwald is the exception, not the rule.** It has the highest share and almost no fills. [eigene Auswertung]

# 3. New sites

Municipal dwellings 2022 in cells without public stock 2011: 2,714. 1,733 of them lie in cells without dwellings in
2011, so they are new buildings. 981 lie in cells with dwellings in 2011. In 704 of these the Zensus 2011 hid part
of the owners. The rest changed owner or was not counted as public. Niederrad: 301 of 320 in cells without dwellings
in 2011. [eigene Auswertung]

# 4. Decision

The formula stays. The ⓘ shows Niederrad and splits the fills into two rows: dwellings of 2011 whose owner the
Zensus 2022 does not name (744), and dwellings at new sites since 2011 (725). The first row now holds only the cells
the factor scales (3,336 × 0.91 = 3,035). Sum: 4,504 ÷ 15,389 = 29.3 %. See `pipeline/use_cases/public_housing/README.md`.

# 5. Limits

- The classes of the script are quintiles without the merging of equal labels in `APP.classify`. The count of class
  changes can differ by one or two.
- Variant B also drops research sites that fill a gap of the Zensus 2022. It is an upper bound for the weight of
  the research.
