# Research

Questions to the data, their scripts and their results, sorted by date. These are working notes with a date. A
finding may hold an older number; the numbers of the map count.

- A finding is a Markdown file `<date>-<topic>.md` at the top of this folder.
- Scripts lie in `scripts/`, their results in `results/`.
- The original data lies in `sources/`. `mon.py` writes `Monitoring2024_Stadtbezirke_nach_Umfragebezirk.csv`; it lies
  in `sources/frankfurt/offices/` next to the monitoring PDF, because the build reads it.

## Rules

- Every number is checked against the source. Labels: [belegt], [eigene Auswertung], [unsicher], [offen].
- Sources are named with their path in `sources/`.
- The findings up to 8 Oct 2026 are German. They are historical records and are not translated. New findings are
  English.
- The text of a finding is not changed later. Before the repo went public (16.11.2026), names of persons, unpublished
  mails and internal matters of the initiative were removed. Old paths in it are explained in the section
  "Old folder names".
- A blank line comes before every list.

## Keeping and removing

- A finding stays while a file outside `research/` names it: `CLAUDE.md`, a README, `docs/`, code, tests or
  `reference/`. A script or result of `research/` counts too when such a file names it and it names the finding. A
  finding that only another finding names does not count.
- A finding that records only a data situation stays only when the situation stands nowhere else: a source that does
  not exist, a way to a source, a trap. It is listed in the section "Data situation". Better: its core goes into the
  README of the use case or into `sources/README.md`, and the finding goes.
- All other findings go: replaced by a later finding or a README, dropped (a spike, a removed layer), or outside the
  map.
- A script stays only when it runs against today's pipeline and a finding, a source or a file outside `research/`
  needs it. A result follows its finding or the file that names it.
- A branch adds a finding only when a file outside `research/` names it, or when it records a data situation. A
  review or QA report without such a name stays with the spec and the plan in the scratch folder of the user.
- Removed files stay in Git. The history before 16 Nov 2026, with its tags, lies only in a local archive clone (not
  public). Its tag `research-history-2026-11-01` holds every finding up to 1 Nov 2026. A Git tag or `git log` named
  in a finding refers to this archive.
- The test `test_every_finding_is_named` in `tests/test_doc_paths.py` lists every finding that no file names.

## Data situation

Findings that stay only for their data situation. None at present.

## Findings

| Finding | Language |
|---|---|
| `2026-10-06-wohnungsmarkt-sozialraum-protokoll.md` | German |
| `2026-10-08-abg-abgleich-protokoll.md` | German |
| `2026-10-09-private-companies-2011-2022.md` | English |
| `2026-10-09-survey-social-aspects.md` | English |
| `2026-10-10-abg-combined-sources.md` | English |
| `2026-10-10-abg-estimate-accuracy.md` | English |
| `2026-10-10-buildings-and-dwellings-by-owner.md` | English |
| `2026-10-11-heat-saving-and-construction-year.md` | English |
| `2026-10-12-living-space-grid.md` | English |
| `2026-10-12-uncertainty-of-ownership.md` | English |
| `2026-10-14-who-are-the-private-companies.md` | English |
| `2026-10-15-new-construction-data.md` | English |
| `2026-10-15-third-private-housing-company.md` | English |
| `2026-10-17-qa-situation-burden.md` | English |
| `2026-10-20-land-values-2026.md` | English |
| `2026-10-20-rent-burden-by-income.md` | English |
| `2026-10-22-public-housing-fills.md` | English |
| `2026-10-25-dwelling-stock.md` | English |
| `2026-10-31-household-types.md` | English |
| `2026-10-31-real-rents.md` | English |
| `2026-10-31-rents-wages.md` | English |
| `2026-11-01-rents-block-review.md` | English |
| `2026-11-01-warm-rent-and-income.md` | English |
| `2026-11-10-flat-roofs.md` | English |
| `2026-11-15-building-gaps.md` | English |

A finding can be turned into docx: `pandoc research/<name>.md -o <name>.docx`.

