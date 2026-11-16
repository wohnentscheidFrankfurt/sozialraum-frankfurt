# monitoring: „Mindestsicherung“, „Arbeitslosendichte“, „Benachteiligungsindex“

## Shows
`SOC_MIN_INCOME` and `SOC_UNEMPLOYED` (districts and Stadtteile, with a city value), `SOC_INDEX` (districts only,
a rank without a city value). Tooltip and profile read „Rang 46 von 114“ (a tie „Rang 23 bis 24 von 114“;
catalog field `rank` holds the number of ranks, 114).

## Formula
1. District: the value of the Monitoring 2024; districts that the monitoring merges are one area (column `Einheit`,
   table 28).
2. Shared value: a table can merge other districts than the map unit (table 12: 202/203/213, 424/25,
   323/25/26/27/28/29). The district keeps the value of that row. `SOC_UNEMPLOYED_SHARED` and `SOC_MIN_INCOME_SHARED`
   hold the numbers of the row as „202, 203 und 213“ where the row holds districts outside the unit, else nothing.
   The source CSV names the row of each table in `Gruppe_<column>` (empty: the table has no row, as 326 and 362 in
   table 14). Labels are compared as district numbers (`591/92` is `591/592`, `010` is `10`). The build stops when a
   group column is missing or names a district that no unit holds.
3. Stadtteil: mean of the districts, weighted by residents (Mindestsicherung) or residents 15 to 64
   (Arbeitslosendichte). This equals persons ÷ residents. Only when the districts with a value hold at least 95 %
   of that weight (`QUARTER_MIN_COVERAGE`), else no value. Today only Sachsenhausen-Süd for Mindestsicherung.
4. Frankfurt: the published value. For the check the same value is recomputed from the districts.
5. Benachteiligungsindex: a rank from 1 to 114. It has no city value.

## Why
The social situation shows where the need is high. The Benachteiligungsindex is a rank and has no city value. The
median of the ranks is always the middle; beside the value of a district it would look like a measurement.

## Inputs
None from other use cases. Files `sources/frankfurt/offices/Monitoring2024_Stadtbezirke_nach_Umfragebezirk.csv`,
`reference/monitoring_city_values.csv`, Stadtbezirke in `sources/frankfurt/geodata/`.

## Output
`monitoring_by_district`, `monitoring_by_quarter`, `monitoring_city`, `monitoring_checks`.

## Checks
- Recomputed city value against the published one, ± 0.3 points (Mindestsicherung, Arbeitslosendichte).

## Limits
- State of the data: end of 2022.
- Residents (`EW`, `HH`, `EW15_65`) are empty for districts 40 and 592 in the source (suppressed); they weigh nothing.
- Mindestsicherung counts residents of homes for refugees.
- Bürgergeld started on 1.1.2023; 2022 still counts Arbeitslosengeld II.
