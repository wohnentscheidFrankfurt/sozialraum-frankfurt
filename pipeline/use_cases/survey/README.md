# survey: „Umfrage 2025“

## Shows
`LIF_RENT_BURDEN_RATIO` (Mietbelastungsquote) and `LIF_ATTACHMENT` (Würden ihr Wohnviertel vermissen).
Districts only. The tooltip names the survey area („… im Umfragebezirk Innenstadt“).
The tooltip of the rent burden also lists the rent burden of three income groups of the survey area:
`LIF_RENT_BURDEN_INCOME_LOW`, `LIF_RENT_BURDEN_INCOME_MID`, `LIF_RENT_BURDEN_INCOME_HIGH` (no layer, estimates).
The ⓘ of the rent burden adds a written sum for one household.
All five entries carry `survey_area`. In the profile the rent burden stands in „Miete“, the attachment in „Soziale
Lage“, each after the note on the Umfragebezirk (`docs/texts.md`, Map: profile).

## Formula
Printed classes:
1. The report „Leben in Frankfurt 2025“ prints a class per survey area (figures 4.5 and 4.11). The classes are
   copied by hand into `FIGURES`.
2. Every district lies in one survey area and shows its class (`research/2026-10-09-survey-social-aspects.md`).
3. Frankfurt: the value printed in the text of the report.

Breakdown by household income (own count from the microdata of 2024 and 2025, both years pooled):
1. Tenants only (`WOmieig_a` = 1) with rent, costs, income and household size.
2. Warm rent = midpoint of the rent class (`WOkami_a`) + midpoint of the cost class (`WObtrko_a`).
   Open classes: rent under 400 € = 325 €, 1,400 € and more = 1,700 €; costs under 100 € = 75 €,
   400 € and more = 450 €.
3. Household income = midpoint of the class of the equivalised income (`XDhhnek_a`) × equivalence scale. Open classes:
   under 1,000 € = 750 €, 5,000 € and more = 6,000 €. The scale is 1 for the first adult, 0.5 for every further
   adult and 0.3 for every child under 18 (`XDhhgr017_a`). Singles and couples have no children. A household of 1 or 2
   without household form counts as adults only.
   `burden_ratios` takes two parameters for other use cases. `income_position` places the income of a closed class at
   low + position × (high − low); the default 0.5 is the midpoint, and rent and costs always keep their midpoint.
   `open_low_income` replaces the 750 € of the open lowest class; the default keeps 750 €.
4. Ratio = 100 × warm rent ÷ household income. Groups by household income: under 2,000 €, 2,000 to under 3,200 €,
   3,200 € and more.
5. Value per survey area and group: weighted median (`weighted_median`) over both years, rounded half up to 5
   points. Under 30 cases (unweighted, both years): no value.
6. City value per group: the same over all survey areas.
7. Half width of the 90 % interval of the weighted median per area and group: bootstrap, 400 draws, fixed seed.
   `survey_half_widths` holds three numbers in points: `typical` (median over the areas for the lowest group),
   `max_low` (its largest) and `max_upper` (largest of the two upper groups).
8. Worked example (`survey_calc_examples`, `survey_calc_example` in `catalog.py`): tenants living alone with an
   equivalised income of 1,000 to 2,000 €. Rent and costs are the weighted medians of their class midpoints. Income
   is 1,500 €. The last row is the ratio of this one household, whole percent, without „~“.

## Why
The map shows what the city prints per survey area, at the resolution of its figures. The colour of the layer stays
the printed class.
The city publishes no breakdown by income. A special evaluation by the city takes too long. So the map computes it
from the public microdata of the city. It stands only in the tooltip of the published value and never colours the map.
The own count reproduces the published value (see Checks). Evidence and numbers:
`research/2026-10-20-rent-burden-by-income.md`.
Both limits of the groups are limits of the classes of the questionnaire (question 65).
Both years are pooled: twice the cases. The 90 % interval per area and group shrinks to about ±5 points.
Survey areas only. The microdata hold no Stadtteil, so a Stadtteil value would repeat its survey area.

