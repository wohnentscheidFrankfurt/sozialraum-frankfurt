# Data rules

Cross-cutting rules for the numbers of the map. Formulas and the choices of one use case stand in its README in
`pipeline/use_cases/`. Terms follow `docs/glossary.md`.

## Sources

### Precedence

- A number the city publishes for an area of the map is the value of the map.
  Why: the city answers for it in public, so the map cannot be attacked on it.
- An own count only checks a published number. It never stands beside it on the map, except as the breakdowns below.
- City values of the Monitoring, the survey and the election are published values (kind `published`).
- Printed classes stay as printed. A class „64–70“ reads „über 63 bis 70“. The last class ends at the rounded maximum.
- Where the city publishes no breakdown, an own breakdown from the microdata of the city may stand in the tooltip of
  the published value. It must reproduce the published value and never colours the map.
  Example: the rent burden by household income, from the microdata of „Leben in Frankfurt“.
  Why: the city publishes no such breakdown, and a special evaluation by the city takes too long. The own count
  reproduces the published value.
- Such a breakdown may also stand as a chart of its own. It must reproduce the published value, and the ⓘ names the
  last published breakdown. Example: the tenants by income group in the view Miete, with the Mikrozensus 2018 of the
  Wohnungsmarktbericht 2019/2020 in the ⓘ.
- Where the map aggregates the Zensus grid itself, its city value is computed like the areas. A Zensus table for
  Frankfurt checks it.
- Among answers of the Magistrat on the same number, the latest answer counts.
- A number the Magistrat may still revise is marked „vorläufig“.

### Allowed sources

- Sources are official statistics, reports and answers of the Magistrat, and publications of the owners themselves.
- No number rests on a party document (motion, faction release).
  Why: the map stays independent of parties, and party numbers are open to attack.
- A party document may point to a primary source. Only the primary source is cited.
- Every source lies in `sources/`, once, with its provenance in `sources/README.md`.
- Every number is checked against its source before it goes on the map.
- Texts use the terms of the source, so that a reader finds the number there.
- The map may draw an own conclusion or estimate. It must be well founded, traceable and as simple as possible.
  Why: a complex conclusion raises questions and gives an attack surface.
- Each assumption of such a conclusion stands in the ⓘ with a one-sentence reason. The arithmetic is a written sum.
  The ⓘ names what the estimate does not know.
- Prefer round assumptions that explain themselves („die Hälfte“, 25 m² for one module).
- Without a source the map still states no cause of a trend.
  Examples: the survey shows the printed classes per survey area; the view Neubau states the numbers of its sources;
  the module estimate of `ROOF_FLAT` follows two stated assumptions; the suitability line of a building gap names a
  real example (see Hand verdicts).

### As-of dates

- Every value names its reference date in the ⓘ (Stand).
- Numerator and denominator come from the same date and the same list where a source allows it.
- Where they cannot, the README of the use case names the mismatch and how the formula handles it.

## Estimates and uncertainty

### Counted or estimated

- A value is counted when a source counts it for the area. Every other value is an estimate.
- Estimates on the map: the six ownership shares, both vacancy rates, both construction-year classes and their counts,
  and the three rent burdens by income group (`LIF_RENT_BURDEN_INCOME_LOW`, `_MID`, `_HIGH`).
  The module count of `ROOF_FLAT` is a model value, see the next bullet.
  `test_estimates_are_the_ownership_construction_year_vacancy_and_income_indicators` pins the list.
- The module estimate in the ⓘ of `ROOF_FLAT` is a model value („~14.700 leichte Wohnmodule haben Platz“, rounded to
  hundreds) and stands in the ⓘ only.
  `ROOF_FLAT` itself is counted from the 3D building model (m² of low flat roofs).
- An estimate starts with „~“. Tooltip and profile show no range at the value.
  Why: the order of magnitude holds; the reader finds the Unsicherheit in the ⓘ.
