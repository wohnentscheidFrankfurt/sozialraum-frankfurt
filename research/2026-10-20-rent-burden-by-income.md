# Rent burden by household income, from the survey microdata 2024 and 2025

As of 20 Oct 2026. Script: `scripts/rent_burden_income.py` (call in the header). All numbers below are its output.
Formula and limits as built: `pipeline/use_cases/survey/README.md`.

Labels: [belegt] = printed in the source; [eigene Auswertung] = counted by us; [unsicher]; [offen].

## Question

The report „Leben in Frankfurt“ prints one median of the rent burden (Mietbelastungsquote) per survey area. The
city publishes no breakdown by income. Can we count one from the public microdata, and does it reproduce the
published value?

## Data

- [belegt] `sources/frankfurt/statistics/leben-in-frankfurt_2025.csv` (8,185 cases) and `leben-in-frankfurt_2024.csv`
  (8,195 cases). Reports: `FU_5_Leben_in_Frankfurt_2025.pdf`, `FU_4_Leben_in_Frankfurt_2024.pdf`. Licence
  dl-de/by-2-0, Stadt Frankfurt am Main (codebooks). Provenance: `sources/README.md`.
- [belegt] Columns: `Umfragebezirk` (1–13), `weight`, `WOmieig_a` (1 = zur Miete), `WOkami_a` (rent, 12 classes of
  100 €), `WObtrko_a` (costs, 8 classes of 50 €), `XDhhnek_a` (equivalised net income, 6 classes of 1,000 €),
  `XDhhgrabs_a`, `XDhhgr017_a`, `XDhhform_a`. -42 = no answer.
- [belegt] The raw household income (24 classes) is not public. The city derived `XDhhnek_a` from it with the
  equivalence scale (1 for the first adult, 0.5 for every further adult, 0.3 for every child under 14).

## Formula

1. Tenants only, with rent, costs and income.
2. Warm rent = midpoint of the rent class + midpoint of the cost class. Open classes: rent under 400 € = 325 €, 1,400 €
   and more = 1,700 €; costs under 100 € = 75 €, 400 € and more = 450 €.
3. Household income = midpoint of the equivalised class × equivalence scale. Under 1,000 € = 750 €, 5,000 € and more =
   6,000 €. Children come from `XDhhgr017_a` (age 0–17, so 14–17 count 0.3 instead of 0.5). A household of one or two
   without household form counts as adults only.
4. Burden = 100 × warm rent ÷ household income. Groups: under 2,000 €, 2,000 to under 3,200 €, 3,200 € and more.
5. Value = weighted median. For the map: both years pooled, rounded half up to 5 points.

## Validation

- [eigene Auswertung] Median burden of all tenants: 2025 29.4 % (report FU 5: „mindestens 29 Prozent“), 2024 29.3 %
  (FU 4: 29 %). Both within 1 point of the printed 29.
- [belegt] Warm rent 2025 in the report: median 1,030 €, quartiles 792 € and 1,400 €. Own, from class midpoints:
  1,075 €, 825 € and 1,475 €. The midpoints overstate by 33 to 75 €.
- [eigene Auswertung] All 13 survey areas 2025, own median against the printed class (Abb. 4.5, p. 27 of FU 5; the
  classes are `FIGURES` in `pipeline/use_cases/survey/sources.py`). The comparison uses the shown value, the median
  rounded to whole percent. Twelve areas lie inside their class or at most 1 point outside it (unrounded at most
  1.1): Süd 30 against 29, West 30 against 31–33, Mitte-West 31 against 30. Ost has 32.2, shown 32, against class
  30. The largest gap is Ost: 2 points rounded, 2.2 unrounded. This is the limit of the rule „at most 2 points
  outside“, and the unrounded value is above it.
- [eigene Auswertung] Weights: they sum to the cases in both files. The weight share of each survey area differs
  by at most 0.09 points between 2024 and 2025. This is the evidence that the 2024 CSV uses the codes of 2025
  (see Traps).

## Results

Equivalised-income view, tenants 2025 (background; the map does not use it):

| Equivalised income | Cases | Share of tenants | Median burden | Share above 40 % |
|---|---|---|---|---|
| under 1,000 € | 246 | 6.9 % | 68.9 | 93.5 % |
| 1,000 to 2,000 € | 1,064 | 29.0 % | 41.1 | 51.4 % |
| 2,000 to 3,000 € | 1,132 | 27.2 % | 28.7 | 13.7 % |
| 3,000 € and more | 1,716 | 36.9 % | 22.4 | 2.4 % |

Groups by household net income, city, median burden (cases, share above 40 %):

