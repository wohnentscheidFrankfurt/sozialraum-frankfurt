# Review of the block of rents in the view „Neubau“

1 Nov 2026. Question: do the sources and their uncertainties carry the statements of the block „Seit 2017 wuchs die
Zahl der Wohnungen schneller als die Bevölkerung, die Mieten neuer Verträge noch schneller“? The review covers the
heading, the lead and the ⓘ (`RENTS_TEXTS` in `pipeline/use_cases/new_construction/catalog.py`).

Answer: every number of the block matches its source. The heading holds in Euro under every calculation of this
review. Its comparison without inflation does not hold safely, although README, `docs/data-rules.md` and the check
„rents heading“ claim it. The lead „Die Haushalte blieben im Schnitt gleich groß“ holds for the base year 2017 only.
The lead „Die Mieten älterer Verträge stiegen weniger als Preise und Löhne“ holds safely.

## Sources

- Stock: `sources/regionalstatistik/Regionalstatistik_31231-02-01-4_Frankfurt.csv`,
  `sources/hessen/statistics/fi1_j25.pdf`, `sources/hessen/statistics/FI1_j22_a.pdf`.
- Population: `sources/regionalstatistik/Regionalstatistik_12411-01-01-4_Frankfurt.csv`,
  `sources/hessen/statistics/AI2_AII_AIII_AV_22-2hj_a.pdf`, `sources/hessen/statistics/AI2_AII_AIII_AV_25-2hj_a.pdf`.
- Melderegister: `sources/frankfurt/statistics/Demographische Kennzahlen (Stadtbezirke).xlsx` (Einwohner/-innen, sum
  of the Stadtbezirke), `sources/frankfurt/statistics/bevoelkerung_in_haushalten_stadtbezirke_.csv`,
  `sources/frankfurt/statistics/haushalte_nach_groesse.csv`.
- Mietspiegel: Gutachten 2018 and 2022, Gutachten 2024, Dokumentation 2026 in `sources/frankfurt/offices/`.
- Prices and wages: `sources/hessen/statistics/mi2_j25.pdf`,
  `sources/hessen/statistics/pm_verdienste_q3_2025_statistikhessen.xlsx`.
- Script: `research/scripts/rents_block_review.py`, result `research/results/rents_block_review.txt`.

## Values checked

- Stock on 31.12.: 389,524 (2017) and 404,227 (2022) in the Regionaldatenbank. 415,359 (2025) in table 4 of F I 1 j/25,
  PDF page 12. 408,605 (2022 on the old base) in table 4 of F I 1 j/22, PDF page 12. [belegt]
- Both stock reports count Wohnheime since 2010 (F I 1 j/25, table 1, footnote 1, PDF page 7). The only break is the
  base. [belegt]
- Population on 31.12.: 746,878 (2017) and 747,389 (2022) in the Regionaldatenbank. 773,068 (2022 on the old base) in
  A I 2 of 2022, PDF page 33. 760,656 (2025) in A I 2 of 2025, PDF pages 28 and 35. [belegt]
- Rents of 2017: new 10.21, older 8.69, all 9.36. They stand in figure 1 of the Gutachten 2018 (PDF page 23), in
  figure 21 of the Gutachten 2022 (PDF page 90) and in figure 17 of the Dokumentation 2026 (PDF page 103). Figure 17
  draws all surveys from 2013 to 2025 as one series. Figures 1 and 17 are images, checked by eye. The build reads
  figure 21 only. [belegt]
- All four reports come from ifak and IWU (2024: IWU alone). [belegt]
- VPI Hessen June 2017: 97.2 (M I 2 j/25, table 3, PDF page 20). Nominallohnindex Hessen: 93.6 and 84.0 (2nd and 3rd
  quarter 2017), 120.1 and 110.9 (2025). [belegt]
- `interim/new_construction_rents.csv` holds the same values. [belegt]

## Uncertainties

### Stock