- A Rechenbeispiel is a model person computed from published inputs, not a measured household. Every model value starts
  with „~“. Quelle and Stand of the ⓘ name the sources of the inputs, not every input (not the Mindestlohn, not the
  contribution rates); the written sums show the inputs of their example. The source line starts with „Rechenbeispiel.“
  Example: the wage example of the view Miete.
- Every model value of the view Miete starts with „~“: the wage example is a Rechenbeispiel, the bars are an own count
  of the survey. Published values, fixed bounds and ranges in its ⓘ carry none (29 %, „gut 11 %“, „1 bis 4 Punkte“).
- Ownership and construction year count dwellings, not buildings.
  Why: a block of 80 dwellings would else count like a single-family house.

### Uncertainty

- The Unsicherheit of the ⓘ says how far an estimate or a survey can be off.
- The uncertainty of a share is in percentage points, never in relative percent.
  Why: relative ranges of small groups read ±42 % and more, and points add to the value on screen.
- The half range is the error the estimate had in 9 of 10 areas of the backtest on 2011.
- Exception: the half range of ABG und NH is 16 % of the estimated change plus the 2011 secrecy gap
  (`pipeline/use_cases/public_housing/README.md`, Formula).
- A counted part of a value has no range.
- Texts name the hits of the backtest („40 von 45“), not „90 %“.
- A range is a budget from the backtest, not a measurement of 2022. The README names its parts.
- The data keep the range (`_LOW`, `_HIGH`). The candidates use its upper end.
- A survey share names its sampling error where that is sensibly possible. Where the report prints no margin, the ⓘ
  says so. This holds for shares. The means of the Mietspiegel name no sampling error in the ⓘ: the reports print
  none, and the own estimate rests on assumptions (README of `new_construction`, Limits; decision of the user,
  1.11.2026).
- A heading compares a survey value with another series only where the gap is larger than the sampling error. A check
  tests what the text says, not more. Why: within the sampling error the order can turn by chance. Example: without
  inflation the rents of new contracts in the view Neubau grew by 9.3 %, the dwellings by 6.6 % (published) or 7.8 %
  (chained). The gap to 7.8 % lies within the sampling error of the Mietspiegel, about ±2.6 points (own estimate,
  `research/2026-11-01-rents-block-review.md`). So heading and check „rents heading“ compare in Euro (+36.6 %), with a
  margin of 4 points (`RENT_MARGIN`), above the sampling error in Euro (about ±3.2 points).
- A comparison across a Zensus break names both calculations in the ⓘ and rounds the statement so that both hold.
  Why: the new base moves the value by itself, and neither calculation is the true change.
  Example: in the view Neubau the dwellings grew from 2017 to 2025 by 7.79 % chained over the stock of 31.12.2022 on
  the old base (report F I 1 j/22) and by 6.63 % as published. The population grew by 5.34 % chained (report A I 2,
  2nd half of 2022) and by 1.84 % as published. The heading of the block of rents, that the dwellings grew faster than
  the population, holds for both calculations. The ⓘ names both calculations (7.8 % and 5.3 % chained, 6.6 % and 1.8 %
  as published) and both base effects („25.679“, „4.378“). The check „rents uncertainty“ guards the four numbers. The
  check „rents heading“ compares the rents of new contracts in Euro with the dwellings in both calculations too.
- A chain across a Zensus break uses the official value of the break year on the old base, not an estimate.
  Why: a published number comes before an own estimate (Precedence). The HSL publishes the last year on the old
  base, for the stock and for the population.

### Counts of an estimate

- A count of an estimate is rounded: to 50 for owner groups, to 10 for vacancy and construction year.
  Why: small exact numbers would look more exact than the grid, which changes them for secrecy.
