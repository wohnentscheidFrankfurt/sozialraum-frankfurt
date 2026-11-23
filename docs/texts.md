# Texts

Rules for every visible text of the map: catalog texts, tooltips, legend, profile, help, views and cover note.
The code and the tests are the truth. Where a rule is pinned by a test, the test is named.

## Where texts live

- A map text stands once in the repo, in the language file `texts.<lang>.yaml` (`texts.de.yaml`, `texts.en.yaml`)
  of its package: of its use case, of `pipeline/shared/core` (sentences that several use cases share), of
  `pipeline/map/assembly` or of `pipeline/map/html` (the page, the UI words and the cover note). No text stands in
  Python or in `web/`.
- A file holds nested maps. Each leaf is one text, quoted (a long multi-line text may be a block scalar). A key is its
  path (`OWN_COOP.title`, `ui.layers.details`). A list is a map with the keys `"1"`, `"2"`. The loader
  `pipeline/shared/core/texts.py` rejects a list.
- A text holds `{name}` placeholders. Code fills numbers and names that it computes (`Texts.fill`). A placeholder of the
  build (`{range_<ID>}`, `{fetch_date}`) stays until the build fills it.
- A text may refer to another with `{@key}` (same file) or `{@core.key}` (core file). Write a whole text in the file,
  joined by references. Python joins no sentences.
- `catalog.py` loads its texts (`T = package_texts(__file__)`) and builds each text constant per language:
  `X[lang]`. `LANGUAGES` in `pipeline/shared/core/texts.py` lists the languages of the map.
- Source vocabulary stays in Python (`sources.py`, codes, regexes, names of source columns). So do ids, colours, links
  and thresholds. Only what the reader sees goes into the file.
- The numbers inside a text come from `Texts.number`, `number_range`, `month` and `date`
  (`pipeline/shared/core/numbers.py`). Do not format numbers by hand.
- Each `texts.en.yaml` has a lock `texts.en.lock`: per key a hash of the German text it translates (references
  resolved). `tests/test_texts_pairs.py` fails on a stale key, on other keys, placeholders or numbers. After you
  update an English text, run `.venv/bin/python -I -m pipeline.lock_texts <folder>`.
- The pytest tests check the rules of this file, the numbers, the placeholders and where a text goes. They do not pin
  the wording. Why: a text can change without a second edit in a test.
- A test that needs a text takes it from its constant or from `Texts` (`TEXTS["key"]`). The key is the link to the file.
- A README names a map text by its key or by a short title. It quotes no sentence of a map text.
- `docs/` quotes a map text only as an example of a rule.
- The browser tests follow the same rule. They check rules, numbers, placeholders and structure, never the wording.
  A check that needs a text takes it from the page: the payload, the catalog or `APP`.
- `tests/test_text_copies.py` finds a test literal of 20 or more characters with a German word that stands in a map
  text. It reads the Python tests and the browser tests (`tests/browser/**/*.mjs` without `node_modules`). In a
  browser test it reads strings, the parts of template literals and regex literals. Its `ALLOWED` names each
  exception with its reason.

## Language

- The build writes the map in German and in British English (`LANGUAGES`). Every visible text, including the views,
  the help and the cover note, stands in both. The language files are named `texts.<lang>.yaml`.
- The British English texts stand in `texts.en.yaml` next to the German ones. Section English holds their rules.
- Everything else is English: code, comments, docs, the check report, commit messages, file names.
- German terms map to English names in `docs/glossary.md`. Proper names and source vocabulary stay German.
- The chat with the user is German.

## Map texts

### Reader and sentence style

- Write for a reader who sees the map for the first time and lacks our context.
- Write fluent German in full, simple sentences without nesting. Every sentence has a verb.
  Why: telegraphic text such as „Geschätzt. Spanne ±3,5 Prozentpunkte, als Klammer am Wert.“ is hard to read for a
  first-time reader.
- A colon is the exception. It stays after a label: the ⓘ labels, „Name: Wert“ in tooltips and the legend
  („Ganz Frankfurt: ~18,3 %“), the keywords of the help („Stadt:“). It also stays in a label list such as
  „Oranger Rand: alle Kriterien erfüllt.“
- Prefer a fluent sentence even where a colon is shorter. Example: „Die Zahl ihrer Häuser stieg nur halb so stark.“,
  not „Ihre Häuser: nur die Hälfte mehr.“
- A line builds on the text directly above it and does not repeat it. A lead does not restate its heading.
- „Z. B. …“ opens the example sentence of a Trend tooltip.

### Length

- „Der kürzeste Satz ist der kürzeste, der noch stimmt.“ Default to the shortest version that is still exact.
- Never drop the denominator, the year or „geschätzt“ to save words.
  Why: a generic phrase such as „Anteil an allen Wohnungen“ is wrong for many layers.
- Keep what identifies, drop what restates. A district number stays, a repeated context goes.
- Extra numbers and nice-to-know facts go into a tooltip or the ⓘ, not into a heading or a lead.
- A text explains what the reader sees and does right now: the view, layer, level or state they are in.
- Prefer explanation by the interface itself (label, legend note, tooltip at the value) over a general ⓘ.

### Coarse breakdowns

- Small gaps between numbers get no note on the surface.
  The rules: `docs/data-rules.md`, Rounding and coarse breakdowns.

### Terms

- One word for one thing. No word that a reader has to look up.
- Say „100-m-Feld“ (not „Zelle“), „Nassauische Heimstätte“ (not „NH“), „aus Datenschutzgründen“ (not
  „Geheimhaltung“) and „Die Karte hat die Schätzung mit den Zahlen von 2011 getestet.“ (not „Rücktest“).
- A dash in the Zensus is explained once, as `dash_meaning` in `pipeline/shared/core/texts.de.yaml`.
- Construction-year texts say „Wohnungen in Gebäuden mit Baujahr …“. Why: the map counts dwellings, the class
  belongs to the building.
- A share of votes says „Stimmen“, never „Wählende“. Why: every voter has several votes in the local election.
- Shared sentences of several catalogs stand once in `pipeline/shared/core/texts.de.yaml` (`quarters_rule`,
  `field_midpoint`, `field_sum`, `tip_dwellings_rule` and others).