- The Zensus 2022 lowered the stock of 31.12.2022 by 4,378 (1.1 %). [belegt]
- From the Zensus 2011 to 31.12.2022 the old Fortschreibung gathered a mean overcount of 376 dwellings per year. Three
  such years after 2022 make 1,128, or 0.27 % of 2025. The outflow of 2025 adds to it (HBO § 63a). [eigene Auswertung,
  unsicher]

### Population

- The Zensus 2022 lowered the population of 31.12.2022 by 25,679 (3.4 % of 2017). [belegt]
- When this overcount arose is unknown. Three calculations bracket it [eigene Auswertung]:
  - published, all of it after 2017: +1.84 %;
  - chained, the same share of it already in 2017: +5.34 %;
  - linear, built up evenly from 9.5.2011 to 31.12.2022: +3.88 %.
- The Melderegister grew from 741,093 to 781,337 (+5.43 %). It has no break. It carries the same moves as the
  Fortschreibung: the Fortschreibung lies 5,785 above it in 2017 and 5,459 in 2022 on the old base. So it confirms the
  moves, not the time of the overcount. [eigene Auswertung]

### Rents of the Mietspiegel

- The means are not hedonically adjusted. Gutachten 2018, PDF page 23: „keine hedonische Bereinigung … der auf Neubau
  und Modernisierung entfallende Anteil der Preissteigerung nicht herausgerechnet“. New flats raise the mean of the new
  contracts. Direction: the growth is too high. Size unknown. [belegt, unsicher]
- Six instead of four years from 2021 lower the means. Direction: the growth is too low. Size unknown. [belegt]
- Parking: the Gutachten 2022 (PDF page 89) gives 10.29 before and 10.21 after the deduction of parking surcharges;
  figure 21 draws 10.29. The Dokumentation 2026 (PDF page 102) gives 12.28 after and 12.33 before the deduction.
  Its figure 17 says „um Stellplatzzuschläge bereinigt“, but draws 10.29 for 2021. So the groups of 2021 probably
  include parking and those of 2025 do not. The report of 2018 does not say it. Size 0.5 to 0.8 %. [belegt, unsicher]
- Sampling error: the reports print none for the means. Rough own estimate [eigene Auswertung, unsicher]:
  - new contracts: about 1,540 cases in 2017 (43.5 % of 3,537) and 1,965 in 2025 (unweighted, table 62 of the
    Dokumentation 2026);
  - spread from the deciles (2021: P10 6.99, P90 14.31 €/m²; 2025: P10 7.89, P90 17.53 €/m²), design effect 1.5
    assumed;
  - standard error of a mean about 0.8 to 0.9 %, of the growth about 1.1 %;
  - 95 %: new contracts 136.6 ± 3 in Euro and 109.3 ± 2.4 without inflation, older contracts 116.3 ± 2.7 and
    93.1 ± 2.2.
- 2023 is an adjustment sample. It shapes the drawn line, not the heading. [belegt]

### Persons per household

- The Melderegister file is irregular around 2017. Single households rise by 10,410 in 2015 and fall by 5,796 in 2018
  and by 3,315 in 2019. Persons in households lie 3.70 % above the Einwohner/-innen in 2017 and 0.89 % in 2019, so the
  file counts other persons from 2019. [belegt, eigene Auswertung]
- Persons per household: 1.8238 (2016), 1.8447 (2017), 1.8720 (2018), 1.8741 (2019), 1.8446 (2025). Change to 2025:
  +1.14 % from 2016, −0.01 % from 2017, −1.47 % from 2018, −1.58 % from 2019. [eigene Auswertung]

## Statements against the uncertainties

| Statement | Numbers | Verdict |
|---|---|---|
| Dwellings faster than population since 2017 | lowest dwellings 6.63 % against highest population 5.43 % (Melderegister): +1.20 points, about +0.9 with the drift | holds safely |
| Rents of new contracts even faster, in Euro | 36.6 ± 3 against at most 7.8 | holds safely |
| The same without inflation | 9.3 ± 2.4 against 7.8 (chained) and 6.6 (published) | not safe |
| Households stayed the same size | −0.01 % from 2017, up to −1.58 % from other base years | holds for 2017 only |
| Older contracts rose less than prices and wages | 116.3 ± 2.7 against 125.0 and 130.1; 93.1 ± 2.2 against 100 | holds safely |