## Scripts

Call from the repo root with `.venv/bin/python -I research/scripts/<script>.py …`. The column "Call" shows the
arguments.

| Script | Purpose | Call |
|---|---|---|
| `lif.py` | Single dataset "Leben in Frankfurt 2025": rent per m² by landlord, lock-in when moving (weighted with `weight`) | `lif.py <leben-in-frankfurt_2025.csv> [rent cap, default 1550]` |
| `rent_burden_income.py` | Rent burden of tenants by household income from the datasets 2025 and 2024: validation against the reports, groups, pooled values, bootstrap, sensitivity, worked example (`research/2026-10-20-rent-burden-by-income.md`) | `rent_burden_income.py <leben-in-frankfurt_2025.csv> <leben-in-frankfurt_2024.csv>` |
| `boris_2026_zone_match.py` | BORIS: do the zones of 2024 keep their number in 2026? Three points per zone against the WMS (`research/2026-10-20-land-values-2026.md`) | `boris_2026_zone_match.py <out.csv>` |
| `boris_2026_cells.py` | BORIS: all zones of 2026 at the centre of every inner cell (WMS) | `boris_2026_cells.py <out.csv>` |
| `boris_2026_compare.py` | Built land values against `results/boris_2026_cells.csv`, per cell, Stadtteil, district and city | `boris_2026_compare.py` |
| `rent_burden_west_mitte_west.py` | Why the overall burden differs between West and Mitte-West while the three income groups do not: group shares, unrounded group medians, income-mix counterfactual, bootstrap of the difference; uses the functions of the map (`research/2026-10-20-rent-burden-by-income.md`, Addendum) | `.venv/bin/python -I research/scripts/rent_burden_west_mitte_west.py` (repo root) |
| `bez.py` | Population per survey area: income, landlord, origin, education, families, overcrowding | `bez.py <leben-in-frankfurt_2025.csv>` |
| `map.py` | Assign quarters to survey areas via WFS | `map.py <Umfragebezirke.gml> <Stadtteile.gml>` |
| `mon.py` | Read monitoring 2024 (part 1) from the PDF, assign districts, summarise indicators | `mon.py <Monitoring.pdf> <Umfragebezirke.gml> <Stadtbezirke.gml> <Stadtteile.gml> <output folder> [<Demographische Kennzahlen (Stadtbezirke).xlsx>]` |
| `kw_extract.py` | Local council election 2026: votes, seats and turnout from the subpages of the Statistikportal (Plotly JSON in `kap2/Ortsbeirat-1.html` to `-16.html`). The result lies in `sources/frankfurt/statistics/` | download the 16 subpages with curl as `obr1.html` … `obr16.html` into a folder, then `kw_extract.py <folder> <output folder>` |
| `space_check.py` | Wohnfläche je Bewohner: Zensus 2022 grid (weighted by residents) against the Zensus database, for Germany and Frankfurt (`research/2026-10-12-living-space-grid.md`). Result in `research/results/space_check.txt`. The pipeline no longer downloads `cache/zensus_space_per_resident.zip`; after a cache wipe fetch it from `https://www.destatis.de/static/DE/zensus/gitterdaten/Durchschnittliche_Wohnflaeche_je_Bewohner_in_Gitterzellen.zip` | `space_check.py cache` |
| `formula_review.py` | Numbers behind the formula review (old protocol in tag `docs-history-2026-10-20` of the archive): Zensus 2011 against 2022 per owner group, coop and ABG+NH formulas, denominator, backtest, Wohnfläche, templates. Reads the interim data of a build | `formula_review.py interim > research/results/formula_review.txt` |
| `abg_accuracy_extract.py` | Frankfurt extract of the grids 2011 and 2022 for the accuracy test of the ownership estimate (`research/2026-10-10-abg-estimate-accuracy.md`). Reads the grids from `cache/` and `interim/cells_2022.csv`, writes `cache/abg_accuracy/` | `abg_accuracy_extract.py` |
| `abg_accuracy.py` | Accuracy of the ownership estimate per district and Stadtteil: the methods E0 to E2 on the 2011 grid against the counted dwellings (`research/2026-10-10-abg-estimate-accuracy.md`). Results in `research/results/abg_accuracy_*.csv` | `abg_accuracy.py` |
| `abg_combined.py` | Count of 2011 × change up to 2022, research sites and error budget per Stadtteil (`research/2026-10-10-abg-combined-sources.md`). Results in `research/results/abg_combined_*.csv` | `abg_combined.py` |
| `uncertainty_scenarios.py` | Scenarios of the Unsicherheit per owner group (`research/2026-10-12-uncertainty-of-ownership.md`; old protocol in tag `docs-history-2026-10-20` of the archive): smallest, median and largest half range, what sets the range of ABG+NH and of the Genossenschaften, Abgleich against the half range of Frankfurt. Reads the interim data of a build | `uncertainty_scenarios.py interim > research/results/uncertainty_scenarios.txt` |
| `qa_construction_year_variants.py` | Construction year (`research/2026-10-17-qa-situation-burden.md`): five ways to share the 2011 classes on the 2022 dwellings; Hausen and the city. Reads the interim data of a build; `cache/zensus_construction_year.zip` only for variant V4. Results in `research/results/qa_construction_year_variants*` | `qa_construction_year_variants.py` (no arguments, from the repo root) |
| `vacancy_km.py` | Reference values of the check „Vacancy: city values against the 1-km grid“ (`reference/check_reference.csv`): both rates of the 185 1-km cells wholly inside Frankfurt, weighted with the dwellings of the 1-km grid. Reads `interim/cells_2022.csv`, `sources/zensus/grid/` and `cache/zensus_dwellings.zip`. Result in `research/results/vacancy_km.txt` | `vacancy_km.py > research/results/vacancy_km.txt` |
| `qa_vacancy_fill.py` | Vacancy (`research/2026-10-17-qa-situation-burden.md`): the „–“ cells filled from the 1 km grid; city, Stadtteile, districts; test of the owner rate. Reads the interim data and `sources/zensus/grid/`; `cache/zensus_owner_rate.zip` only for the owner part. Results in `research/results/qa_vacancy_fill*` | `qa_vacancy_fill.py` (no arguments, from the repo root) |
| `public_housing_fills.py` | What the fills of ABG and Nassauische Heimstätte add, and what the map loses without them; reruns the step `public_housing` without writing (`research/2026-10-22-public-housing-fills.md`) | `public_housing_fills.py > research/results/public_housing_fills.txt` |
| `rents_block_review.py` | Review of the block of rents of the view „Neubau“ (`research/2026-11-01-rents-block-review.md`): growth of dwellings and population per start year in four calculations, the overcount that would turn the heading, the drift of the stock, persons per household of the Melderegister per base year, the sampling error of the Mietspiegel means. Reads the interim data of a build. Result in `research/results/rents_block_review.txt` | `rents_block_review.py interim "<Demographische Kennzahlen (Stadtbezirke).xlsx>" <bevoelkerung_in_haushalten_stadtbezirke_.csv> > research/results/rents_block_review.txt` |
| `warm_rent_wage.py` | Warm rent of 55 m² against the net wage of three model persons (Mindestlohn, median, pension ceiling), 2017 to 2025, new and older contracts, with sensitivities, measured values, the bridge to the block of rents and where the ceiling lies (`research/2026-11-01-warm-rent-and-income.md`). Reads the interim data of a build | `warm_rent_wage.py > research/results/warm_rent_wage.txt` |
| `net_wage.py` | Net monthly wage of a single full-time employee by the Programmablaufplan of the BMF, 2017 to 2025, checked against the calculators of the BMF (`research/2026-11-01-warm-rent-and-income.md`) | `net_wage.py` |
| `flat_roofs_breakdown.py` | Low flat roofs: the funnel of the build and the roof candidates by BORIS zone class and by AdV function (`research/2026-11-10-flat-roofs.md`). Runs the model of `flat_roofs` on the sources. Result in `research/results/2026-11-10-flat-roofs.txt` | `flat_roofs_breakdown.py > research/results/2026-11-10-flat-roofs.txt` |
| `building_gaps_sheet.py` | Building gaps: judgement sheet. An RGB and a CIR crop of the orthophoto 2025 with the parcel outline for every gap past the cover filters without a verdict row (`--all` draws every such gap, `--ids` chosen ones). The verdicts go by hand into `reference/building_gaps_reference.csv` (`pipeline/use_cases/building_gaps/README.md`, `research/2026-11-15-building-gaps.md`). Pages and `index.csv` in `research/results/building_gaps_sheet/`; the PNG pages are not in Git (about 37 MB, drawn again from the WMS and `cache/dop/`) | `building_gaps_sheet.py [--all] [--ids ID,ID] [--per-page 12] [--out FOLDER]` |
| `low_income_burden.py` | Warm rent against household income of tenants under 2,000 €, survey 2024+2025: shares, burden classes, bootstrap, sensitivities, Mikrozensus values of the city (`research/2026-11-01-warm-rent-and-income.md`) | `low_income_burden.py > research/results/low_income_burden.txt` |