- `test_no_info_uses_a_term_of_the_working_sessions` in `tests/map/assembly/test_catalog.py` bans the terms of the
  working sessions in every ⓘ of the catalog. Its `BANNED` lists „Rücktest“, „Lücke“, „Geheimhaltung“, „Maß:“,
  „Rechenweg“, „Zelle“, „Spanne“ and „Abgleich“. A separate regex in the same test bans „NH“ as a word.
  A table code such as „4000W“ stands only in the Quelle.
- The catalog tests of the views Neubau and Miete take the session fixture `banned` of `tests/conftest.py`
  (`BANNED_TERMS`): the same terms plus „NH“.

### Gender

- Map texts gender with the star in the plural: „Einwohner*innen“, „Bewohner*innen“, „Wohnungseigentümer*innen“.
- A singular with an article, a vowel change or a case ending gives way to a neutral form. Examples: „Wählende“,
  „Briefwählende“, „die öffentliche Hand“, „Eigentumsform“, „Die Wohnungen gehören Personen oder Firmen.“
  „je Einwohner*in“ is fine without an article.
- Readability wins. Use a star only where the neutral form says less or reads worse.
- Compounds („Eigentümerquote“, „Mieteranteil“), proper names and terms of the law or the sources stay.
- „Kandidaten“ stays. It names areas, not persons.
- `UNGENDERED` in `tests/map/assembly/test_catalog.py` checks every map text and every Python and language file of
  `pipeline/`. `tests/map/html/test_web.py` applies it to `web/`. The only allowed hit is the source column
  „Einwohner“ in `pipeline/shared/zensus/sources.py`.

### Owners are „Personen“

- Map texts call owners „Personen“, never „Menschen“. Examples: „einzelne Personen, Paare oder
  Erbengemeinschaften“, „Einzelne Personen und Gemeinschaften von Wohnungseigentümer*innen“.
  Why: „Personen“ is more neutral.
- Texts that do not speak of owners keep „Menschen“: „Die Karte beschreibt Gebiete, nicht Menschen.“

### Numbers

- An estimated value starts with „~“ without a space: „~17,8 %“, „~3.120“. The catalog field `estimate` sets it.
- Which values are estimates stands in `docs/data-rules.md`, Counted or estimated.
- The tilde stands at every place that shows such a value: tooltip, profile, city value, count line, worked example.
- No tilde in legend classes, the CSV, candidate thresholds, histograms, „unter 10“, „unter 200“, „unsicher“ or
  „k. A.“. Printed survey classes („26–28 %“) are classes, not estimates, and carry none.
- No range at a value. The Unsicherheit of the ⓘ says how far an estimate can be off.
- German number format: „1.754“, „6,6 %“, a space before „%“. A number and its „%“ stay on one line
  (`APP.keepUnits`).
- Dates read „15.3.2026“, without leading zeros. A date that several texts name stands once as a constant of its
  use case (`SH_AS_OF`, `BORIS_AS_OF`, `ELECTION_DAY`).
- An exact count in a text is preferred over a rounded ratio: „In 40 von 45 Stadtteilen“, not „9 von 10“.

### Area names

- On the level Bezirke every name carries its number: „Bockenheim (Bezirk 343)“ in the tooltip.
  Why: 13 names stand for 55 districts. A name alone does not identify a district.
- The candidates list adds the Stadtteil when the name lacks it: „Osthafen (Bezirk 70, Ostend)“.
- The profile title stays the name. The line below reads „Bezirk 343 · 2.530 Einwohner*innen (Zensus 2022)“.
- Stadtteile carry no number. `APP.areaLabel` in `web/js/01_base.js` builds every label.

### Neutrality

- The map states facts. It may draw the conclusion that the shown numbers carry.
  Why: „Politik ist nie neutral.“ A heading may say what the numbers show. Example: the rents of new contracts grew
  faster than the dwellings.
- An own conclusion or estimate follows the rule in `docs/data-rules.md` (Allowed sources): well founded, traceable
  and simple.
- The map demands nothing. No campaign wording, no target line, no comparison with a goal.
- A conclusion in a heading or a lead holds only as far as a check of the build keeps it true.
- The header says „Sozialraum Frankfurt“ (`tests/test_architecture.py`, `test_web_names_the_map`).
- „Die Karte beschreibt Gebiete, nicht Menschen.“ stands in the election legend, below the block Wahl of the
  profile, in the help and in the cover note.
- The ⓘ holds no evaluation („eher“) and no demand (ⓘ protocol, Lines).

## ⓘ protocol

### Lines

- Every ⓘ is a result protocol with fixed lines in a fixed order: Quelle, Stand, Rechnung, Regel, Unsicherheit.
- The ⓘ clarifies where the value comes from and how it arises. Quelle names who publishes the numbers and in which
  document (report, table, data set, Drucksache), so a reader can find them. Stand names the date the numbers describe.
- Everything else explains the value with facts, formulas and the meaning of terms, and says how far it can be off. The
  ⓘ holds no evaluation („eher“) and no demand. `NOT_A_FACT` in `tests/map/assembly/test_catalog.py` guards against
  evaluations.
- The label stands above its value, at every width. The browser renders the protocol as a `<dl>`.
- An indicator needs Quelle, Stand and Rechnung. Regel and Unsicherheit appear only when needed.
- An overlay needs Quelle, Stand and Regel. Only the grid overlay has a Rechnung.
- Quelle and Stand are lists. Parts split at „ · “ and stand one per line. Regel never splits.
- The Stand of a WFS layer reads „Abruf <date>“ (`{fetch_date}`).
- A Rechnung may start with a formula with ÷, × or −: „Wählende ÷ Wahlberechtigte. Briefwählende zählen mit.“
- Everything else is a full sentence. Regel and Unsicherheit start with a capital and end with a full stop
  (`test_rules_and_uncertainties_are_full_sentences`).
- Regel says when no value shows or what does not count: „Den Wert gibt es nur für Stadtteile.“
- Unsicherheit names in one or two sentences how far an estimate or a sample can be off, without the derivation.
- No line Abgleich. The checks of the build cover every comparison with a published value.
  Why: a reader without our context cannot use a comparison.