- A count below its step reads „unter N“, without a tilde.
- An owner group reads „unter 200“ where the upper end is under 200. This comes first, so it is always true.
- Else it reads „~N“ where the half range is at most one third of the value, and „unsicher“ otherwise.
- „k. A.“ marks a missing value only.
- Exports round the counts of owner groups to 50.
- No count stands beside a published share or a vote share. This holds for Mindestsicherung, Arbeitslosendichte, the
  party lists and the Mieteranteil.
  Why: the Monitoring publishes shares only, and share × residents would be an own count. Every voter casts several
  votes. A count of renters adds little.

### Hand verdicts

- A building gap (`building_gaps`) counts only with a hand verdict `counts` in `reference/building_gaps_reference.csv`.
  Why: a rule alone finds schoolyards, gardens and new buildings, and one such case costs the whole layer.
- Every candidate past the filters gets a verdict in the aerial image. A doubtful one gets `site` and does not count
  until a visit. A verdict of a visit (`by=site`) wins over one of the image. A candidate without a verdict (after a
  new delivery) is not drawn until judged; the check warns.
- Only sealed or open land counts: Parkplatz, Hof, Lagerplatz, Brache. Green, tree canopy, squares, schoolyards,
  playgrounds, ways and new buildings do not.
- The minimum area is 300 m², a round number below the smallest Frankfurt example (312 m²).
- The suitability of a gap is an own conclusion. It names the largest of five real examples whose plot area the gap
  reaches (300, 365, 1,270, 2,000, 5,400 m²), with the number of the example. It is an illustration, not a plan: the
  map knows no Bebauungsplan. Each example and its quote stand in `reference/building_gaps_examples.csv`.

### Areas, not persons

- An area value describes the area. It says nothing about a single resident or house (ecological fallacy).
- A value the source publishes for several districts says so („gemeinsamer Wert der Bezirke …“).
- A district shows the class of its survey area and names it („im Umfragebezirk …“).
- A mean over districts needs values for at least 95 % of its weight. Else the area shows „k. A.“.
  Why: a mean with a missing district reads like a full value.

### Rounding and coarse breakdowns

- Every comparison uses the shown value: the value rounded half up to the decimals of the indicator.
- This holds for colour, legend, candidates, own query and histogram. Ranks are not rounded.
- A value on a class break lands in the upper class.
  Why: the reader sees the rounded value, and a comparison on the raw value can disagree with it.
- The map sorts areas roughly for housing policy. A small gap between two numbers of one value gets no note on the map.
  Example: ~1.550 in the tooltip against ~1.526 in the worked example.
- The rent burden by income group rounds to steps of 5 points on the map, its city value too. A chart of its own for
  the city rounds to whole percent. The gap gets no note. Example: the median of the lowest group reads ~55 % on the
  map and ~53 % in the view Miete. Why: the steps of 5 serve the survey areas, whose intervals are about ±5 points;
  the pooled city value has an interval of 52 to 55 %.
- A sentence goes into an ⓘ or a tooltip only if it changes how a reader reads an area. Else it goes into the README.
  Why: volunteers read little, and such notes change no political statement.

### Two y axes

- Two y axes only in the same proportion: equal height means equal share of the value of the anchor year, the first
  year of the statement.
  Why: with two free axes any line can look steeper than the other. In the same proportion the slopes compare
  growths, and the reader can check the statement by eye.
- The second series is drawn at value ÷ K on the first axis, with K = second value ÷ first value in the anchor year.
  Both dots of the anchor year coincide. Every value, also on an old base, lies inside the drawn axis.
- No view uses two y axes today. Series of different units share one axis as an index (below).

### Index of several series

- Series of different units share one axis as an index: every line is its value divided by its value in the base
  year, times 100. The base year is the first year of the statement (view Neubau: 2017, `RENT_FROM`). All lines start
  at 100.
  Why: equal height means an equal growth since the base year, so the slopes compare growths. No second axis is needed.
- Stocks count on 31.12. of a year. Rents, prices and wages count at mid-year. In an index chart they share the slot
  of their year. The base of the stocks is 31.12.2017, that of the others mid-2017.