The `.txt` results `Einzeldatensatz_*.txt` in `research/results/` were captured with German console headers. A rerun
of `lif.py` or `bez.py` prints English labels.

Traps to know:

- Area, rent, length of residence and age exist only in classes. Always check classes against the codebook. Example:
  `XDhhnek_a`, class 4 = 3,000 to under 4,000 €.
- `WOverm_a` = 2 means public housing company, so ABG, Nassauische Heimstätte and the federal government.
- frankfurt.de answers automatic requests with 403, also to headless Chrome. Such PDFs are downloaded by hand and
  put into `sources/`.

## Old folder names

- Findings removed on 1 Nov 2026 lie under the tag `research-history-2026-11-01` of the archive:
  - `2026-10-07-abg-bestand-und-bindungen.md`
  - `2026-10-07-nh-aus-gitter-2011/`
  - `2026-10-08-abg-holding-abgleich/`
  - `2026-10-08-leerstand/`, now `scripts/vacancy_km.py`
  - `2026-10-08-sozialwohnungen-bindungen-protokoll.md`; a copy lies with the protocols of the campaign, outside the
    repo
  - `2026-10-08-sozialwohnungen-je-stadtteil.md`
  - `2026-10-14-examples-of-owner-groups.md`
  - `2026-10-14-links-without-file.md`
  - `2026-10-15-grid-feasibility.md` and `2026-10-15-simplification-review.md` (formula G), with
    `scripts/formula_g.py`, `scripts/grid_feasibility.py` and their results
  - `2026-10-24-owner-associations-tenancy-and-heating.md`; a copy lies outside the repo