- The ⓘ of a share also explains its count in the tooltip. A count has no rule of its own. Example: „Im Tooltip
  rundet die Karte die Wohnungen auf 10. Unter 10 Wohnungen steht dort „unter 10“.“ (`tooltip_rounding`).
- Every ownership layer ends its Regel and Unsicherheit with `tip_dwellings_rule` and
  `tip_dwellings_uncertainty` (core texts).

### Written sums

- Default: an ⓘ shows its Rechnung as a written sum where that is sensibly possible, else as prose. The prose then
  keeps only what no sum shows.
- Some indicators show a worked example as their whole Rechnung: the six ownership groups, both vacancy shares,
  `HOU_RENTERS`, both construction-year shares and `SH_SHARE`. Their `calc` stays empty.
- The label reads „Rechnung am Beispiel <Stadtteil>“. Each indicator has one fixed Stadtteil, chosen for a high share.
  ABG and NH use Niederrad, 5th of 45: its fills are large, so the reader sees why the sum needs them.
- Each row has an operator (+, −, ×, ÷ or none), a rounded number and what the number is: „÷ 4.282 alle Wohnungen“.
- A total row stands under a line. The last row is the map value with „Wert auf der Karte“, large and without a box.
- Rows are whole numbers. Factors have one decimal (per type) or two (adjustment). Totals are build values, so the
  rows may not add up to the last digit. No note says so.
- A row whose rounded number is 0 is left out. An estimated number carries „~“, the last row exactly as the map.
- No note under the sum and no sentence „Im Tooltip steht …“. What the sum leaves out stands in the README of the
  use case.
- Exception: an indicator may keep its prose Rechnung and add a sum. The ⓘ then shows both entries, the prose first.
  The last row may then be an example value instead of the map value, whole percent and without „~“. Rows may carry
  the unit „€“. Example: `LIF_RENT_BURDEN_RATIO`, „Rechnung am Beispiel einer alleinlebenden Person“
  (`survey_calc_example` in `pipeline/use_cases/survey/catalog.py`). The prose does not repeat what the sum shows.
- Exception: an ⓘ may carry a sum for the whole city with its own label („Rechnung für ganz Frankfurt“). It ends in a
  model value with „~“, rounded to hundreds („~14.700 leichte Wohnmodule haben Platz“). The rows before it carry
  „m²“ in their text. Example: `ROOF_FLAT`. `GAP_AREA` has such a sum in parcels. It ends in two counted totals
  without „~“: „Baulücken zählen“ and „m² zählen“. A step that drops no parcel is left out.
- The ⓘ of the views Neubau and Miete show their Rechnung as written sums too, after a short prose (sections Neubau
  and Miete). An ⓘ with two sums gives each its own label (`label` of `CalcExample`). The last row of a sum there is
  the value of the chart for the example, with „~“ where it is a model value.
- The map indicators of rent, land value, rank, survey, monitoring, protection and election keep a prose Rechnung.
  Why: a weighted mean or a median has no readable sum. One voter casts many votes, so a sum of votes would mislead.
- `pipeline/shared/core/calc_example.py` defines the rows. `APP.calcExampleHtml` in `web/js/01_base.js` renders them.

### Catalog fields and placeholders

- Each use case writes its texts in its own `texts.<lang>.yaml`; its `catalog.py` builds them: title, unit, legend
  note, Quelle, Stand, Rechnung, Regel, Unsicherheit, and the texts of its view or templates.
- `pipeline/map/assembly/catalog.py` holds only the order of the layers and of the sources.
- A catalog text may hold `{fetch_date}`, `{range_<ID>}` and `{high_<ID>}`. `fill` puts in the numbers of the build.
  The rent burden also holds `{city_<ID>}` (city value of a breakdown line, `breakdown_numbers` in
  `pipeline/map/assembly/catalog.py`) and `{typical_LIF_RENT_BURDEN_INCOME_LOW}`, `{max_LIF_RENT_BURDEN_INCOME_LOW}`,
  `{max_LIF_RENT_BURDEN_INCOME_UPPER}` (`survey_half_widths`).
  A leftover placeholder fails the check.
- Names and texts come from the payload, never from lists in `web/js`. Fixed words of the page (help, tabs) are
  markers `{{key}}` in `web/map.html` that name a text under `html` in `pipeline/map/html/texts.<lang>.yaml`. The words
  that the browser sets (buttons, labels, messages) are texts under `ui`. The page reads them with
  `APP.t(key, values)` from the payload key `ui`.
- A phrase that a check guards stands once in the language file (`phrases.*`). The texts refer to it with
  `{@phrases.x}`. The check takes the phrase as an argument.
- The `link` of a chart (docs/design.md, Direct links) names the question the chart answers, not its number or its
  finding: headings change with the data, a link must not. ASCII only (`ae`, `oe`, `ue`, `ss`), words joined by `-`.
  A link claims no more than the chart shows: `wachstum-im-bestand`, not `kaufen-statt-bauen`.

## Texts per view

- Each view explains only itself. A map text never names the view Trend. A Trend text never names „Karte“ or
  „Schicht“. `test_a_text_explains_only_the_view_it_is_in` checks both.
  Why: the user: „Wenn ich in der Karte bin, will ich Infos zur Karte. Wenn ich in Trend bin, Infos zu Trend.“
- A difference between the views is explained only in the view whose behaviour it explains. Example: the Trend
  tooltip of „Öffentlich“ says why it joins Kommune, Bund and Land; the map ⓘ says nothing about Trend.

### Map: legend

- Every layer has a `legend_note` under the legend title. It says what the number is: numerator, base and year.
  Examples: „Anteil der Wohnungen, 2022, geschätzt“, „Bezogen auf die gültigen Stimmen, 15.3.2026“.
- `tests/map/assembly/test_catalog.py` checks that the note of each layer, except a rank, names the year of its Stand.
- `OWN_COMPANY` and `OWN_PERSON` add a second line (`legend_detail`) with examples.
- Titles carry no as-of year. The legend note and the profile heading name it.
- The city value reads „Ganz Frankfurt: <value>“.
- A layer for one level only ends its row with „(nur Stadtteile)“ or „(nur Bezirke)“.
- A silent layer switch shows one sentence: „Private Unternehmen gibt es nur je Stadtteil.“
- Below the minimum zoom of an overlay, the key shows its note: grid „Für die 100-m-Felder näher heranzoomen.“,
  flat roofs „Für die Flachdächer näher heranzoomen.“ (texts `ui.overlays` in `pipeline/map/html/texts.de.yaml`).
