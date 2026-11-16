# protection: „Abdeckung mit Milieuschutz“

## Shows
`PROT_SOCIAL` (profile and criterion; no layer), the names of the statutes per area. Districts and Stadtteile.
Topic „Planung“; the profile block „Planung“ lists the statutes and the pending plans.
Overlays „Milieuschutz“, „Milieuschutz im Verfahren“, „Ortsbild“, „Ortsbild im Verfahren“. Each has a `key` (its
name in the overlay key under the legend, without the pattern word). The tooltips carry no plan codes.

## Formula
Residents in cells whose centre lies in a valid area under § 172 Abs. 1 Nr. 2 BauGB ÷ residents of the area.

## Why
The overlays show where Milieuschutz and Ortsbild statutes apply or are in preparation. The layer shows the share of
residents under Milieuschutz, so areas that look alike but have no statute stand out.

## Inputs
`cells_2022`; files `sources/frankfurt/geodata/planAS_erhaltungssatzungen_e-rv.gml` and
`sources/frankfurt/geodata/planAS_erhaltungssatzungen_e-iv.gml` (planAS WFS),
Stadtbezirke and Stadtteile in `sources/frankfurt/geodata/`; the monitoring table
`sources/frankfurt/offices/Monitoring2024_Stadtbezirke_nach_Umfragebezirk.csv` joins the Stadtbezirke into the 114
districts; `reference/social_preservation_expected.csv`.

## Output
`protection_cells`, `protection_by_district`, `protection_by_quarter`, `protection_city`, `protection_overlays`,
`protection_checks`.

## Checks
- The areas under No. 2 against the list of 6.10.2026 (WARN on a new or a missing area).
- Both WFS answers hold areas.

## Limits
- Areas in procedure do not count.
- Ortsbild (No. 1) is only an overlay; it counts in no indicator.