| Year | Under 2,000 € | 2,000 to 3,200 € | 3,200 € and more | Households in the groups |
|---|---|---|---|---|
| 2025 | 55 % (631, 81 %) | 37 % (851, 37 %) | 24 % (2,676, 6 %) | 17.3 / 22.5 / 60.2 % |
| 2024 | 52 % (562, 78 %) | 35 % (911, 31 %) | 24 % (2,559, 6 %) | 16.1 / 24.6 / 59.2 % |
| Pooled | 53.3 (1,193) | 36.1 (1,762) | 23.9 (5,235) | |

Pooled, per survey area, median rounded to 5 points (unrounded; cases):

| Survey area | Under 2,000 € | 2,000 to 3,200 € | 3,200 € and more |
|---|---|---|---|
| Innenstadt I | 50 (52.4; 105) | 35 (37.0; 144) | 25 (24.2; 542) |
| Innenstadt II | 50 (48.3; 63) | 40 (38.9; 117) | 25 (23.6; 549) |
| Innenstadt III | 50 (51.7; 82) | 35 (37.0; 123) | 25 (23.3; 600) |
| Bornheim/Ostend | 50 (48.6; 121) | 35 (35.0; 189) | 25 (23.1; 549) |
| Süd | 55 (55.6; 85) | 35 (37.0; 138) | 25 (24.3; 502) |
| West | 55 (56.9; 105) | 35 (34.4; 164) | 25 (24.3; 308) |
| Mitte-West | 55 (55.0; 91) | 35 (34.1; 143) | 25 (24.0; 342) |
| Nord-West | 50 (51.7; 113) | 35 (37.0; 148) | 25 (25.5; 304) |
| Mitte-Nord | 55 (53.7; 79) | 35 (36.7; 147) | 25 (22.5; 421) |
| Nord-Ost | 55 (55.0; 108) | 35 (34.2; 164) | 25 (25.2; 263) |
| Ost | 55 (53.3; 117) | 35 (36.7; 141) | 25 (24.3; 296) |
| Kalbach/Riedberg | 60 (58.3; 51) | 45 (43.0; 57) | 30 (28.1; 310) |
| Nord | 50 (51.7; 73) | 40 (38.6; 87) | 25 (26.0; 249) |

- The smallest group has 51 cases (Kalbach/Riedberg, under 2,000 €). The rule „under 30 cases: no value“ never
  applies to the pooled data. In 2025 alone it would: Kalbach/Riedberg has 25 and 26 cases in two groups.
- Result in one line: the low group pays about 55 %, the middle group about 35 %, the high group about 25 %. Frankfurt
  as a whole 29 %.

## Uncertainty

Bootstrap, 400 draws, seed 1, 90 % interval of the weighted median.

Pooled, half width of the interval per survey area (smallest, mean, largest):

| Group | Smallest | Mean | Largest |
|---|---|---|---|
| Under 2,000 € | 2.5 | 5.1 | 13.3 (Kalbach/Riedberg) |
| 2,000 to 3,200 € | 1.3 | 2.2 | 3.9 |
| 3,200 € and more | 0.5 | 0.8 | 1.3 |

- Pooled interval examples, under 2,000 €: Innenstadt II 48 [45–55], Süd 56 [52–62], Kalbach/Riedberg 58 [48–75].
- 2025 alone (script section 5): mean half width 7.1 (under 2,000 €), 3.6 (middle), 1.1 (high). Pooling lowers the
  mean half width of the low group to 5.1. The „about ±5“ of the spec is the mean of the low group; Kalbach/Riedberg
  is the exception.
- The build (`pipeline/use_cases/survey/model.py`) reports typical 5.0 (median over the areas, not the mean), largest
  13.33 and largest of the other groups 3.65. The script gives 5.1, 13.3 and 3.9. The values differ slightly because
  the build draws its 400 resamples per cell in another order, so the random draws are not the same. The stated ±5,
  ±13 and ±4 hold for both.
- 2025 against 2024, area medians correlate at 0.25 (low), 0.41 (middle), 0.72 (high). In the low group the order of the
  areas is mostly noise. This is why the map rounds to 5 points and shows no ranking.
- Share above 40 %: the half width is 9.7 (low) and 11.0 points (middle) in 2025 alone, the 2024 values differ by up to
  25 points in single areas. The share is not fit for the map.

## Sensitivity

Pooled city median when the open classes change (rent 1,400 € and more / income 5,000 € and more):

| Assumption | Under 2,000 € | 2,000 to 3,200 € | 3,200 € and more | All tenants |
|---|---|---|---|---|
| 1,550 / 5,500 € | 53.3 | 36.1 | 24.1 | 29.2 |
| 1,700 / 6,000 € (central) | 53.3 | 36.1 | 23.9 | 29.4 |
| 1,900 / 7,000 € | 53.3 | 36.1 | 23.9 | 30.0 |