- The candidates legend is „Kriterien erfüllt“ and has no note.

### Map: tooltip

- The value line reads „<Titel>: <Wert>“. An election layer adds „(Stadtverordnetenwahl)“ to the title.
- A rank reads „Rang 46 von 114“, a tie „Rang 23 bis 24 von 114“.
- A shared Monitoring value adds „(gemeinsamer Wert der Bezirke …)“. A survey value adds „im Umfragebezirk …“.
- A layer with breakdown lines ends its tooltip with the line `breakdown_lead` („Nach Haushaltsnettoeinkommen:“) and one
  line „<Titel>: <Wert>“ per value with `breakdown_of` set to the layer (`APP.breakdownLines`). A value without data
  reads „k. A.“.
- A count stands in its own line under the value line: „Wohnungen: 1.754“, „Leer stehende Wohnungen: ~120“,
  „Wählende: 1.343 von 2.871“. The catalog field `count_of` links it to its share (`APP.countLine`).
- An ownership layer adds „Wohnungen: ~1.250“, „unter 200“, „unsicher“ or „k. A.“ (`APP.dwellingsText`).
- Below 90 % coverage it adds „Nur N % der Wohnungen sind einer Eigentumsform zugeordnet.“
- The grid tooltip reads „Die meisten Wohnungen gehören <Dativ> (geschätzt).“ (`GROUP_DATIVE`).
- Overlay tooltips show no plan codes.
- A flat roof reads „Flachdach: <area> m², <height> m hoch (<use>).“ (prefix `tip` of the overlay, then the `text` of
  the feature). A roof that does not count ends with „Zählt nicht: <reason>“. A counted roof with a wall strip of at
  least 1 m² ends with „Vor einer höheren Wand bleiben <strip> m² frei.“ The height is rounded down to 0.1 m.
  Why: a shown height never contradicts a threshold („3,1 m“ for 3,17 m is under 3,2 m).
- A building gap reads „Baulücke: Gemarkung 0499, Flur 46, Nr. 325/30. 796 m², 31 m an der Straße, freistehend.“
  (prefix `tip`, then the parcel, area, front and kind; „zwischen Nachbarhäusern“ or „freistehend“). Area and front
  are rounded down. A counted gap goes on „Zählt: Parkplatz, geprüft im Luftbild vom 19.8.2025.“ (or „geprüft vor
  Ort am <date>.“ after a visit). Why: the first-time reader sees at once that it counts. A gap to check on site goes
  on „Muss vor Ort geprüft werden.“, without a prefix and without „Zählt nicht:“. Why: who wants to know goes there.
  Both end with the suitability line „Platz zum Beispiel für …“: the largest example the area reaches, with place,
  number and plot area of the example. A gap judged `not` or not judged yet is not drawn.
- A land value zone reads „Bodenrichtwert 1.1.2026: 1.600 €/m² (Wohngebiet, Mehrfamilienhäuser)“: area, then the
  building type of BORIS where the zone has one (`use_name`). Zones on top of each other give one row each. Why: in
  mixed areas BORIS lays a zone for houses over one for blocks of flats; the same label for both would confuse.
- A candidates tooltip reads „4 von 5 Kriterien erfüllt. Es fehlt …“ or „Alle 5 Kriterien erfüllt.“

### Map: profile

- The profile is the tab „Gebiet“.
- Under the head, above the topic blocks, stands the details line. Its heading is the overlay heading of „Stadt“
  („Details“). The short names of the overlays that are on follow, joined by „, “. With none on, only the heading
  shows. A short name is the title without a final look in brackets: „Milieuschutz“, not „Milieuschutz
  (schraffiert)“. `APP.overlayNames` derives it, so no text stands twice. An overlay below its minimum zoom counts.
- One value per row, the share. No count. Counts stand in the tooltip.
- Exception: the breakdown of a layer shows under its row. The lead line is the `breakdown_lead` of the layer plus „:“.
  Each entry has its title, its value with the tilde and „Stadt ~X %“. A missing value reads „k. A.“.
- The blocks follow the topics, not the sources. Each row names its source in its ⓘ. The headings are single nouns:
  „Eigentum“, „Soziale Lage“, „Miete“, „Wohnungsbestand“, „Boden“, „Planung“, „Wahl 2026“. „Stadt“ shows the same
  headings in the same order (`group` and `section` of the catalog, `LAYER_ORDER`; `docs/glossary.md`, Topics). Two
  exceptions: „Planung“ has no layer, so „Stadt“ lacks it, and „Wahl“ stands there without the year.
- „Würden ihr Wohnviertel vermissen“ stands in „Soziale Lage“. Why: beside the rent it would read as pressure to move.
- „Boden“ and „Planung“ stay apart. Why: the Bodenrichtwert is a price, not a rule.
- In a block the rows of the area come first. Then the rows of the Umfragebezirk (`survey_area`, only on a Bezirk),
  then the rows of the Stadtteil. Each group follows one note: „Der Wert darunter gilt für den Umfragebezirk X.“ for
  one value, „Die Werte darunter gelten für den Umfragebezirk X.“ for more. A row with breakdown bars counts as more.
  The Stadtteil note follows the same rule („Der Wert darunter gilt für den Stadtteil X.“).
- A Stadtteil has no survey values. Its „Miete“ block shows Mieteranteil and Miete im Bestand only.
- Each group heading names its dates once. „Miete“ on a Bezirk reads „15.5.2022, Mai–August 2025, April–August
  2024“. The ownership heading names only the Stand of 2022. „Planung“ names no date.
- A row without its own layer carries its own ⓘ.
- Without any statute the block „Planung“ says „Hier gilt kein Milieuschutz.“

### Map: candidates

- Each template has a `lead` in `pipeline/use_cases/candidates/texts.de.yaml`.
- A criterion on the upper end of an estimate is labelled „(Schätzung plus Unsicherheit)“. While it checks „unter“,
  it carries `UPPER_END_NOTE`.