- Older findings use the old folder names. Mapping:
  - `quellen/` is now `sources/`.
  - `auswertungen/` is now `analyses/` (`auswertungen/ergebnisse/` is `analyses/results/`).
  - `protokolle/` is now `findings/`.
  - `zwischen/` is now `interim/`.
  - `ausgabe/` is now `output/`.
  - `konstanten/` is now `reference/`.
  - `docs/recherche/` is now `docs/research/`.
  - `findings/` is now `research/`. The three German protocols got a date in front of their name:
    `Wohnungsmarkt_Sozialraum_Protokoll.md`, `Sozialwohnungen_Bindungen_Protokoll.md`, `ABG_Abgleich_Protokoll.md`.
  - `analyses/` is now `research/scripts/`; `analyses/results/` is now `research/results/`.
  - `docs/research/` is now `research/`.
  - `docs/specs/` and `docs/plans/` were deleted on 13 Oct 2026. The archive holds them (`git log --all -- docs/specs`).
  - `analyses/results/Monitoring2024_Stadtbezirke_nach_Umfragebezirk.csv` is now in `sources/monitoring/`.
  - `sources/01 Umfrage Leben in Frankfurt 2025/` is now `sources/survey/`.
  - `sources/02 Gebäude- und Wohnungsbestand/` is now `sources/buildings/`.
  - `sources/03 Sozialmonitoring 2024/` is now `sources/monitoring/`.
  - `sources/04 Mietpreisüberhöhung & Mietenregister/` is now `sources/rents/`.
  - `sources/05 Eigentümerstruktur/` is now `sources/ownership/`.
  - `sources/06 Geodaten/` is now `sources/geodata/`.
  - `sources/07 Sozialwohnungen & Bindungen/` is now `sources/social_housing/`.
  - `sources/08 Wohnungspolitik der Stadt/` is now `sources/housing_policy/`.
  - `sources/09 Kommunalwahl 2026 Ergebnisse/` is now `sources/election/`.
  - `sources/10 Wärmeplanung/` is now `sources/heat_planning/`.
  - `sources/01 …/Statistikportal-Exporte/` is now `sources/survey/statistikportal/`.
  - The `Zensus2022_*` files of `02` and `05` are now in `sources/zensus/`.
  - Since 14 Oct 2026 `sources/` is ordered by origin (the decision of 14 Oct 2026, tag `docs-history-2026-10-20` of
    the archive):
    - `sources/buildings/` and `sources/survey/` are now in `sources/frankfurt/statistics/`;
      `sources/survey/statistikportal/` is now `sources/frankfurt/statistics/statistikportal/`.
    - `sources/social_housing/` is now `sources/frankfurt/parlis/`.
    - `sources/geodata/` is now `sources/frankfurt/geodata/`.
    - `sources/monitoring/` and `sources/housing_policy/` are now in `sources/frankfurt/offices/`, except
      `Demographische Kennzahlen (Stadtbezirke).xlsx` (`sources/frankfurt/statistics/`).
    - `sources/election/`: the gazette is in `sources/frankfurt/offices/`, the three CSV files in
      `sources/frankfurt/statistics/`.
    - `sources/heat_planning/`: the PARLIS documents (M 109/2026, M 118/2024) are in `sources/frankfurt/parlis/`, the
      preview of the Geodatenkatalog in `sources/frankfurt/geodata/`, the rest in `sources/frankfurt/offices/`.
    - `sources/rents/`: the Mietspiegel annex is in `sources/frankfurt/offices/`, the statement to the Bundestag in
      `sources/other/`.
    - `sources/ownership/`: F 3283/2025 is in `sources/frankfurt/parlis/`; Vonovia, GWH, Catella and cash-online are
      in `sources/companies/`; the RLS profile, „Wem gehört die Stadt?“ and the ABG research are in `sources/other/`.
      The copy `statistik_aktuell_2013-11_GWZ_2011_Frankfurt.pdf` was deleted; the same file is
      `sources/frankfurt/statistics/statistik.aktuell 11-2013 Gebäude und Wohnungen Frankfurt.pdf`.
  - `Weblinks.txt` and `Hinweis.txt` are now sections of `sources/README.md`.
  - `pipeline/<use case>/` is now `pipeline/use_cases/<use case>/` (14 Oct 2026), for example
    `pipeline/public_housing/`.
  - `pipeline/core/`, `pipeline/zensus/` and `pipeline/geography/` are now in `pipeline/shared/`.
  - `pipeline/infra/` was split: `download.py` is in `pipeline/engine/`; `gml.py`, `pdf.py` and
    `reference.py` are in `pipeline/shared/readers/`.
  - `pipeline/steps.py`, `pipeline/store.py` and `pipeline/datasets.py` are now in
    `pipeline/engine/`. `inner_cells` moved to `pipeline/shared/zensus/cells.py`.
  - `pipeline/assembly/` and `pipeline/checks/` are now in `pipeline/map/`; the old `pipeline/map/` is
    `pipeline/map/html/`.
  - Imports follow the folders: `pipeline.zensus` is `pipeline.shared.zensus`, `pipeline.public_housing` is
    `pipeline.use_cases.public_housing`, and so on.
