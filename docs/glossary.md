# Glossary

The domain speaks German, the code speaks English. This table is the bridge. Proper names and source vocabulary
stay German (see "Stays German").

## Core terms

| German | English identifier | Meaning |
|---|---|---|
| Stadtbezirk | `district` | One of 114 analysis units of the city's monitoring ("Einheit"); some join several statistical districts. |
| Stadtteil | `quarter` | One of 45 city quarters; Sachsenhausen-Süd and Flughafen count as one. |
| Nettoäquivalenzeinkommen | `income` (`income_low`, `income_high`) | Household income divided by the equivalence scale; class `XDhhnek_a` of the microdata. |
| Haushaltsnettoeinkommen | `household_income` | Net income of the household; the income groups of the rent burden use it. |
| Einkommensgruppe | `BREAKDOWN_IDS` (column `group`) | One of three groups of household net income: under 2,000 €, 2,000 to under 3,200 €, 3,200 € and more. |
| Umfragebezirk | `survey_area` | One of 13 areas of the survey "Leben in Frankfurt"; a union of districts. No map level. |
| Gebiet | `area` | A district or a quarter. |
| Ebene | `level` | `district` or `quarter`. |
| Gitterzelle | `cell` | A 100 m cell of the Zensus grid (EPSG:3035). |
| Randzelle | `edge_cell` | A cell outside all districts but within 71 m of the city. |
| Wohnung | `dwelling` | A dwelling as counted by the zensus. |
| Gebäude | `building` | A building with living space. |
| Häuser (visible text) / Gebäude mit Wohnraum | `buildings` | The view "Trend" says "Häuser"; only the source line says "Gebäude mit Wohnraum". |
| Wohnungen im Gebäude | `size` (of a building) | Number of dwellings in a building, Zensus variable GEBWG2; classes in `SIZES`. |
| große Häuser (ab 13 Wohnungen) | `large buildings` (`LARGE`) | Buildings with 13 or more dwellings. |
| gezählt 2011 | `counted_2011` | Coop dwellings the Zensus 2011 counted in a cell (`coops`). |
| Geheimhaltungslücke | `gap_2011`, `gap_public` | Dwellings without owner in the 2011 grid because of secrecy, at the coop share of the cell in 2022 (`coops`); in `public_housing` the public dwellings of table 4000W-1011 that the grid 2011 does not locate, part of the range. |
| Schätzung 2022 | `estimate_2022` | Coop dwellings estimated from the buildings of 2022, for cells without a coop count in 2011 (`coops`). |
| Einwohner | `pop` | Residents. |
| Haushalt | `household` | Household. |
| Stadt (tab) | `city` | The tab of the whole city: the choices of the map. Not to be confused with `city_value` (Stadtwert). |
| Kennzahl | `indicator` | A value per area, with metadata in the catalog. |
| Stadtwert | `city_value` | The value for all of Frankfurt, computed the same way as for the areas. |
| Klasse (einer Abbildung) | `class` | A range as printed in a legend, for example 64–70; `<ID>_LOWER` holds its lower end. |
| Schicht | `layer` | An indicator shown as a choropleth. |
| Details | `overlay` | Areas drawn above the choropleth (statutes, plans, zones, grid). |
| Quelle, Stand | `source`, `as_of` | First two lines of the ⓘ (result protocol). |
| Rechnung | `calc` | How the value of an area is computed; line of the ⓘ. |
| Regel | `rule` | When no value shows or what does not count; line of the ⓘ. |
| Unsicherheit | `uncertainty` | How far an estimate or a survey can be off; line of the ⓘ, in plain sentences. |
| Tilde (~) | `estimate` | Marks an estimated value on the map: „~17,8 %“. |
| Abgleich | (check) | Value of the map beside a published value; a check of the build, not a line of the ⓘ. |
| Rücktest | backtest | The estimate applied to 2011, where the counts are known; its error in 9 of 10 Stadtteile sets the half range. On the map: `test_2011` („Die Karte hat die Schätzung mit den Zahlen von 2011 getestet.“). |
| Spanne | range (`_LOW`, `_HIGH`); half range `half` | The range of an estimate. The map does not show it; the candidates compare its upper end (`_HIGH`). |
| Stand | `as_of` | The reference date of a value. |
| Quelle | `source` | Where a value comes from. |
| Kandidatenvorlage | `candidate template` | A saved set of criteria. |
| Kriterium | `criterion` | Indicator, comparison and threshold. |
| Schwelle | `threshold` | The value a criterion compares with. |
| erfüllt | `met` | A criterion holds for an area. |
| Prüfung | `check` | One test of the check report. |
| Prüfbericht | `check report` | `interim/check_report.md`. |
| OK / WARNUNG / ABBRUCH | `OK` / `WARN` / `FAIL` | `FAIL` stops the build. |
| Eigentumsform | `ownership type` | One of eight Zensus classes. |
| Eigentümergruppe | `owner group` | Classes joined for the map (for example persons and condominium owners). |
| nicht zugeordnet | `unassigned` | Dwellings without an ownership type. |
| Öffentlich (Kommune, Bund, Land) | `public` | Group of the view Trend: municipality and Federation/Land together. |
| Eigentümergemeinschaft (WEG) | `condo` | Owners' association of a building split into condominiums. |
| Baujahr (Jahrzehnte) | `decade` | Class of the year of construction in table 3000G-2001. |
| Baujahr (Mikrozensus-Klassen) | `construction year class` (`pre1919`, `1949_1978`) | Class of the year of construction in the Zensus grid and in table 4000W-1008: Vor 1919, 1919–1948, 1949–1978, later classes. |
| Altbau vor 1919 | `HOU_PRE1919` | Dwellings in buildings built before 1919 (count of 2011) per dwellings of 2022; the closest class to the Gründerzeit. |
| Nachkriegsbau 1949–1978 | `HOU_1949_1978` | Dwellings in buildings built from 1949 to 1978 (count of 2011) per dwellings of 2022. The first Wärmeschutzverordnung came into force on 1.11.1977. |
| Altbestand | `older stock` | Buildings built before 2010. |
| Neubau | `new_construction` (`new`) | Dwellings in new residential buildings (`new_res`, Wohnheime included) plus dwellings in new non-residential buildings (`new_nonres`); the view „Neubau“. |
| Umbau | `conversion` (`conversions`) | All completed dwellings minus new construction. The map says „Umbau bestehender Gebäude“; a net balance, no table gives it directly. |
| Baumaßnahmen an bestehenden Gebäuden | `measures at existing buildings` | Term of the HSL: Umbau-, Ausbau-, Erweiterungs- oder Wiederherstellungsmaßnahmen. What the map shows as conversions. |
| Nichtwohngebäude | `non-residential building` | Building mainly for other use than living. Its new dwellings count as new construction. |
| Bestand (Wohnungsbestand) | `stock` | Dwellings in residential and non-residential buildings on 31.12. of a year (HSL); the red line of the block of rents in the view „Neubau“. |
| Bevölkerung (Bevölkerungsstand) | `population` | Persons with Hauptwohnsitz in Frankfurt on 31.12. of a year (HSL, Fortschreibung des Bevölkerungsstands, Regionaldatenbank 12411-01-01-4); the black line of the block of rents in the view „Neubau“. |
| Einwohner*innen | `population` | What the map calls the population in the view „Neubau“ (key, end label, tooltips): persons with Hauptwohnsitz in Frankfurt. |
| Hauptwohnsitz | (main residence) | The residence a person mainly lives in. The Fortschreibung des Bevölkerungsstands counts persons only there. |
| Melderegister | (residents' register) | The city's register of residents. It counts differently from the Fortschreibung: about 20,000 more from 2022, no Zensus break. The view „Neubau“ takes only the persons per household from it. |
| Fortschreibung | `stock update` | How the HSL carries the stock forward: stock of the year before + completed dwellings − outflow, on the base of the last Zensus. Not a count. The population is carried forward the same way, with births, deaths and moves. |
| Abgang | `outflow` | Dwellings that leave the stock, for example by Abriss or Umnutzung. The build computes it as a rest: completed dwellings − change of the stock. |
| Bruch der Basis | `break` (`STOCK_BREAKS`, `break_year`) | First year of a Fortschreibung on a new Zensus base (2022), for the stock and the population. No change, no outflow, no line segment to the year before; a dotted segment to the hollow dot on the old base. |
| Bestand auf alter Basis | `bridge` (`OLD_BASE`, `old_base`) | The value of the break year on the old Zensus base: the stock on 31.12.2022 on the Gebäude- und Wohnungszählung 2011 (report F I 1 j/22, 408,605), the population on the Zensus 2011 (report A I 2, 2nd half of 2022, 773,068). The chained growth and the hollow dots use it. |
| Basiseffekt | `base effect` | Value of the break year on the new base minus the value on the old base: what the new Zensus moves by itself (Frankfurt 31.12.2022: stock −4,378, population −25,679). |
| Mietspiegel | `surveys` (`RENT_SOURCES`, `read_rent_surveys`) | The city's table of comparative rents. The view „Neubau“ reads the sample means of its reports (Gutachten) in the survey years 2017, 2021, 2023 and 2025. |
| Erhebungsstichtag | `survey date` (`SURVEY_DATES`, `month`) | The day the Mietspiegel counts the rents: Juni 2017, 1.7.2021, 1.7.2023, 1.7.2025. |
| Neuvertrag | `new` (`new_index`, `new_real`) | A contract that started in the observation period before the survey day: four years in 2017, six years from 2021. The map says „Miete neuer Verträge“. |
| erhöhter Altvertrag | `old` (`old_index`, `old_real`) | A contract that started before that period and had a rent change in it (2024: „veränderter Altvertrag“). Contracts without a change are not in the Mietspiegel. The map says „Miete älterer Verträge“. |
| Verbraucherpreisindex (VPI) | `prices` (`prices_index`) | The price index of Hessen, 2020 = 100 (HSL report M I 2 j/25, table 3). Frankfurt has none. The map says „Preise“. |
| Nominallohnindex | `wages` (`wages_index`) | The index of the gross monthly earnings of Hessen including special payments, 2022 = 100 (HSL press table, per quarter). A year is the mean of the quarters 2 and 3 (`WAGE_QUARTERS`). The map says „Löhne in Hessen“. |
| Personen je Haushalt | `household` (`household_low`, `household_high`) | Persons in households divided by households, Melderegister, row `insgesamt` (`read_household_size`): 2017 to 2025 from 1.8446 (2025) to 1.8741 (2019). |
| Index (2017 = 100) | `*_index` (`RENT_FROM`) | A value divided by the value of the base year, times 100. |
| ohne Inflation | `*_real` | An index divided by the price index of its year, times 100. The prices become the line at 100. |
| Warmmiete | `warm_rent` | Net cold rent plus Betriebskosten and Heizkosten, per month. The view „Miete“ sets it against the net wage of a model person and against the household income of tenants. |
| Nettolohn | `net` | Gross monthly wage minus the employee contributions, Lohnsteuer and Soli; Steuerklasse I, no children, no church tax (`net` in `pipeline/use_cases/rent_burden/model.py`). |
| Rechenbeispiel | `wage example` (`wage_table`, `WAGE_TEXTS`) | A model person computed from published inputs, not a measured household (`docs/data-rules.md`, Counted or estimated). Not the „Rechnung am Beispiel“ of an ⓘ (`calc_example`). |
| Mindestlohn | `mindestlohn` (`MINDESTLOHN`) | The statutory minimum wage per hour; full time is hourly × 40 × 52 ÷ 12 (`full_time`). One of the three model persons. |
| mittlerer Lohn, hoher Lohn | `median`, `high` (`PERSONS`) | The other two model persons: the median wage of full-time employees living in Frankfurt, and a wage at the pension ceiling. |
| Beitragsbemessungsgrenze (Rentenversicherung) | `ceiling_rv` (`WageRules`) | The pension ceiling: the gross wage up to which contributions are due, set by law each year. The wage of the „hoher Lohn“. |
| Kosten der Unterkunft (KdU, SGB II) | `nebenkosten` (`read_nebenkosten`, `BA_KDU_XLSX`) | Statistic of the Bundesagentur für Arbeit on the housing costs of households in the Grundsicherung. The view „Miete“ takes the actual Betriebskosten and Heizkosten per m² of June. |
| Entgeltstatistik | `wages` (`read_median_wage`, `BA_WAGES_2017_XLSM`, `BA_WAGES_SERIES_XLSX`) | Statistic of the Bundesagentur für Arbeit on the gross monthly wage of full-time employees on 31.12. The view „Miete“ takes the median by Wohnort. |
| Belastungsklasse | `CLASSES` (`class_0` to `class_3`) | A class of warm rent ÷ household income in the view „Miete“: under 30 %, 30 to under 40 %, 40 to under 50 %, 50 % and more. |
| Baufertigstellung | `completion` | A building or dwelling counted in the year it is finished. |
| gefördert | `subsidised` | A dwelling in Förderweg 1 or 2: the rent is bound for a time. Says nothing about the owner. |
| Förderweg 1 / 2 | `funding path 1` / `2` (`fw1`, `fw2`) | Subsidy programmes of the city with their predecessor programmes (FW 1, FW 2). |
| Wohnheim | `residence` (dormitory) | Residential building for groups such as students. The HSL counts its dwellings as new dwellings. |
| Abdeckung | `coverage` | Share of the base that has a value. |
| Strich („–“ im Zensus; project term „Strich-Feld“) | `dash cell` (`vacancy_rate_dash`) | A 100 m cell where the Zensus shows „–“: exactly zero or changed to zero. `fill_rate` fills it from the 1 km grid (`housing`). |
| gemeinsamer Wert | `shared value` (`<ID>_SHARED`) | A Monitoring value that the source row holds for several districts. The map names them (`monitoring`). |
| angezeigter Wert | `shown value` (`shown`, `APP.shownOf`) | The value rounded half up to the decimals of the indicator. Colour, legend, candidates and histogram compare it. A rank is not rounded. |
| bereinigt | `capped` | Construction year: per cell the 2011 class counts at most the dwellings of 2022 (`construction_year`). |
| Erhaltungssatzung | `preservation statute` | Statute under § 172 BauGB. |
| Milieuschutz (§ 172 Abs. 1 Nr. 2 BauGB) | `social_preservation` | Protects the residents' composition. |
| Ortsbild (§ 172 Abs. 1 Nr. 1 BauGB) | `townscape` | Protects the townscape, not the residents. |
| Bodenrichtwert | `land_value` | Standard land value in €/m² (BORIS). |
| Gebäudemodell LoD2 | `LoD2` | 3D building model of the Hessian survey office (HVBG) with roof shapes, level of detail 2. |
| Gebäudeteil | `part` | One part of a building in the LoD2 model with its own roof type, function and height. |
| Gemarkung | `gemarkung` | Cadastral district; the LoD2 delivery comes per Gemarkung (59 in Frankfurt). |
| niedriges Flachdach | `low flat roof` | Flat roof of a part 2.5 m to under 8 m high; a building is a roof candidate from 200 m² of it (`flat_roofs`). |
| Abstandsfläche | `wall strip` (`wall_m2`, `WALL_GAP_M`) | Strip of 2.5 m in front of a wall more than 3 m higher than a low flat roof, within 1 m of it. It stays free, the rest of the roof counts. 2.5 m is the smallest Abstandsfläche of the Hessische Bauordnung, § 6 Abs. 5 Satz 4 (`flat_roofs`). |
| leichtes Wohnmodul | `light module` | Housing module for a roof. The estimate takes half the counted roof, 25 m² per module (`ROOF_FLAT`). |
| B-Plan im Verfahren | `pending_plan` | Development plan in procedure. |
| Flurstück | `parcel` | A parcel of the ALKIS cadastre. A building gap is always a whole parcel. |
| Flurstückskennzeichen | `kz` | Key of a parcel: Land, Gemarkung, Flur, Zähler, Nenner (`060499046003250030__`). The tooltip reads „Gemarkung 0499, Flur 46, Nr. 325/30“ (`kz_parts` in `sources.py` cuts the key, the text `kz` in `texts.de.yaml` writes it). |
| Hauptgebäude | `main building` | An ALKIS building of at least 30 m² whose function is not minor (`MAIN_MIN_M2`). |
| Nebengebäude | `minor building` | Garage, shed, Tiefgarage and the like (`MINOR_FUNCTIONS` in `building_gaps/sources.py`), or any building under 30 m². |
| Baulücke | `building gap` (`gap`, `Gap`) | A parcel almost without a main building (at most 5 % of its area or 20 m²) that passes the geometry rule of `building_gaps` (300 m², 15 m wide, front, neighbour wall or 30 m front). It counts only after a hand verdict `counts`. |
| Front | `front` (`front_m`) | Length of the parcel boundary within 1.5 m of a street, a way or a square, minus 2 × 1.5 m per connected piece. The tooltip says „<n> m an der Straße“. |
| zwischen Nachbarhäusern (Häuserzeile) | `row` | Kind of a gap: at least 5 m of its boundary lie within 0.3 m of a neighbour main building. |
| freistehend | `free` | Kind of a gap without a neighbour wall: its front is at least 30 m. |
| offen (weder bebaut noch grün) | `open` | Cover class of a pixel: lower than 2.5 m above ground and not green (NDVI under 0.2). Sealed or bare land. The ⓘ says „weder bebaut noch grün“. |
| Urteil | `verdict` (`counts`, `not`, `site`) | The hand verdict of a gap in `reference/building_gaps_reference.csv`. `site` means „Muss vor Ort geprüft werden“; it does not count. |
| Eignung | `suitability` (`SUITABILITY`) | What the area of a gap could carry, named by the largest real example it reaches (300 to 5,400 m²). |
| Mindestsicherung | `min_income` | Share of residents on minimum income support. |
| Arbeitslosendichte | `unemployment` | Unemployed per resident aged 15 to 64. |
| Benachteiligungsindex | `deprivation index` | Index of the monitoring; higher means more deprived. |
| Sozialwohnung | `social_housing` | Dwelling with rent and occupancy restriction. |
| Mietpreis- und Belegungsbindung | `restriction` | The restriction of a social dwelling. |
| Wahlberechtigte / Wähler / gültige Stimmen | `eligible` / `voters` / `valid_votes` | votemanager columns A, B, D. |
| Wahlbeteiligung | `turnout` | Voters per eligible voter. |
| Liste | `list` | A party or voter list. |
| Amtsblatt | `gazette` | Official gazette with the election result. |
| Jahresbericht | `annual report` | Annual report "Kommunale Wohnraumversorgung". |

## Ownership classes

| Zensus class | Old code | New code |
|---|---|---|
| Gemeinschaft von Wohnungseigentümer/-innen | `weg` | `condo` |
| Privatperson/-en | `pers` | `person` |
| Wohnungsgenossenschaft | `geno` | `coop` |
| Kommune oder kommunales Wohnungsunternehmen | `kom` | `municipal` |
| Privatwirtschaftliches Wohnungsunternehmen | `privwu` | `housing_company` |
| Anderes privatwirtschaftliches Unternehmen | `privand` | `other_company` |
| Bund oder Land | `land` | `state` |
| Organisation ohne Erwerbszweck (z.B. Kirche) | `org` | `nonprofit` |

Sectors of the view „Trend“ (`SECTORS`): „Privat“ = `private`, „Gemeinschaft“ = `community`.

## Dataset names

Directories, reference files, modules, constants, payload keys and catalog fields: the tables below.
The full lists of old and new names lay in tools/renames.json (architecture refactoring) and
tools/renames_use_cases.json (use cases), both deleted; the local archive of the
history before 16.11.2026 holds them (`git log --all -- tools/renames.json`).

Old findings use the old file names. The datasets live in `interim/` and are declared in
`pipeline/engine/datasets.py`.

| Old file | New dataset |
|---|---|
| `zellen_2022.csv` | `cells_2022.csv` |
| `zellen_2011_eigentum.csv` | `cells_2011_ownership.csv` (renamed `cells_2011_dwellings.csv`; it also holds the year of construction) |
| `eigentum_zellen.csv` | `ownership_cells.csv` |
| `eigentum_faktoren.csv` | `ownership_factors.csv` (removed; the step logs the factors) |
| `nh_zellen.csv` | `public_owner_cells.csv` (removed; successor `public_housing_quarters.csv`) |
| `lage_bezirke.csv` | `situation_districts.csv` (removed; successor `monitoring_by_district.csv` and `monitoring_by_quarter.csv`) |
| `lif_umfragebezirke.csv` | `lif_survey_areas.csv` (removed; successor `survey_by_district.csv`) |
| `brw_zellen.csv` | `land_value_cells.csv` |
| `boden_bezirk.csv` | `land_districts.csv` (removed; successor `land_by_district.csv`) |
| `boden_stadtteil.csv` | `land_quarters.csv` (removed; successor `land_by_quarter.csv`) |
| `milieu_zellen.csv` | `protection_cells.csv` |
| `schutz_bezirk.csv` | `protection_districts.csv` (removed; successor `protection_by_district.csv`) |
| `schutz_stadtteil.csv` | `protection_quarters.csv` (removed; successor `protection_by_quarter.csv`) |
| `milieu_nr2_aktuell.csv` | `social_preservation_current.csv` (removed) |
| `wahl_stadtteile.csv` | `election_quarters.csv` (removed; successor `election_by_quarter.csv`) |
| `wahl_listen.json` | `election_lists.json` |
| `sozialwohnungen_stadtteile.csv` | `social_housing_quarters.csv` (removed; successor `social_housing_by_quarter.csv`) |
| `sozialwohnungen_stadt.json` | `social_housing_city.json` (rows `indicator`, `value`, `kind`) |
| `kennzahlen_bezirke.csv` | `indicators_districts.csv` |
| `kennzahlen_stadtteile.csv` | `indicators_quarters.csv` |
| `manuell_meta.json` | `manual_layers.json` (removed with the manual layers) |
| `stadtwerte.csv` | `city_values.csv` |
| `kandidaten_referenz.csv` | `candidates_reference.csv` |
| `pruefbericht.md` | `check_report.md` |
| – (temporary) | `indicators_survey_areas.csv` (removed) |

The exports in `output/data/` were renamed too.

| Old export | New export |
|---|---|
| `kennzahlen_stadtbezirke.csv` | `indicators_districts.csv` |
| `kennzahlen_stadtteile.csv` | `indicators_quarters.csv` |
| `stadtbezirke.geojson` | `districts.geojson` |
| `stadtteile.geojson` | `quarters.geojson` |
| – (temporary) | `indicators_survey_areas.csv` (removed) |
| – (temporary) | `survey_areas.geojson` (removed) |

## Use cases

Each chapter of the map is one package in `pipeline/use_cases/`
(`docs/architecture.md`, Use-case packages). The map shows the German chapter names. The package has the files
`README.md`, `model.py`, `catalog.py`, `step.py`, `checks.py` only with checks, and `sources.py` only if it reads its
own sources.

| Chapter in the map | Package | Indicators |
|---|---|---|
| ABG und Nassauische Heimstätte | `public_housing` | `OWN_PUBLIC` (text and range; the share is computed in `ownership_shares`; the count is `OWN_PUBLIC_DWELLINGS` there) |
| Genossenschaften | `coops` | `OWN_COOP` (text and range; the share is computed in `ownership_shares`) |
| Private Unternehmen, Privatpersonen und WEG, Bund oder Land, Organisationen ohne Erwerbszweck | `ownership_shares` | `OWN_COOP` (share), `OWN_COMPANY`, `OWN_PERSON`, `OWN_STATE`, `OWN_NONPROFIT`, `COV_OWN`, `BLD_*`, `<group>_DWELLINGS` (counts per group, shown in the map tooltip) |
| Eigentum je 100-m-Feld | `ownership_cells` | none; the estimate per cell and the overlay |
| Ansicht Trend | `ownership_history` | none; four charts |
| Ansicht Neubau | `new_construction` | none; the columns of completions and the block of rents (two index charts) |
| Ansicht Miete | `rent_burden` | none; the wage example (wage bars of the latest year) and the tenants by income group (bars) |
| Mindestsicherung, Arbeitslosendichte, Benachteiligungsindex | `monitoring` | `SOC_MIN_INCOME`, `SOC_UNEMPLOYED`, `SOC_INDEX` |
| Sozialwohnungen | `social_housing` | `SH_SHARE`, `SH_COUNT` |
| Mieter, Miete, Leerstand | `housing` | `HOU_RENTERS`, `HOU_RENT`, `HOU_VACANT_MARKET`, `HOU_VACANT_ALL`, `COV_HOU_*` |
| Baujahr | `construction_year` | `HOU_PRE1919`, `HOU_1949_1978` and their `_DWELLINGS` |
| Umfrage 2025 | `survey` | `LIF_RENT_BURDEN_RATIO`, `LIF_ATTACHMENT`, `LIF_RENT_BURDEN_INCOME_*` (tooltip lines) |
| Bodenrichtwert, B-Plan im Verfahren | `land` | `LAND_VALUE`, `LAND_PENDING_PLAN` (topic Planung); overlays land value zones and pending plans |
| Niedrige Flachdächer | `flat_roofs` | `ROOF_FLAT` (topic Boden); overlay of the roofs |
| Baulücken | `building_gaps` | `GAP_AREA` (topic Boden); overlay of the drawn gaps |
| Abdeckung mit Milieuschutz | `protection` | `PROT_SOCIAL` (topic Planung); overlays Milieuschutz and Ortsbild |
| Wahl | `election` | `ELEC_*` |
| Kandidaten | `candidates` | none; three templates |

Tiers of `pipeline/`: `engine` (steps, store, datasets, downloads), `shared` (`zensus` for the grids and tables of the
Zensus, `geography` for districts and quarters, `core`, `readers`), `use_cases`, and `map` (`assembly` joins the area
tables and the city values, `checks` collects the check results, `html` packs payload and HTML).
`pipeline/update_sources.py` downloads, by hand; no step downloads.

| German | English | Meaning |
|---|---|---|
| Anwendungsfall | `use case` | One package per chapter of the map. |
| gemeinsamer Baustein | `shared block` | A package in `shared/` or `map/`; it holds no formula of an indicator. |
| Zusammenführung | `assembly` | Joins the area tables of the use cases into `indicators_districts` and `indicators_quarters`. |

New datasets. `<package>` is a use case.

| Dataset | Content |
|---|---|
| `<package>_by_district.csv`, `<package>_by_quarter.csv` | Area table of a use case: one row per area, key `id`, columns are indicator IDs. |
| `<package>_city.json` | City values of a use case: rows `indicator`, `value`, `kind` (`computed`, `published`). |
| `<package>_checks.json` | Check results of a step: rows `name`, `status`, `text`. |
| `coops_quarters.csv` | Coop dwellings per Stadtteil: `counted_2011`, `gap_2011`, `estimate_2022`, `coop_value`, `coop_half`. |
| `ownership_grid_cells.json`, `ownership_history_view.json` | Grid overlay rows; data and texts of Trend. |
| `new_construction.csv`, `new_construction_view.json` | One row per year (all, new_res, new_nonres, new, conversions, FW 1, FW 2, subsidised, share, provisional); data and texts of Neubau. |
| `new_construction_stock.csv` | One row per year (year, stock, population, completed, change, outflow); input of `new_construction_rents.csv`. |
| `new_construction_rents.csv` | One row per year from `RENT_FROM` (2017) to `RENT_TO` (2025), the last survey year: stock, population, the indices (`*_index`), the wages and rents without inflation (`*_real`) and the rents in €/m² of the survey years; the block of rents of Neubau. |
| `survey_respondents.csv` | Working data of `survey`: the respondents of both surveys with their classes and weights; `rent_burden` recomputes the burden from it. |
| `rent_burden_wage.csv` | One row per survey year, model person and contract: warm rent, gross and net wage, share, left, left without inflation; the wage example of Miete. |
| `rent_burden_groups.csv` | One row per income group: share of the adult tenants, median burden, the four burden classes, cases; the bars of Miete. |
| `rent_burden_view.json`, `rent_burden_checks.json` | Data and texts of Miete (payload key `rent_burden`); the checks of the view. |
| `land_overlays.json`, `protection_overlays.json`, `flat_roofs_overlays.json`, `building_gaps_overlays.json` | Shapes of the overlays. |
| `assembly_checks.json` | Population per district and Stadtteil and the ⓘ protocols. |

Kept as working data: `ownership_cells`, `public_housing_quarters`, `land_value_cells`,
`protection_cells`, `election_lists`, `survey_respondents` and the three history
tables. Removed: `situation_districts`, `lif_survey_areas`, `land_districts`, `land_quarters`,
`protection_districts`, `protection_quarters`, `election_quarters`, `social_housing_quarters` (the table above lists
their successors). The packages `indicators`, `situation` and `ownership` are removed too.

## Topics

The profile and „Stadt“ group the indicators by topic, not by source (`docs/texts.md`, Map: profile). The
heading is `group` in the catalog; the browser keys on `section`. Headings stay German.

| Heading | `section` | Indicators |
|---|---|---|
| Eigentum | `ownership` | `OWN_*` |
| Soziale Lage | `situation` | `SOC_MIN_INCOME`, `SOC_UNEMPLOYED`, `SOC_INDEX`, `LIF_ATTACHMENT` |
| Miete | `rent` | `HOU_RENTERS`, `HOU_RENT`, `LIF_RENT_BURDEN_RATIO`, `LIF_RENT_BURDEN_INCOME_*` |
| Wohnungsbestand | `stock` | `SH_SHARE`, `SH_COUNT`, `HOU_VACANT_*`, `HOU_PRE1919*`, `HOU_1949_1978*` |
| Boden | `land` | `LAND_VALUE`, `ROOF_FLAT`, `GAP_AREA` |
| Planung | `planning` | `PROT_SOCIAL`, `LAND_PENDING_PLAN`; in the profile the block of statutes and plans |
| Wahl (profile: Wahl 2026) | `election` | `ELEC_*` |

`survey_area` (field of the catalog) marks a value of the Umfragebezirk, not of the area: the five `LIF_*` entries.

## Indicator IDs

The prefix names the use case, not the topic (see Topics).

Removed IDs and their successors:

- `OWN_ABG`, `OWN_NH`, `ABG_DWELLINGS`, `NH_DWELLINGS`: one count of ABG and NH per quarter, `PUBLIC_DWELLINGS`
  (`pipeline/use_cases/public_housing/README.md`). The ends of a range carry `_LOW` and `_HIGH`.
- `PUBLIC_DWELLINGS`, `public_housing_by_quarter`: `<group>_DWELLINGS` with `_LOW` and `_HIGH` for the six groups in
  `ownership_shares_by_quarter` (`pipeline/use_cases/ownership_shares/README.md`).
- `OWN_DWELLINGS` (the ⓘ of the column „Wohnungen“): none. The count stands in the map tooltip; its ⓘ is the one of
  the layer.
- `HOU_PRE1949`: `HOU_PRE1919` and `HOU_1949_1978` (dwellings of the class in 2011 per dwellings of 2022) with their
  counts `HOU_PRE1919_DWELLINGS` and `HOU_1949_1978_DWELLINGS` (`pipeline/use_cases/construction_year/README.md`).

| Old | New | Old | New |
|---|---|---|---|
| `EW` | `POP` | `B_MIET` | `HOU_RENTERS` |
| `E_KOM` | `OWN_PUBLIC` | `B_MIETE` | `HOU_RENT` |
| `E_ABG` | `OWN_ABG` | `B_FLAECHE` | removed |
| `E_NH` | `OWN_NH` | `B_LEER` | `HOU_VACANT_MARKET` |
| `ABG_WHG` | `ABG_DWELLINGS` | `B_LEER_ALLG` | `HOU_VACANT_ALL` |
| `NH_WHG` | `NH_DWELLINGS` | `B_ALTBAU` | `HOU_PRE1949` |
| `E_GENO` | `OWN_COOP` | `ABD_<B ID>`, for example `ABD_B_MIET` | `COV_<HOU ID>`, for example `COV_HOU_RENTERS` |
| `E_PRIVU` | `OWN_COMPANY` | `D_BRW` | `LAND_VALUE` |
| `E_PERS` | `OWN_PERSON` | `D_BPLAN` | `LAND_PENDING_PLAN` |
| `E_LAND` | `OWN_STATE` | `S_MILIEU` | `PROT_SOCIAL` |
| `E_ORG` | `OWN_NONPROFIT` | `A`, `B`, `D` (votemanager) | `ELEC_ELIGIBLE`, `ELEC_VOTERS`, `ELEC_VALID_VOTES` |
| `E_ABD` | `COV_OWN` | `W_BETEIL` | `ELEC_TURNOUT` |
| `GEB_<CLASS>`, for example `GEB_PRIVWU` | `BLD_<CLASS>` with the new class name, for example `BLD_HOUSING_COMPANY` | `W_STAERKSTE` | `ELEC_STRONGEST` |
| `EW_MON` | `POP_MONITORING` | `W_<LIST>`, for example `W_CDU` | `ELEC_<LIST>`, for example `ELEC_CDU` |
| `HH` | `HOUSEHOLDS` | `W_SONSTIGE` | `ELEC_OTHER` |
| `EW15_65` | `POP_15_65` | `W_LISTE` (JS only) | `ELEC_LIST` |
| `L_MIND` | `SOC_MIN_INCOME` | `SW_N` | `SH_COUNT` |
| `L_ALO` | `SOC_UNEMPLOYED` | `SW_ANT` | `SH_SHARE` |
| `L_INDEX` | `SOC_INDEX` | `SW_BIND_N` | – (removed) |
| `L_RANG` | `SOC_RANK` (removed) | `SW_BIND_ANT` | – (removed) |
| `L_SOZW` (reference only) | `SH_SHARE_MONITORING` | `LIF_EINK2000` | `LIF_INCOME_UNDER_2000` (removed) |
| `<ID>_BERECHNET` | `<ID>_COMPUTED` | `LIF_BELAST` | `LIF_BURDEN` (removed) |
| `M_<NAME>` | `MAN_<NAME>` | `LIF_EURM2_NEU` | `LIF_RENT_RECENT` (removed) |
| `klein` | `small` | – (new) | `LIF_RENT_BURDEN_RATIO`, `LIF_ATTACHMENT` |

## Stays German

- Proper names: ABG, Nassauische Heimstätte (`nh`), BORIS, planAS, votemanager, Leben in Frankfurt (`lif`), Monitoring,
  Zensus (with its tables, for example 4000W), PARLIS, party names, names of districts, quarters and survey areas.
- Source files, their folders under `sources/`, source column names and labels (only in `*/sources.py` and
  `shared/zensus/tables.py`).
- Everything the team reads in the map, and the findings in `research/`.