- The own query carries `CUSTOM_NOTE`.
- The count line names the full hits and the areas that miss one criterion.
- The list headings are „Alle Kriterien erfüllt (n)“ and „Ein Kriterium fehlt (n)“. The second names the missing
  criterion, or „k. A. bei <Titel>“.
- The tab note explains the black line, the dashed line, the colour and the histogram once.

### Help and cover note

- The help explains only what the map does not say itself. Keywords end with a colon. „Handy: …“ shows on phones only.
- The caveats of the help and of the cover note say the same.
- The cover note (key `cover_note` in `pipeline/map/html/texts.<lang>.yaml`) exists in both languages.
  It must not contain „--“.
  Its list of data years follows new data.

### Trend

- Headings have at most 61 characters. Each is one finding as a full sentence with a verb.
- A lead is one or two short sentences. It adds what the heading does not say.
- Every statement of a heading or a lead is backed by a check of the build.
- No intro line. One source line stands once below the charts (`HISTORY_SOURCE`).
- The view says „Häuser“. Only the source line says „Gebäude mit Wohnraum“.
- Descriptions and examples of the groups stand only in the tooltips.
- An example names only a firm that a stored source places in its Zensus class. Tooltips print no numbers of examples.
- Texts live in `pipeline/use_cases/ownership_history/texts.de.yaml`.

### Neubau

- Two figures below each other: the columns and the block of rents. Each has a heading, a lead, a ⓘ at the end of the
  lead and a source line. The block of rents holds two charts between its lead and its source line.
- Columns: a heading with one finding and a lead with the range of all dwellings. The source line reads
  „Quelle: …“. The ⓘ (key `new-construction`) gives the terms as prose, then two written sums of the last year: „Säule
  am Beispiel <year>“ (new construction in residential and non-residential buildings, conversions) and „Anteil am
  Beispiel <year>“ (Förderweg 1 and 2 ÷ new construction; „vorläufig“ where the year is). No sum for the lead.
- Block of rents: the heading (`RENTS_TEXTS["title"]`) says that from 2017 the dwellings grew faster than the
  population and the rents of new contracts faster still. The lead says that the rents of older contracts rose less
  than prices and wages. The heading draws the conclusion that the numbers carry (Neutrality).
- Two checks back them. „rents heading“: from 2017 the dwellings grew faster than the population, and the rents of new
  contracts grew faster than the dwellings in Euro, by more than the sampling error, published and chained. Without
  inflation the heading claims nothing: there the gap to the chained growth of the dwellings lies within the sampling
  error (`docs/data-rules.md`, Uncertainty). „rents lead older contracts“: the rents of older contracts rose less than
  prices and wages, and fell without inflation.
- The lead says nothing about households. The ⓘ names the size of households of all years as a range, guarded by
  the check „rents households“ (`docs/data-rules.md`).
- The heading names 2017, because the statement holds from there (index base, `RENT_FROM`). A new base year needs
  a new heading.
- Each chart has a title (bold) and one line below it (`RENTS_TEXTS["charts"]`). Chart 1 shows the rents in Euro; its
  line explains the grey band and the dots. Chart 2 shows the rents without inflation; its line says what a line under
  100 means.
- Under chart 1 stands one note in the wide drawing (on phones the key holds the same entry): the hollow dots show
  2022 on the old base. The year and the base come from `STOCK_BREAKS` and `OLD_BASE` (`RENTS_TEXTS["old_base_note"]`).
- Keys and end labels use the plain words of the source: „Miete neuer Verträge“, „Miete älterer Verträge“, „Preise“,
  „Löhne in Hessen“ (the wages are those of all of Hessen, so the name says so). The end labels at the last year
  read „neue Verträge“, „ältere Verträge“, „Preise“, „Löhne in Hessen“. In the wide drawing the key is hidden, so the
  end label of the wages says „in Hessen“ itself; on phones the key does.
- The chart says „Einwohner*innen“ (key, end label, tooltips).
- The ⓘ (key `housing-rents`) closes the lead line and explains both charts. Quelle: every report with its table or
  press table (stock, population, VPI, wages, Mietspiegel files, Melderegister). Stand: the day of each series, derived
  from `RENT_TO`. Rechnung: the day each series counts on and the mean of the Mietspiegel as prose, then the written
  sum „Rechnung am Beispiel neuer Verträge <RENT_TO>“: rent ÷ rent of `RENT_FROM` × 100, ÷ prices × 100. Regel: the
  two groups of the Mietspiegel, that subsidised dwellings with a bound rent are not in it, who counts as Einwohner*in,
  the month of the prices between the surveys, the wages and the range of persons per household. Unsicherheit: six
  instead of four years, no adjustment for new and modernised dwellings, contracts without an increase, the wages of
  Hessen, the base effects of the Zensus 2022 („25.679“, „4.378“), the growth in both calculations (chained 7,8 % and
  5,3 %, published 6,6 % and 1,8 %) and the outflow caveat of the HSL. The check „rents uncertainty“ backs the base
  effects and the four growths. The check „stock outflow of the last year“ requires the caveat sentence while the
  outflow of the last year is below a third of the mean of the other years.
- The last two sentences of the Unsicherheit say what the numbers do not show: how many people look for a fitting
  dwelling, and how high the rents would be without the new dwellings. The population is no measure of demand: it
  counts the residents, whether their dwelling fits or not, and not the people who would like to move to the city.
  The map names no cause and gives no number for the demand.
- The tooltip of a year has a head with the year and the index base, one row per series (value, then its label) and a
  note. The rent rows exist only in a survey year. The new contracts name their euro value and the survey day, the
  older contracts their euro value. The note says whether the year has a survey of the Mietspiegel. The check „rents
  survey dates“ keeps the dates true.
- The source line of the block names its sources itself („Quellen:“), so it has no „Quelle:“ in front.
- Every statement of a heading and a lead is backed by a check. Texts live in
  `pipeline/use_cases/new_construction/texts.de.yaml` (`TEXTS`, `RENTS_TEXTS` of `catalog.py` build them).

### Miete

- Two figures below each other: the wage example and the tenants by income group. Each has a heading, a lead, a ⓘ at
  the end of the lead and a source line.
- The source lines name their sources themselves. The line of the wage example starts with „Rechenbeispiel.“
  (`docs/data-rules.md`, Counted or estimated), the line of the bars with „Quelle:“.