[eigene Auswertung]

- The first statement turns only if the old Fortschreibung overcounted by 33,534 persons on 31.12.2017, against 25,679
  on 31.12.2022.
- It also holds from 31.12.2016 (+0.91 points) and from 2015 (+1.31). From 2013 it is not safe (−1.05): the
  Melderegister grew by 12.69 %, the dwellings by 11.64 % as published. 2013 is a survey year of the Mietspiegel too.
- The lines show the largest gap: 4.8 points as published. Chained it is 2.45 points, linear 3.44, at the lowest 1.2.
- Composition effects of several points do not reach the margin in Euro. Without inflation the sampling error alone
  reaches it.
- The ⓘ states every number correctly. It does not say that the means are not hedonically adjusted. It names no
  sampling error of the Mietspiegel.

## What the block does not show

- The heading names no cause. The ⓘ ends with „Die Zahlen zeigen nicht, wie hoch die Mieten ohne die neuen Wohnungen
  wären.“ [belegt]
- A reader may still conclude that more dwellings did not help. The numbers do not carry this:
  - In a tight city the dwellings bound the population. The population is no measure of the demand. [unsicher]
  - From 2011 to 2017 the population grew by 10.40 % and the dwellings by 6.27 %. Dwellings per 1,000 residents:
    541.8 (2011), 521.5 (2017), 533.6 (2025, chained on the old base). The level of 2011 is not reached again.
    [eigene Auswertung]
  - New flats enter the mean of the new contracts, because the means are not hedonically adjusted. [belegt]
- The lead on households answers one objection, but with a number that holds for the base year 2017 only.

## Limits

- The sampling errors are a rough own estimate. The design effect is assumed.
- The time of the overcount of the old Fortschreibung is unknown. The three calculations are cases, not a range with a
  probability.
- The size of the hedonic effect and of the effect of six instead of four years is unknown.

## Corrections after the review of the branch

1 Nov 2026, later. A fresh review of the branch `rents-review` checked this note. The text above stays as written; these
points correct it.

- Parking: both pairs are means of all contracts, not of a group. The effect is 0.4 % in 2025 (12.33 ÷ 12.28) and
  0.8 % in 2021 (10.29 ÷ 10.21), not 0.5 to 0.8 %. That the group means of 2021 include parking is probable, not
  certain. [belegt, eigene Auswertung]
- Sampling error: `research/scripts/rents_block_review.py` now computes the estimate. It gives each group the relative
  spread of all contracts (deciles of 2021 and 2025; 2017 takes the spread of 2021, because the report of 2018 prints no
  deciles). The cases of 2017 are a weighted count (43.5 % and 56.5 % of 3,537), those of 2025 an unweighted one (table
  62). The design effect of 1.5 is assumed. 95 %: new contracts 136.6 ± 3.2 in Euro and 109.3 ± 2.6 without inflation,
  older contracts 116.3 ± 2.8 and 93.1 ± 2.2. The first estimate above (± 3, ± 2.4, ± 2.7, ± 2.2) took other spreads per
  group. [eigene Auswertung, unsicher]
- Without inflation: the gap to the chained growth of the dwellings (9.30 − 7.79 = 1.51 points) lies within the sampling
  error. The gap to the published growth (9.30 − 6.63 = 2.67 points) lies just outside it. The verdict „not safe“
  stands. [eigene Auswertung]
- From 2013: the Melderegister (12.69 %) lies above the published growth of the dwellings (11.64 %) and below the
  chained one (12.85 %). [eigene Auswertung]
- The check „rents heading“ now demands that the rents of new contracts outgrow the dwellings in Euro by more than
  4 points (`RENT_MARGIN`), above the sampling error in Euro.