- A rent exists in the years of a survey only (Mietspiegel: 2017, 2021, 2023 and 2025). The line joins these years and
  has a dot in each. A year without a survey has no rent and no dot. The tooltip says so.
- „Ohne Inflation“ divides a series by the price index of the same year, so the prices become the line at 100.
- The prices are the Verbraucherpreisindex of Hessen. A rent is deflated with the index of its survey month: July in
  2021, 2023 and 2025, June in 2017. A year without a survey takes July (`PRICE_MONTH`).
  Why: the survey counts the rents on one day, so the prices of that month belong to it.
- The wages are the Nominallohnindex of Hessen. A year takes the mean of the quarters 2 and 3 (`WAGE_QUARTERS`).
  Why: the survey days lie on the border of both quarters, and the quarters differ by special payments. From 2017 to
  2025 the 2nd quarter alone gives +28.3 %, the 3rd quarter alone +32.0 %, the mean +30.1 %.
- There is no price index or wage index for Frankfurt alone. Both are the indices of Hessen, and the map says so at
  the wages and in the ⓘ.
- A statement about the size of households rests on one list. The size is the persons in households divided by the
  households, both from the Melderegister. A text names the lowest and the highest size of all years of the span, not
  two years. Why: the Melderegister is irregular around 2017 (2015 to 2019) and counts other persons from 2019, so two
  years compare differently from each base year (`research/2026-11-01-rents-block-review.md`). The Melderegister never
  stands beside the Fortschreibung as a count, because it counts other persons.
- The mean of the Mietspiegel is not the average rent of all dwellings. Its two groups count different contracts: new
  contracts started in the last four years (2017) or six years (from 2021), older contracts started earlier and had a
  rent change in that time. Contracts without a change are missing. Texts name the group. The Mietspiegel leaves out
  subsidised dwellings with a bound rent; the ⓘ says so. The means are not adjusted for new and modernised dwellings
  (Gutachten 2018, page 23); the ⓘ says so too.
- The 2017 values stand as text only in the labels of a figure of the report of 2022. No sentence prints them. The
  growth rates that the reports print (check „rents growth rates of the reports“) guard their order. Two more reports
  show them as images, checked by hand (`pipeline/use_cases/new_construction/README.md`, Formula).

### Traps of the Zensus grid

- Both grids hide the values 1 and 2. In 2011 that hides 1–2 dwellings, in 2022 1–2 buildings of any size.
- 2011 counts the owner per dwelling, 2022 only per building.
- A „–“ means exactly zero or set to zero. Each use case decides how to read it and says so in its README.
- The 2011 grid counts dormitories as dwellings, the 2022 grid does not.
- A cell belongs to the area of its centre. So a cell on a border counts wholly to one area.
- The 2022 grid holds about 3 % fewer dwellings than table 4000W-1008. This gap is accepted.
- The Zensus counts about 3 % fewer residents than the register of the Monitoring.

## Ownership

### Groups

- The groups join the Zensus classes of the Eigentumsform (variable GEBEG1).
- The map has six groups: ABG und NH (class Kommune), Genossenschaften, Private Unternehmen (both company classes),
  Privatpersonen und WEG, Bund oder Land, Organisationen ohne Erwerbszweck.
- Organisationen ohne Erwerbszweck have no layer, only a row in the profile.
- The view Trend has seven groups. The two company classes, Privatpersonen and WEG stand apart.
- Trend joins Kommune and Bund oder Land as „Öffentlich“.
  Why: the Zensus counts the Nassauische Heimstätte as Bund oder Land in 2011 and as Kommune in 2022.
- Trend joins the groups into two sectors. „Privat“: companies, WEG, persons. „Gemeinschaft“: Öffentlich,
  Genossenschaften, Organisationen ohne Erwerbszweck. A sector is a plain sum of groups.
- A company group is always called private. Why: „Unternehmen“ alone also fits the ABG.
- The company classes are split only city-wide, in Trend.
  Why: the grid splits the other companies per Stadtteil only within ±87 %.