- Wage example: it shows the latest survey year only. The heading (`WAGE_TEXTS["title"]`) says that at the
  Mindestlohn the same flat takes about three times the share it takes at the high wage. The check „rent wage
  heading“ backs it in both contracts.
- The lead (`WAGE_TEXTS["lead"]`) names what is left after the warm rent at the Mindestlohn and at the high wage, new
  contract. The build fills both euros from the table; they are data, not a statement, so no check backs them.
- The ⓘ (key `rent-wage`) names every input in Quelle and the day of each input in Stand. Rechnung: the tax case as
  prose, then two written sums at the Mindestlohn, new contract: „Nettolohn am Beispiel Mindestlohn“ and „Rechnung am
  Beispiel Mindestlohn, neuer Vertrag“ (warm rent and share). Regel: what the mittlerer and the hoher Lohn are, with the
  share of employees above the pension ceiling (check „rent wage ceiling“). Unsicherheit: the Nebenkosten of households
  in the Grundsicherung and the gap with those of the Mietspiegel (check „rent wage sensitivity“), and the measured
  median of all tenants (check „rent wage measured“). No sentence on the window of the Mietspiegel (spec of the wage
  bars): the figure shows one year, and the window lowers its level by an amount nobody knows (use case README,
  Limits).
- The switch names the contracts („Neuer Vertrag“, „Älterer Vertrag“). The explain line stands below it and says what
  a bar and its red part are. The tooltip of a row names contract, person, warm rent, net wage, share and what is
  left.
- Bars: the heading (`LOW_INCOME_TEXTS["title"]`) says that the warm rent of the lowest income group is about half
  of its income. The check „low income heading“ backs it at every position of the income in its class.
- The lead (`LOW_INCOME_TEXTS["lead"]`) names the share of the lowest group (check „low income share“) and the median
  of the highest group (check „low income lead“).
- The ⓘ (key `rent-low-income`) names the own evaluation of the microdata in Quelle. Rechnung: the prose on heating and
  class midpoints, then the written sum of the map indicator `LIF_RENT_BURDEN_RATIO`. Regel: the shares count adult
  tenants, not households. Unsicherheit: the range of the median by the position of the income in its class, the
  households whose rent the Jobcenter pays, and the Mikrozensus 2018 as the last published breakdown. The build fills
  the numbers of the Unsicherheit.
- Group and class names come from `INCOME_LIMITS` and `CLASSES`. The label of a bar names the median in whole
  percent (`docs/data-rules.md`, Rounding and coarse breakdowns).
- The view has no line in the help. The cover note names its years.
- Every statement of a heading and a lead is backed by a check; a number the build fills from the data needs none.
  Every number of an ⓘ is backed by a check or filled by the build. Texts live in
  `pipeline/use_cases/rent_burden/texts.de.yaml` (`WAGE_TEXTS`, `LOW_INCOME_TEXTS` of `catalog.py` build them).

## English

The English map is for people in Frankfurt who speak little or no German. Its texts translate the German ones.
The rules of Map texts and of the ⓘ protocol hold for them too.

### Reader and style

- The readers come from many countries. For many of them English is a second language too. They know little of
  German housing law or of the areas of the city.
- Plain English: short, plain sentences, one statement each. Common words, no idioms, no rare phrasal verbs
  („zoom in“ is fine), no German word order („the City tab“, not „the tab City“).
  Why: a reader who learned English as a second language misreads „be off by“, „bound“ or „removals“.
- `UNCLEAR_EN` in `tests/map/assembly/test_catalog.py` bans such words. Where one word replaces another, the table
  of Terms names it.
- The help and the hints of the interface say what the reader does: „Click a value to see it on the map.“
- An English text says exactly what its German text says: the same statement, the same numbers, the same hedges
  („estimated“, the year, the denominator). It adds no explanation and drops none.
  One exception: a German term that a newcomer would misread or would not know gets a short explanation once in the ⓘ of
  the layer. Examples: „Sozialwohnung“ (below), „Bodenrichtwert“, „Ortsbildsatzung“, „Liste“, ABG and
  Nassauische Heimstätte („public housing companies“), and the levels in the help („Districts (Stadtteile)“).
  Why: numbers flow into political demands (`docs/data-rules.md`, Demands).
- British spelling with -ise: „organise“, „colour“, „centre“, „neighbourhood“, „programme“.
- Numbers: „1,754“, „6.6%“ without a space, „€1,200“, „~17.8%“. Dates: „15 March 2026“; a year alone stays a year.
  The build formats the numbers of placeholders. A number typed in a text follows the same format.
- Quotation marks are “…”, the apostrophe is ’.
- A label starts with a capital, the same word inside a sentence does not: the row „Buildings“, the tooltip
  „1,234 buildings“. Where German uses one noun for both, English needs two texts (`ui.levels.choice`,
  `ui.history.houses.bar_tip`).

### German terms in English texts

- The German term stands in brackets once per text, where the reader meets it in daily life: in letters, at the
  offices, in the news. Example: „rent index (Mietspiegel)“. A button or a legend entry carries no bracket. A profile
  row may carry it: its terms are those the reader meets in letters and in the news.
  An overlay title carries none either. The title ends in the look of the overlay („Social preservation (hatched)“),
  and the browser strips that final bracket for the short name (`APP.overlayNames`). A German term in a final
  bracket would be lost there. The term stands in the ⓘ of the overlay.
- Names of German benefits and laws stay German, as proper names. The first time, a short English gloss follows in
  brackets: „Asylbewerberleistungen (benefits for asylum seekers)“. This is the reverse of the term rule.
- „Sozialwohnung“ is not British council housing. The text says what it is: a dwelling with a capped rent. Only
  households below an income limit may rent it. Both rules apply for a fixed number of years. The text says nothing
  about the owner.
- Owners are „people“, never „humans“ (German „Personen“, never „Menschen“). Where the source counts households, the
  text says „households“.
- Neutral words replace the gender star: „residents“, „tenants“, „owners“, „voters“.
- Proper names stay German: Stadtteile, Bezirke, streets, parties, lists, ABG, Nassauische Heimstätte, Zensus
  („Zensus (census)“ once in the help), and the titles of sources, tables and laws.
  The header stays „Sozialraum Frankfurt“ (`test_english_header` in `tests/test_architecture.py`).