## Inputs
No dataset. The Stadtbezirke in `sources/frankfurt/geodata/`; the monitoring table
`sources/frankfurt/offices/Monitoring2024_Stadtbezirke_nach_Umfragebezirk.csv` names the survey area of each district;
`FIGURES` in `sources.py`. The reports `sources/frankfurt/statistics/FU_5_Leben_in_Frankfurt_2025.pdf` and
`sources/frankfurt/statistics/FU_4_Leben_in_Frankfurt_2024.pdf` (printed city value). The microdata
`sources/frankfurt/statistics/leben-in-frankfurt_2025.csv` and
`sources/frankfurt/statistics/leben-in-frankfurt_2024.csv` (`SURVEY_MICRODATA`).
The codebook 2024 prints wrong codes for `WOkami_a`, `WOflae_a` and `Umfragebezirk`. The CSV uses the codes of 2025.
Evidence: the weight share of each survey area differs by at most 0.1 points between the years.
`sources.py` holds the class bounds of the codebook. A code outside them stops the build (`ValueError`).

## Output
`survey_by_district` (class per district: upper end `<ID>`, lower end `<ID>_LOWER`; the three breakdown values per
district), `survey_city` (printed city value and the three breakdown values), `survey_half_widths`,
`survey_calc_examples`, `survey_checks`. `survey_respondents` (working data): one row per respondent of both years as
`read_microdata` returns it, for use cases that recompute the burden.

## Checks
- The lowest and the highest class of each figure against the minimum and maximum printed in the report
  (`check_printed_extremes`). A typing error in `FIGURES` stops the build.
- The texts of both reports contain „mindestens 29 Prozent“ (`FAIL`).
- Own median of all tenants against the printed value: city 2025 and 2024 at most 1 point off, each survey area of
  2025 at most 2 points outside its printed class (`WARN`).
- The weight share of each survey area differs by at most 0.5 points between the years (`FAIL`).

## Limits
- Sampling error ± 4 to 4.5 points per survey area for shares of respondents (`LIF_ATTACHMENT`). It is an own value.
  Tab. 9.5 of the report prints ± 3.8 to ± 4.1 points at 50 %. With the design effect of the weights (1.13 to 1.29)
  the own count gives ± 4.1 to ± 4.5 (`research/2026-10-09-survey-social-aspects.md`). The report prints no margin
  for the rent burden. Its ⓘ says so.
- The report states the median of the rent burden only for the whole city (PDF p. 31, printed p. 27: „Die Hälfte der
  Menschen in Frankfurt gibt mindestens 29 Prozent des Einkommens allein für die Wohnkosten aus“). Figure 4.5 does
  not name the statistic of the classes per survey area. The ⓘ names the median for Frankfurt only and says that the
  classes show how the ratio differs per survey area.
- Not per Stadtteil: Bockenheim and Praunheim are split between survey areas.
- The raw household income (24 classes) is not public. The city derived `XDhhnek_a` from the class midpoint divided by
  the equivalence scale. The map multiplies it back. About a third of the tenants cannot be placed in a group with
  certainty from the classes.
- The lowest equivalised class („unter 1.000 €“) has no midpoint. The build takes 750 €. From 600 to 750 € the city
  median of the lowest group is about 55 %, from 800 € about 50 %. The area values move by one step of 5 points,
  within the stated uncertainty. The check against the published median of all tenants does not test this value.
- Minors count 0.3 instead of 0.5 for every child under 18, because the microdata only give minors from 0 to 17. The
  equivalence scale wants children under 14 at 0.3.
- Bürgergeld: the questionnaire names Wohngeld and Arbeitslosengeld as income, not the housing costs paid by the
  Jobcenter. The lowest group may read too high.
- The weights count persons (adults), not households.
- Medians of class midpoints are discrete. Rounding to 5 points hides this.
- The own breakdown has no layer, no colour, no profile row and no candidate criterion.
