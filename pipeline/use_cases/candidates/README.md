# candidates: „Kandidaten“

## Shows
Three templates: „Milieuschutz-Kandidat“ (districts), „Genossenschafts-Lücke“ (Stadtteile), „Lücke bei öffentlichen
Wohnungsbaugesellschaften“ (Stadtteile). No indicator of its own.

- Each template has a `lead` under the select. The lead of „Milieuschutz-Kandidat“ has three sentences. The last
  one says that a hit is a reason to look closer, not a finding.
- „Eigene Abfrage“ has `CUSTOM_NOTE` (key `custom_note`) instead: it names the groups without a Bezirk value
  (Eigentum, Sozialwohnungen, Wahl); a test pins them against the catalog.
- A criterion on the upper end of an estimate has a `note` (`UPPER_END_NOTE`, key `upper_end_note`): the Stadtteil
  counts only when the upper end of the estimate lies below the threshold too.
- A count line near the top names the full hits and the areas that miss one criterion. It scrolls to the list.
- The list has two headings, „Alle Kriterien erfüllt (n)“ and „Ein Kriterium fehlt (n)“. The second names the missing
  criterion. A heading without items is not shown.

- „Genossenschafts-Lücke“: Genossenschaften, upper end of the range (`OWN_COOP_HIGH`) below the city value of
  `OWN_COOP`; Mieteranteil at or above the city value; a pending plan (`LAND_PENDING_PLAN`).
- „Lücke bei öffentlichen Wohnungsbaugesellschaften“: Mindestsicherung at or above the city value; ABG and NH, upper
  end of the range (`OWN_PUBLIC_HIGH`) below the city value of `OWN_PUBLIC`.

## Formula
A criterion compares an indicator with the city value or a fixed number. A criterion on the end of a range has the
keys `city` (the indicator whose city value is the threshold, unit and ⓘ) and `label` (its title in the tab and the
CSV). An area is a full hit when it meets every
criterion. A criterion with no value for the area counts as not met (`meets` in `model.py`); the tooltip names it
„k. A. bei …“. Districts under 1,000 residents do not count; Stadtteile have no such rule.

Comparisons use the shown values. The value and the threshold (city value or fixed number) are rounded half
up to the decimals of the indicator before the comparison: `floor(x * 10^d + 0.5) / 10^d`. A criterion uses the
decimals of its `city` indicator if set (`OWN_COOP_HIGH` rounds like `OWN_COOP`). A rank (indicator with `rank`) is not
rounded. So a district that shows 79,9 meets „at or above the city value 79,9“ although the stored value is a little
lower. The step reads `decimals` and `rank` from `map_catalog`; the browser applies the same rule, and the browser check
compares both.

In the browser (`web/js/02_candidates.js`):

- The default threshold is the city value. A criterion added by hand without a city value gets the median of the
  areas. Only number and yes/no indicators of the level of the template with `criterion` set can be added. „Eigene
  Abfrage“ works on districts.
- The list shows full hits and areas that miss one criterion, under two headings, sorted by name. The tooltip names
  the missing criteria. The histogram sentence stands once, in the tab note.
- The CSV is called `<prefix>_<slug>.csv` (`kandidaten_milieuschutz.csv` in German; prefix and slug: texts
  `ui.candidates.csv.file_prefix` and `ui.candidates.csv.slug.<template>` of `pipeline/map/html`). It has a BOM and
  the columns of its level.

## Why
The templates point to areas that fit a demand. „Milieuschutz-Kandidat“: many renters, much Mindestsicherung, much old
stock and high land values, but less than half the residents under Milieuschutz. „Genossenschafts-Lücke“: few
Genossenschaften, many renters and a pending plan. „Lücke bei öffentlichen Wohnungsbaugesellschaften“: high need, but
few dwellings of ABG and Nassauische Heimstätte. Each template works on its level: ownership exists only per Stadtteil.
The template „Milieuschutz-Kandidat“ uses „Altbau vor 1919“, the class closest to the Gründerzeit
(`pipeline/use_cases/construction_year/README.md`). The two ownership templates check the upper end of the range, so
only a Stadtteil that stays below the city value despite the doubt is a hit. The numbers flow into demands, so a gap
must hold despite the estimate. The map shows no range, so „oberes Ende der Spanne“ would mean nothing to a reader.
The labels therefore name what is compared: „Genossenschaften (Schätzung plus Unsicherheit)“, „ABG und Nassauische
Heimstätte (Schätzung plus Unsicherheit)“. Operator and threshold stand below the label.

## Inputs
`indicators_districts`, `indicators_quarters`, `city_values`, `map_catalog` (decimals and rank per indicator).

## Output
`candidates_reference` (hits per template for the browser check).

## Checks
None in the build; `tests/browser/desktop/candidates.spec.mjs` compares the map with the reference.

## Limits
- „Genossenschaften (Schätzung plus Unsicherheit) unter dem Stadtwert“ filters little: a Stadtteil without coops always
  meets it. The template rests on Mieteranteil and the pending plan.