### Terms

One English word for one thing. The German term in the second column is the one the brackets give. A later text may
add a term here; it keeps the terms that stand.

| English | German | Note |
|---|---|---|
| district | Stadtteil | One of the 45 areas; the level „Districts“. English texts about Frankfurt (Wikipedia, guides for newcomers) say „district“ for it. Never „quarter“. Code and map links keep the id `quarter`. |
| sub-district | Bezirk | One of the 114 areas of the social monitoring; „Sub-district 343“ in a tooltip. Code and map links keep the id `district`. |
| statistical sub-district | Stadtbezirk | One of the 123 of the statistics office. |
| borough | Ortsbezirk | One of 16. Its council is the local council (Ortsbeirat). Never „local district“: it is larger than a district. |
| local council | Ortsbeirat | |
| survey area | Umfragebezirk | |
| area | Gebiet | A district or a sub-district; the tab „Area“. |
| all of Frankfurt, City | ganz Frankfurt, Stadt | „All of Frankfurt: ~18.3%“ in the legend, „City ~18.3%“ in the profile. |
| 100 m grid square | 100-m-Feld | Never „cell“. |
| centre | Mittelpunkt | Of a grid square, a zone or a parcel. „midpoint“ only for the middle of a bracket. |
| level | Ebene | |
| indicator | Kennzahl | |
| layer | Schicht | |
| Details | Details | The overlays. |
| Source, As of, Calculation, Rule, Uncertainty | Quelle, Stand, Rechnung, Regel, Unsicherheit | The lines of the ⓘ. |
| example calculation for … | Rechnung am Beispiel … | |
| estimated, estimate | geschätzt, Schätzung | |
| differ by | abweichen um | Never „be off by“. „is as uncertain as the share“ for the counts in the tooltip. |
| upper end of the estimate | obere Grenze der Schätzung | Never „range“. |
| tested the estimate against the numbers from 2011 | Rücktest | Never „backtest“ (`test_2011`). |
| for data protection reasons | aus Datenschutzgründen | Never „secrecy“. |
| n/a | k. A. | |
| percentage points | Prozentpunkte | |
| dwelling | Wohnung | The unit the Zensus counts: a flat or a house. Not „flat“, not „home“. |
| building | Gebäude, Haus | Also where German says „Häuser“: a Haus of the Zensus can be a block of flats. |
| buildings with living space | Gebäude mit Wohnraum | The source line of Trend. |
| housing stock | Wohnungsbestand | |
| residents | Einwohner*innen, Bewohner*innen | |
| tenants | Mieter*innen | |
| rent index | Mietspiegel | |
| warm rent | Warmmiete | Rent with service charges and heating. „warm rent (Warmmiete)“ once. |
| net cold rent | Nettokaltmiete | Rent without service charges and heating. |
| cold rent | Kaltmiete | The rent bracket of the survey. |
| rent burden | Mietbelastung | Warm rent as a share of household net income; „rent burden rate“ for the Quote. |
| market-active vacancy | marktaktiver Leerstand | Vacant dwellings available within three months. |
| service charges | Nebenkosten, Betriebskosten | „service charges (Nebenkosten)“ once. |
| income bracket | Einkommensstufe, Klasse der Umfrage | Never „in brackets“: in British English that also means „in parentheses“. |
| rents of new contracts, of older contracts | Miete neuer Verträge, älterer Verträge | |
| vacant dwellings | leer stehende Wohnungen | |
| year of construction | Baujahr | „built before 1919“ in a tooltip. |
| new housing, in new buildings | Neubau | The view „New housing“, the key „In new buildings“, in prose „dwellings in new buildings“. The link stays `#neubau`. Never „new build“. |
| conversion of existing buildings | Umbau bestehender Gebäude | |
| subsidised | gefördert | Says nothing about the owner. |
| restricted | gebunden | „the rent is restricted for a period“. Never „bound“: „bound for“ means „heading for“. |
| funding scheme 1, 2 | Förderweg 1, 2 | Subsidy programmes of the city. „funding schemes 1 and 2 (Förderweg)“. |
| dormitories | Wohnheime | |
| city government | Magistrat | In brackets once: „city government (Magistrat)“; later „the Magistrat“. |
| Hessian statistics office | Hessisches Statistisches Landesamt, Landesamt | „the Hessian statistics office (Landesamt)“ once, then „the statistics office“. |
| population register | Melderegister | |
| expert reports | Gutachten | The Mietspiegel reports. |
| losses of dwellings | Abgänge | Dwellings that leave the stock, for example by demolition. Never „removals“: in British English that means moving house. |
| Q3 2025 | 3. Quartal 2025 | A quarter of the year, written „Q3“. The texts never use the word „quarter“. |
| median wage, high wage | mittlerer Lohn, hoher Lohn | The high wage is the pension insurance contribution ceiling (Beitragsbemessungsgrenze). |
| service charges and heating costs | Betriebs- und Heizkosten | |
| basic income support | Grundsicherung | A benefit name: stays German with this gloss. |
| social housing, social housing dwellings | Sozialwohnungen | Capped rent and an income limit for a fixed period; never „council housing“. „social housing dwellings“ where the text counts them. |
| rent and occupancy restriction | Mietpreis- und Belegungsbindung | |
| housing benefit | Wohngeld | |
| minimum income support | Mindestsicherung | |
| unemployment density | Arbeitslosendichte | Unemployed per resident aged 15 to 64; not the unemployment rate. |
| deprivation index | Benachteiligungsindex | |
| minimum wage | Mindestlohn | |
| net wage | Nettolohn | |
| household net income | Haushaltsnettoeinkommen | |
| prices, wages in Hessen | Preise, Löhne in Hessen | |
| without inflation | ohne Inflation | In prose „in the chart without inflation“: a sentence that starts „Without inflation, …“ reads as „if there were no inflation“. |
| housing office | Wohnungsamt | |
| ownership type | Eigentumsform | One of the eight classes of the Zensus. |
| people | Personen, Menschen | Owners are „Personen“, everyone else „Menschen“; English says „people“ for both, never „humans“. „The dwellings belong to people or companies.“ |
| private individuals | Privatpersonen | The class of the Zensus. |
| condominium owners (WEG) | Wohnungseigentümer*innen (WEG) | Owners of the flats of a building split into condominiums (Eigentumswohnungen). |
| associations of condominium owners | Gemeinschaften von Wohnungseigentümer*innen | |
| renting out housing | Vermietung | Never „renting“ alone or „letting“. |
| public sector | öffentliche Hand | |
| city, federal government, state | Kommune, Bund, Land | The state is Hessen. „state (Land)“ and „federal government (Bund)“ once. „municipal“ stays for the class „kommunal“ of the Zensus. Never „Federation“. |
| housing cooperatives | Genossenschaften | |
| private housing companies | Privatwirtschaftliche Wohnungsunternehmen | |
| other private companies | Andere privatwirtschaftliche Unternehmen | |
| private companies | Private Unternehmen | The sum of both company classes. |
| non-profit organisations | Organisationen ohne Erwerbszweck | |
| Private, Community | Privat, Gemeinschaft | The sectors of Trend. |
| unassigned | nicht zugeordnet | |
| standard land value | Bodenrichtwert | Its ⓘ explains it: „the official average value of land per m² in a zone“. |
| standard land value zone, zone | Bodenrichtwertzone, Zone | The zones of BORIS. „zone“ also stands for the land use of a zone. |
| residential zone, mixed-use zone | Wohngebiet, Mischgebiet | „residential or mixed use“ after „zones for“. |
| land ready for building | baureifes Land | The state of development „B“ of BORIS. |
| Hessian building code | Hessische Bauordnung | A law: stays German with this gloss; „setback distances“ glosses Abstandsflächen. |
| federal building code | Baugesetzbuch (BauGB) | A law: „BauGB (federal building code)“ once per text. |
| development plan | Bebauungsplan, B-Plan | |
| in preparation | im Verfahren | Plans and statutes. Never „pending“. |
| social preservation statute | Milieuschutz | § 172 para. 1 no. 2 BauGB; also „social preservation“. Its ⓘ: „These statutes aim to protect the current mix of residents.“ |
| townscape statute | Ortsbildsatzung | Its ⓘ: „These statutes protect the look of a place.“ |
| building gap | Baulücke | |
| unused land | Brache | Never „wasteland“. |
| block of flats | Mehrfamilienhaus | Never „multi-family house“. |
| roof surface | Dachfläche | „area“ is the Gebiet. |
| parcel | Flurstück | |
| low flat roof | niedriges Flachdach | |
| light housing module | leichtes Wohnmodul | |
| city council election | Stadtverordnetenwahl | |
| votes | Stimmen | A share of votes says „votes“, never „voters“. |
| voters, postal voters, eligible voters | Wählende, Briefwählende, Wahlberechtigte | |
| turnout | Wahlbeteiligung | |
| list | Liste | |
| strongest list | Stärkste Liste | The ⓘ of the lists explains „list (party or voter group)“. |
| vote share of a list | Anteil der Liste | |
| Others | Sonstige | The group of the lists under the threshold in the city; it stands like a list name. |
| valid votes | gültige Stimmen | |
| official final result | amtliches Endergebnis | |
| estimate plus uncertainty | Schätzung plus Unsicherheit | The label of a criterion on the upper end of an estimate. |
| Map, Trend, New housing, Rent | Karte, Trend, Neubau, Miete | The views. |
| Limits | Vorbehalte | The heading in the help and the cover note. Never „caveats“. |
| date of the data | Stand | In prose; the ⓘ label stays „As of“. Never „as-of date“. |
| share of owner-occupied dwellings | Eigentümerquote | |
| rent of existing contracts | Miete im Bestand | The layer `HOU_RENT`. |
| own analysis | eigene Auswertung | |
| social monitoring | Monitoring, Sozialmonitoring | „(Sozialmonitoring)“ in the help. |
| not met, no data | es fehlt, k. A. bei | The candidates: „Social preservation coverage not met“, „Standard land value: no data“. |
| City, Area, Candidates, Help | Stadt, Gebiet, Kandidaten, Hilfe | The tabs. |
| template, criterion, threshold, met, matches, custom query | Vorlage, Kriterium, Schwelle, erfüllt, Treffer, Eigene Abfrage | The candidates. |