The group values move by at most 0.2 points, the median of all tenants by at most 0.6. The upper two open classes do
not matter for the groups. The lowest class does.

Lowest equivalised class (under 1,000 €, central 750 €), group under 2,000 €, pooled (script section 6b):

| Value for the class | City median (unrounded) | Rounded to 5 | 13 area values, rounded | All tenants 2025 |
|---|---|---|---|---|
| 600 € | 55.0 | 55 | 50–65 | 29.4 |
| 650 € | 55.0 | 55 | 50–60 | 29.4 |
| 700 € | 55.0 | 55 | 50–60 | 29.4 |
| 750 € (central) | 53.3 | 55 | 50–60 | 29.4 |
| 800 € | 51.7 | 50 | 50–60 | 29.4 |
| 850 € | 51.7 | 50 | 45–55 | 29.4 |

- The check against the report (median of all tenants, 29.4 at every value) does not test this assumption. The
  median of all tenants never reaches the lowest class.
- Plausible range 600 to 800 €. For a single, the classes of question 65 inside this class reach at most 800 €.
  The city value moves from about 55 % to about 50 %. The area values move by one step of 5 points, within the stated uncertainty.
- About 63 % of the tenant households in 2025 (58 % in 2024) lie in one group for certain, whatever the true income in
  the class. The other third can sit in the neighbouring group. [unsicher] The group medians blur at the limits.

## Worked example

Singles (1 person) with an equivalised income of 1,000 to 2,000 €, both years, weighted medians of class midpoints.
676 cases, 56.3 % of the group under 2,000 €.

| Row | Value |
|---|---|
| Rent class (median) | 3, that is 500 to 600 € |
| Cost class (median) | 3, that is 150 to 200 € |
| Rent | 550 € |
| Costs | 175 € |
| Warm rent | 725 € |
| Income (class 1,000 to 2,000 €, one adult, scale 1) | 1,500 € |
| Burden | 48.3 % |

The median of the single ratios is also 48.3 %. The example is one household, not the map value of the group.

## Traps

- No raw income. The household income is rebuilt from a class midpoint times the scale. The groups are not exact
  (see Sensitivity, 63 % certain).
- Bürgergeld. The questionnaire names Wohngeld and Arbeitslosengeld as income. It does not name the housing costs the
  Jobcenter pays. The lowest group may read too high. [offen]
- Persons, not households. The weights count adults, not households.
- Classes are discrete. Medians of midpoints sit on few values. Rounding to 5 points hides this.
- Codebook 2024. The PDF prints wrong codes for `WOkami_a`, `WOflae_a` and `Umfragebezirk`. The CSV uses the codes of
  2025. Check against the weight shares of the survey areas before reading a new year.
- The report prints the burden as a median of all tenants. Our groups reproduce it (29.4, 29.3). The group values are
  our count and do not carry the authority of the report. The map shows them only in the tooltip.
- The own area medians and the printed classes differ by up to 2 points (Ost, shown value; 2.2 unrounded).
  Classes are rounded ranges, not points.

## Addendum, 20 Oct 2026: West and Mitte-West

Question of the user: the printed class of the overall burden differs between West and Mitte-West, our three groups do
not. Script: `scripts/rent_burden_west_mitte_west.py` (uses the functions of the map). All numbers are its output.

- The report prints West 31 % and Mitte-West 30 %. A class limit of figure 4.5 lies between 30 and 31. [belegt]
- Our overall median of tenants [eigene Auswertung]:

| | 2025 | 2024 | pooled |
|---|---|---|---|
| West | 30.0 | 30.0 | 30.0 |
| Mitte-West | 31.1 | 29.4 | 30.0 |

- In 2025 our order is reversed. The 90 % interval of the 2025 difference West − Mitte-West is −3.3 to +2.1 points
  (bootstrap, 1,000 draws, seed 1). A gap of 1 point cannot be told from zero.
- Within the groups West is 0.3 to 1.9 points higher (pooled, unrounded): 56.9 / 34.4 / 24.3 against 55.0 / 34.1 /
  24.0. Rounding to 5 points shows ~55 / ~35 / ~25 for both.
- Income mix (pooled, share of tenants): West 20 / 31 / 50 %, Mitte-West 19 / 26 / 55 %. West has more tenants in the
  middle group and fewer in the top group.
- Counterfactual: Mitte-West with the income mix of West has an overall median of 31.1 instead of 30.0.
- Reading: the overall value of an area follows mainly how many lower-income households live there. The same income
  group carries almost the same burden in West and Mitte-West.