- A change of group between 2011 and 2022 may be a sale or a new classification. The data cannot tell.

### Level

- Ownership shares exist per Stadtteil only. Districts have none.
  Why: the backtest errs more per district (private companies ±60 % against ±49 % per Stadtteil).
- In the grid overlay only the colour is estimated. Every number in its tooltip is a count.
  Why: per cell the estimate is less sure, and numbers per street get quoted.

### Denominator

- All six shares divide by all dwellings of the Stadtteil in the 2022 grid.
- ABG und NH and Genossenschaften come from near-complete counts.
- The four other groups split the rest in proportion to their estimate, the dwellings without owner type included.
  Why: the table shows these four groups short, and a split in proportion is the neutral assumption.
- No single group takes the rest. Why: it would carry all errors, up to 28 % per Stadtteil.
- The six shares add up to 100 %. The count of a group is its share of all dwellings.
- Ownership shares keep one decimal. Why: whole numbers would often add up to 99 % or 101 % in the profile.
- Where under 90 % of the dwellings have an owner type, tooltip and profile say so.
- Trend divides by the sum of its own groups per year (`pipeline/use_cases/ownership_history/model.py`).
- The map shares have their own check: the share of table 4000W-2002 lies within the range of the city value
  (`pipeline/use_cases/ownership_shares/checks.py`).

### Examples

- Named owners show who stands behind a group. The map prints no numbers of them.
  Why: the dates of their sources differ.
- Each name stands with its passage in a file in `sources/`. The check fails otherwise.
- An example shows that the owner exists in Frankfurt and belongs to the group.
- The Zensus class is reported by the owner. The map does not prove it.

## Checks

- `FAIL` stops the build. It guards what would put a wrong number or sentence on the map.
- `FAIL` examples: sums that must close, the statement of a heading, a changed source format, a missing example.
- `WARN` does not stop the map build. It flags a deviation from a reference value beyond its tolerance.
- The goal is a build without `WARN`. The check report lists every remaining one.
- The website build refuses the map if the check report has a WARN or FAIL row, if the repo is dirty, or if the map
  file is older than HEAD. Commit, then rebuild.
- An accepted deviation becomes the threshold of its check. Why: a check that always warns hides a new warning.
- Every sentence of the map that states a number has a check that keeps it true after a data update.
- A comparison with a published value is a check, not a line of the ⓘ.
- If a doubt stays after the checks, the layer goes. Why: it gives an attack surface the map does not need.
- Reference values stand in `reference/`, each with its source.

| Check | Threshold | Status |
|---|---|---|
| ABG und NH, Genossenschaften per Stadtteil | in 9 of 10 Stadtteile with ≥ 200 dwellings of the group the half range is at most 15 % of the value | `WARN` below |
| ABG und NH, accepted | 35 of 41 Stadtteile | `OK` down to it |
| Same tolerance, „at most 3 points in all areas“ | not checked; the check text says so | – |
| Ownership city share against table 4000W-2002 | ±2 points | `WARN` |
| Table share within the range of the city value | value ± half range of Frankfurt | `WARN` |
| Grid dwellings against table 4000W-1008 | ±3.5 % | `FAIL` |
| Survey: own median of the tenants, city 2025 and 2024, against the printed 29 % | ±1 point | `WARN` |
| Survey: own median of the tenants per survey area against its printed class | 2 points outside the class | `WARN` |
| Survey: „mindestens 29 Prozent“ in the text of both reports | sentence present | `FAIL` |
| Survey: weight share of each survey area, 2024 against 2025 | 0.5 points | `FAIL` |
| Population per district | over 25 % and over 500 residents | `FAIL` |
| Population per Stadtteil, after the offset of the city | 10 % | `WARN` |
| Land values: Stichtag of every value used | 01.01.2026 | `FAIL` |
| Land values: zones of 2024 without a value of 2026 | more than 2 % | `WARN` |
| Miete: own Lohnsteuer and Soli against the Lohnsteuerrechner of the BMF, 2021, 2023 and 2025 | 0.01 € per month; a row per year and person, with the gross of the model | `FAIL` |
| Miete: own tariff and Soli of 2017 against the Einkommensteuerrechner of the BMF | under 0.005 € per year | `FAIL` |
| Miete: „etwa dreimal“, Mindestlohn share ÷ high-wage share in both contracts of the latest year | 2.5 to 3.5 | `FAIL` |
| Miete: the share with the Nebenkosten of the Mietspiegel instead of the BA, latest year | 1 to 4 points lower, rounded; largest at the Mindestlohn | `FAIL` |
| Miete: pension ceiling of the last year in the wage distribution of Hessen („gut 11 %“) | between P88 and P89 | `FAIL` |
| Miete: measured median of all tenants („mindestens 29 %“) | the published city value equals 29 | `FAIL` |
| Miete: „etwa der Hälfte“, median of the lowest income group at every position in its class and every value of the open class | 50 ± 7.5 points | `FAIL` |
| Miete: „knapp ein Viertel“, median of the highest income group | 20 to under 25 % | `FAIL` |
| Miete: share of the lowest income group in the lead („~17 %“) | within the bounds of the class edges; at every position in its class and every value of the open class, rounded, at most 1 percent from the main case | `FAIL` |