### Tests of the English texts

- `test_english_has_no_banned_term` in `tests/map/assembly/test_catalog.py` scans every `texts.en.yaml`. Its
  `BANNED_EN` bans „cell“, „backtest“, „range“ (for „Spanne“), „comparison“ (for „Abgleich“) and „secrecy“ as words,
  and „NH“. The fixture `banned_en` of `tests/conftest.py` holds the same words for the catalog tests of the views.
- `test_english_uses_british_spelling` bans the American forms of `US_SPELLING` and every -ize form outside
  `IZE_WORDS` („size“, „prize“).
- `test_english_demands_nothing` bans the words of `DEMANDS_EN`: the voice of a campaign („we“, „our“), „should“,
  „call for“, a target or a goal.
- `test_english_is_plain` bans the words of `UNCLEAR_EN` (Reader and style). A reference such as `{@key}` is no word.
- `tests/test_text_copies.py` reads the English files too. An English test literal of 20 or more characters that
  stands in an English text fails.

## Agreeing texts with the user

- Every new or changed visible heading, lead or note is agreed with the user in the chat before it goes into code.
- Propose texts as plain chat text, not as a multiple-choice dialog. Give a recommendation and the numbers behind
  each statement.
  Why: the user shapes the wording and often answers with an own version.
- Model for headings: the red headings of statistik.aktuell 11/2013
  (`sources/frankfurt/statistics/statistik.aktuell 11-2013 Gebäude und Wohnungen Frankfurt.pdf`).
  One finding as a full, plain sentence with subject and verb, sober tone, no slogan.
  Examples: „Die meisten Wohnungen sind in Privatbesitz“, „Mittelgroße Wohnungen herrschen vor“.
- Flag a wording that the data do not cover and offer an equally short exact one. Example: „Konzerne“ for the
  Zensus class of all private companies.
- Propose cuts too, including what can go entirely. If the user's own wording is imprecise, offer an exact variant.