- Low flat roofs (`flat_roofs`):

| Check | Threshold | Status |
|---|---|---|
| Buildings per Gemarkung against the txt of the delivery | equal | `FAIL` |
| One Lieferdatum, and the year of most footprints | 26.6.2026; most footprints of 2020 | `FAIL` |
| Three reference buildings read by hand in the GML | area ±1 m², height ±0.1 m, function | `FAIL` |
| Funnel and area sums: candidates minus the roofs out of a housing zone, the very low roofs and the wall strips equal the counted area; districts and Stadtteile add up | 1 m² | `FAIL` |
| Roofs in no district | more than 5 | `WARN` |
| Wall strip never larger than the roof, never below 0 | 0.01 m² | `FAIL` |
| HBO synopsis still says 2.50 m („mindestens 2,50 m betragen“, § 6 Abs. 5 Satz 4) | sentence present | `FAIL` |

- Building gaps (`building_gaps`):

| Check | Threshold | Status |
|---|---|---|
| Portion date of the NAS delivery | 4.11.2026 | `FAIL` |
| Three reference parcels read by hand in the raw NAS | Kennzeichen equal; geometry area within max(1 m², 0.5 %) of the official area | `FAIL` |
| Cover row and a valid height pixel for every gap; cover thresholds in `alkis_meta.csv` equal `model.py`; most common flight | every gap; equal; 19.8.2025 | `FAIL` |
| Pixels without height in a gap | more than 5 % | `WARN` |
| Verdict rows: unknown verdict, reason or `by`, reason of the wrong side, „other“ without note, bad date, second row, Kennzeichen other than the gap's | any | `FAIL` |
| Gap past the filters without a verdict; stale row | any | `WARN` |
| Known cases of the user (`reference/building_gaps_known.csv`) | as expected | `FAIL` |
| Funnel and area sums; districts and Stadtteile add up | 1 m² | `FAIL` |
| Drawn gaps in no district | more than 5 | `WARN` |
| Every suitability has its example; the text names its area, number and residents (where given) | equal | `FAIL` |

- Districts under 1,000 residents in the grid or the Monitoring count neither in the population checks nor in the
  candidates.

## Demands

- Numbers flow into political demands. Unchecked data would cost credibility.
- The map states no demand and compares with no target.
- A criterion on an estimate counts only if it holds at the upper end of the range.
- A criterion with no value for an area counts as not met.
  Why: an area counts only if its gap holds despite the doubt.
- A hit of a template is a reason to look, not a finding.
- The filter of demands (what the city council can decide) belongs to the campaign material, not to this repo.
