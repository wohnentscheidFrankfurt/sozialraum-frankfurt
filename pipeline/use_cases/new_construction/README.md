# new_construction: „Neubau“

## Shows
No layer. The view „Neubau“ with two figures.

The first figure shows all completed dwellings per year 2011 to 2025. Each column has three parts. New construction is
the solid frame from the base. The subsidised part of it is red inside (2023 to 2025 hatched, because the numbers are
provisional). Conversions are the dashed frame on top. The heading says that in 2025 almost every fifth new dwelling
was subsidised, and up to 2024 at most every eighth. The lead names the mean of all dwellings per year in the last 10
years, rounded to hundreds.

The second figure is one block of rents, prices and wages with two charts below each other. All lines are an index with
2017 = 100. The heading (`RENTS_TEXTS["title"]`) says that the dwellings grew faster than the population and the
rents of new contracts faster still. The lead (`RENTS_TEXTS["lead"]`) says that the rents of older contracts rose less
than prices and wages. The block has one ⓘ (key `housing-rents`) and one source line. The footer of the map lists
its sources: the VPI report, the wage table, the Mietspiegel files and the open data of the Melderegister (`SOURCES`
of `catalog.py`, after the entries of the stock and the population).
- Chart 1, „Mieten in Euro, wie im Vertrag“: the dwellings and the population on 31.12. of each year 2017 to 2025, and
  the rents of new and of older contracts in the four survey years of the Mietspiegel (2017, 2021, 2023, 2025).
  Prices and wages are two thin grey reference lines (the wages dashed) with a light grey band between them. The
  dwellings and the population have a gap between 2021 and 2022. There the base changes from the Zensus 2011 to the
  Zensus 2022. A dotted segment leads from 2021 to a hollow dot: the value of 31.12.2022 on the old base.
- Chart 2, „Mieten ohne Inflation“: the rents of new and of older contracts and the wages, each divided by the prices.
  The prices are the reference line at 100.

| Index 2025 (2017 = 100) | Chart 1 (in Euro) | Chart 2 (ohne Inflation) |
|---|---|---|
| New contracts | 136.6 | 109.3 |
| Wages | 130.1 | 104.1 |
| Prices | 125.0 | 100 |
| Older contracts | 116.3 | 93.1 |
| Dwellings (published; chained 107.8) | 106.6 | – |
| Population (published; chained 105.3) | 101.8 | – |

## Formula
1. Per year three HSL values: the dwellings in new residential buildings, Wohnheime included (`new_res`), the dwellings
   in new non-residential buildings (`new_nonres`) and all completed dwellings in residential and non-residential
   buildings, all building measures (`all`). Per year the subsidised dwellings of Förderweg 1 (FW 1) and Förderweg 2
   (FW 2), with their predecessor programmes (Magistrat).
2. New construction = `new_res` + `new_nonres`. Conversions = `all` − new construction. Conversions are the residual:
   no table gives them for Frankfurt directly. They are a net balance, because merging two dwellings lowers them.
   The HSL calls the measures „Baumaßnahmen an bestehenden Gebäuden“.
3. Share = subsidised ÷ new construction, with subsidised = FW 1 + FW 2. The subsidised dwellings come from new-build
   programmes, so the denominator is new construction and not all dwellings.
4. Rule „latest answer wins“: per year and programme the latest answer of the Magistrat counts. 2011 to 2022 come
   from B 12/2024, 2023 to 2025 from the answers named in `SUBSIDISED_SOURCES` of `catalog.py`. The step reads B 12/2024
   only for the years before 2023 (`PROVISIONAL_FROM`).
5. 2011 to 2024 of the three HSL values come from the Regionaldatenbank, 2025 from the HSL report F II 2 2025: table 17
   (`new_res`), table 19 (`new_nonres`) and table 15 (`all`). `add_report_year` adds the report value of each series.
6. Facts behind the heading and the lead (`facts`): the share of the last year, the highest share before it and its
   year, the mean of all dwellings in the last 10 years (2016 to 2025). The phrases the checks
   guard stand once in `texts.de.yaml` under `phrases.*`; the texts refer to them.
7. The browser draws the chart and computes no number. Shares, formatted numbers and tooltips come finished from
   Python (`view`). From 700 px of room the drawing is 760 units wide and scales (`APP.CONSTRUCTION_WIDE` in
   `web/js/08_new_construction.js`). Below it one row per year is drawn in px.
8. Stock: the Fortschreibung des Wohngebäude- und Wohnungsbestands of the HSL, dwellings in residential and
   non-residential buildings on 31.12. 2011 to 2024 come from the Regionaldatenbank table 31231-02-01-4
   (`read_regional_stock`: content `WOHNY1$QMU`, row `WHGGR1` = `%TOTAL%`, day in column `STAG`). 2025 comes from
   table 4 of the HSL report F I 1 j/25 (`read_table_4`): the first number of the row „412 000 Frankfurt am Main,
   Stadt“. The heading of table 4 runs over two pages. The reader takes the row from the left page and the year from
   the right page. `add_report_year` adds 2025, as for the completions. The same reader takes 31.12.2022 on the old
   base from table 4 of the report F I 1 j/22 (July 2023, PDF page 12): 408,605. It stops unless the title of a
   report names the expected base: „Ergebnisse auf Grundlage der Gebäude- und Wohnungszählung 2022“ for j/25 and
   „… 2011“ for j/22 (`NEW_BASE`, `OLD_BASE`).
9. Population: the Fortschreibung des Bevölkerungsstands of the HSL, persons with Hauptwohnsitz in Frankfurt on
   31.12. 2011 to 2025 all come from the Regionaldatenbank table 12411-01-01-4 (`read_regional_population`: content
   `BEVSTD$QMU`, row `GES` = `%TOTAL%`, day in column `STAG`). No report adds a year. `up_to_last_year` stops if the
   extract lacks 2025 (`LAST_YEAR`) or has a later year. The HSL report „Bevölkerung in Hessen am 31. Dezember 2025
   und Bevölkerungsbewegungen im Jahr 2025 nach Gemeinden“ (A I 2 mit A II, A III, A V, July 2026) confirms 2025:
   760,656 (PDF pages 28 and 35, rows „412000“, German 535,235 and not German 225,421). The same reader takes it, with
   the base „Fortschreibungsergebnisse auf Basis Zensus 15. Mai 2022“ (`NEW_BASE`); a check compares it.
   `read_population_report` takes 31.12.2022 on the old base
   from the HSL report „Die Bevölkerung der hessischen Gemeinden am 31. Dezember 2022“ (A I 2 mit A II, A III, A V,
   June 2023): 773,068. It reads every row „412“ or „412000 Frankfurt am Main, Stadt“ with a total and two parts
   (PDF page 33: male and female; pages 36 and 43: German and not German). It stops unless the title page names
   the expected base („Fortschreibungsergebnisse Basis Zensus 09. Mai 2011“, or „… auf Basis Zensus 15. Mai 2022“ in
   2025) and the day („Gemeinden am 31. Dezember“, or „Hessen am 31. Dezember“ in 2025), if the parts of a row do
   not add up, or if two rows differ. A reader finds the number by hand on PDF page 33 in the row „412 Frankfurt am
   Main, Stadt“, column „insgesamt“. Pages 9 and 11 give the balance of the year: 759,224 on 1.1.2022, +13,844.
10. `stock_series`: per year the stock, the population, the completed dwellings (`all` of step 1), the change of the
    stock to the year before and the outflow. Outflow = completed − change. It is a rest: the Fortschreibung is stock
    of the year before + completed dwellings − outflow (Abriss, Umnutzung). Change and outflow stay empty for 2011 and
    for 2022 (`STOCK_BREAKS`), the first year on the base of the Zensus 2022.
11. `stock_facts`: the facts behind heading and ⓘ of the block of rents, per series (`SERIES`: `stock`, `population`).
    The span starts at 2017 (`RENT_FROM`) and ends at the last year of the table it gets. The block of rents gives it
    the stock table up to `RENT_TO` (`up_to_year`). `stock_checks` and the log of the step get the table up to
    `LAST_YEAR`. The published growth = value 2025 ÷ value 2017 − 1.
    The chained growth multiplies the yearly factors. For 2022 it takes the value on the old base (`bridge`). The base
    effect is the value of 2022 on the new base minus the value on the old base.

    | 31.12.2017 to 31.12.2025 | Dwellings | Population |
    |---|---|---|
    | Chained | 408,605 ÷ 389,524 × 415,359 ÷ 404,227 − 1 = 7.79 % | 773,068 ÷ 746,878 × 760,656 ÷ 747,389 − 1 = 5.34 % |
    | Published | 415,359 ÷ 389,524 − 1 = 6.63 % | 760,656 ÷ 746,878 − 1 = 1.84 % |
    | Base effect 2022 | 404,227 − 408,605 = −4,378 | 747,389 − 773,068 = −25,679 |

    The facts also give the outflow of the last year (2025: 5) and the mean outflow of the other years with one base on
    both ends (2012–2021, 2023–2024: 167.0). The mean over all 13 years is 154.54.
12. Rents of the Mietspiegel. `read_rent_surveys` takes per survey year the mean net rent per m² of the new and of the
    older contracts from the reports of the Mietspiegel (Gutachten, Dokumentation) and the survey month from a
    brochure or report; it returns year and month. Each value stands in a pinned phrase (`RENT_SOURCES` in
    `catalog.py`). The date patterns of 2021, 2023 and 2025 pin the survey day as the literal `01`: a brochure with
    another day finds no hit, and the reader stops. The pattern of 2017 holds the month only („Stichmonat … Juni
    2017“). A new contract started in the observation period before the survey day, in the four years before 2017
    and in the six years before each later survey. An older contract (in the reports „erhöhter“ or „veränderter
    Altvertrag“) started before it and had a rent change in it. Contracts without a change are not in the
    Mietspiegel.

    | Survey | New €/m² | Older €/m² | Survey day | Where (PDF pages) |
    |---|---|---|---|---|
    | 2017 | 10.21 | 8.69 | Juni 2017 | Gutachten 2022, figure 21 (p. 90, labels); Gutachten 2018 p. 5 |
    | 2021 | 11.56 | 9.14 | 1.7.2021 | Gutachten 2022 p. 89; brochure 2022 p. 6 |
    | 2023 | 13.05 | 9.43 | 1.7.2023 | Gutachten 2024 p. 29; brochure 2024 p. 6 |
    | 2025 | 13.95 | 10.11 | 1.7.2025 | Dokumentation 2026 p. 102; brochure 2026 p. 5 |

    The values of 2017 stand only in the labels of figure 21 (all, older and new contracts in 2013, 2017 and 2021, in
    this order). The pinned phrase fixes the order. `REPORT_GROWTHS` guards it: the reports print the growth against
    2017 (Gutachten 2022: older +5.2 %, new +13.2 %) and against 2023 (Dokumentation 2026: older +7.2 %, new +6.9 %).
    Figure 1 of the Gutachten 2018 (PDF page 23) and figure 17 of the Dokumentation 2026 (PDF page 103) show the same
    values of 2017 as images. They were checked by hand (`research/2026-11-01-rents-block-review.md`); no check of
    the build reads them. Figure 17 draws all surveys from 2013 to 2025 as one series.
13. Prices. `read_price_index` reads table 3 of the HSL report M I 2 j/25: the Verbraucherpreisindex of Hessen (2020 =
    100) per year and month. `year_prices` takes per year one value. In a survey year it is the value of the survey
    month (June 2017, July 2021, 2023 and 2025). In every other year it is July (`PRICE_MONTH`). 2017 to 2025: 97.2,
    99.2, 100.6, 99.6, 103.1, 109.9, 116.6, 118.7, 121.5.
14. Wages. `read_wage_index` reads the sheet „nach Jahren und Quartalen“ of the HSL press table: the Nominallohnindex
    of Hessen (2022 = 100) per quarter. `year_wages` takes the mean of the quarters 2 and 3 (`WAGE_QUARTERS`). 2017 to
    2025: 88.8, 91.95, 94.4, 92.0, 95.45, 98.05, 104.15, 110.5, 115.5. The survey days lie on the border of both
    quarters, and the quarters differ by special payments. From 2017 to 2025 the 2nd quarter alone gives +28.3 %, the
    3rd quarter alone +32.0 %, the mean +30.1 %.
15. Households. `read_household_size` divides the persons in households by the households of the Melderegister, row
    `insgesamt` of Stadtbezirk, Stadtteil and Nation, from the counts (not from the rounded column). Every year from
    2017 to 2025 counts: 1.8447, 1.8720, 1.8741, 1.8653, 1.8610, 1.8573, 1.8547, 1.8524, 1.8446. The lowest is 2025
    (786,325 ÷ 426,293), the highest 2019 (765,315 ÷ 408,355).
16. `rents_table`: one row per year 2017 to 2025 (dataset `new_construction_rents`). A `*_index` column is the value ÷
    the value of 2017 × 100: `stock_index` and `population_index` (31.12.), `prices_index`, `wages_index`, `new_index`
    and `old_index` (rents, only in the survey years; empty in the others). A `*_real` column is the index ÷
    `prices_index` × 100, so without inflation: `wages_real`, `new_real`, `old_real`. Example 2025, new contracts:
    13.95 ÷ 10.21 × 100 = 136.6; 136.6 ÷ 125.0 × 100 = 109.3. Chart 2 per survey year: new 100, 106.7, 106.5, 109.3;
    older 100, 99.2, 90.5, 93.1. Stops if the first or the last year has no survey or an input lacks a year.
17. `rents_facts`: the growths of the stocks (from step 11), the growth of each rent, price and wage index (index of
    the last year ÷ 100 − 1) in Euro and without inflation, and the lowest and the highest size of a household of all
    years. Rents of new contracts 2017 to 2025: +36.63 % in Euro, +9.30 % without inflation.
18. `rents_view`: the payload `rents` of the view. It holds every text, number, position on the value scale, tick
    text, label and tooltip as the browser shows it. The two value axes (`RENT_AXES`: chart 1 from 95 to 140, chart 2
    from 86 to 112) are fixed; `rents_view` stops if a value lies outside. From 700 px of room the drawing is 760 units
    wide and scales (`APP.CONSTRUCTION_WIDE`), below it every chart is drawn in px. The browser computes no number
    (`docs/design.md`, View Neubau).

## Why
The view shows how many dwellings Frankfurt builds and how many of them have a bound rent. It helps readers who do not
explore the map. Evidence and numbers: `research/2026-10-15-new-construction-data.md`.
- City only, from the HSL. The HSL counts Wohnheime as residential buildings without a break; the city's building file
  counts them only from 2019. The HSL gives no Stadtteile, and the city level is enough.
- No owner type. No source splits Frankfurt's new construction per year by owner.
- The span starts in 2011. The subsidised dwellings exist per year only from then (2010 lacks FW 2 in B 12/2024).
- All dwellings per column, because the Magistrat publishes totals of all dwellings (F 79/2026: 4,203 for 2024).
- The share divides by new construction only: the subsidised dwellings come from new-build programmes, and
  conversions would dilute it by dwellings that no programme counts.
- Columns over years are the form first visitors read without help. The subsidised part is red; the key says
  „(Miete gebunden)“, because red in the view „Trend“ means „Öffentlich“ and „gefördert“ says nothing about the owner.
- Conversions get a dashed frame on top: they are not new, so the solid base stays the comparable part.
- The texts use the term of the HSL, so that readers find the number in its report.
- The block of rents sets the dwellings and the population against the rents of the Mietspiegel, the prices and the
  wages. Evidence: `research/2026-10-25-dwelling-stock.md` (stock and population), `research/2026-10-31-real-rents.md`
  (rents without inflation), `research/2026-10-31-rents-wages.md` (wages against rents) and
  `research/2026-10-31-household-types.md` (household size).
- One axis for all series: every line is an index with 2017 = 100 (`docs/data-rules.md`, Index of several series).
  Equal height means an equal growth since 2017, so the slopes compare growths. The block starts in 2017. Figure 21 of
  the Gutachten 2022 holds the values of 2013 too; the block does not draw them.
- The rents are the means of the Mietspiegel, the city's own published numbers (`docs/data-rules.md`, Precedence). New
  and older contracts stand apart. The two groups count different contracts, and the gap between them grew from 1.52
  €/m² (2017) to 3.84 €/m² (2025). A mean of both would hide it.
- Prices and wages are a scale to read the rents against, not data. They are two thin grey lines with a light grey band
  between them, and their names are grey. A band, because the lead compares the rents with the prices and the wages
  together.
- Prices and wages are those of Hessen. The sources give no index for Frankfurt. The wages say „Löhne in Hessen“
  where the lines are named: in the end label (wide drawing, where the key is hidden) and in the key (phones).
- Each rent is divided by the prices of its survey month. The survey counts the rents on one day, so the prices of
  that month belong to it. The years in between take July.
- The wage of a year is the mean of the quarters 2 and 3. The survey days lie on their border. Each quarter alone
  would move the index of 2025 by about two points: 128.3 (2nd quarter) and 132.0 (3rd quarter) against 130.1.
- Chart 1 shows the rents as the contracts say. Chart 2 divides rents and wages by the prices, so a line below 100 means
  that the rent rose less than the prices. The heading speaks of the rents in Euro, as chart 1 shows them. Without
  inflation the rents of new contracts grew by 9.30 %, the dwellings by 6.63 % (published) or 7.79 % (chained). The gap
  to the chained growth, 1.51 points, lies within the sampling error of the Mietspiegel (own estimate about ±2.6 points,
  `research/2026-11-01-rents-block-review.md`); the gap to the published growth, 2.67 points, lies just outside it. So
  the heading claims nothing without inflation, and the check „rents heading“ tests Euro only (decision of the user,
  1.11.2026). In Euro it demands a margin of 4 points (`RENT_MARGIN`), above the sampling error in Euro (about ±3.2
  points).
- More dwellings than people could mean smaller households. The ⓘ names the size of households of all years: from
  1.84 to 1.87 persons. The lead says nothing about households. Two years do not carry a statement: the Melderegister
  is irregular around 2017. Single households rose by 10,410 in 2015 and fell by 5,796 in 2018 and by 3,315 in 2019.
  From 2019 the file counts other persons (persons in households 3.70 % above the Einwohner/-innen in 2017, 0.89 % in
  2019). So 2017 and 2025 are equal (−0.01 %), but 2018 to 2025 gives −1.47 % and 2016 to 2025 +1.14 %
  (`research/2026-11-01-rents-block-review.md`). The ratio rests on one list, the Melderegister. The Melderegister
  counts other persons than the Fortschreibung (from 2022 it lies about 20,000 above it) and never stands beside it as
  a count.
- The stock comes from the Fortschreibung of the HSL. It rests on the same building statistic as the columns. The
  city's Gebäudedatei has another list: 407,420 dwellings at the end of 2020 and a jump of 8,932 in 2024. It is not
  used.
- The population comes from the Fortschreibung of the HSL too. Both series share the day (31.12.), the publisher and
  the break of the base (2022). The city's Melderegister has no break. Beside the stock of the HSL it would mix two
  lists, one with a break and one without. It is not used for the population (2025: 781,337 against 760,656).
- Both stock lines have a gap between 2021 and 2022. The stock falls from 406,003 to 404,227, although 2,951 dwellings
  were completed in 2022. The population falls from 759,224 to 747,389. The fall is the new base, not a loss of
  dwellings or people. The hollow dots show where each line would go on the old base.
- The heading holds with both calculations. Chained, the dwellings grew by 7.79 % and the population by 5.34 %.
  Published, they grew by 6.63 % and 1.84 %. In Euro the rents of new contracts grew faster than the dwellings in both:
  +36.63 %. The ⓘ names both base effects (`docs/data-rules.md`, Uncertainty).
- The published growth of the population carries the base effect of −25,679. That is 3.4 % of the population of 2017.
- The chain takes the official values of 31.12.2022 on the old base (reports F I 1 j/22 and A I 2), not an estimate.
  The HSL published 2022 still on the Zensus 2011.
- The series of the Regionaldatenbank breaks between 2021 and 2022: 2021 rests on the Zensus 2011, 2022 on the
  Zensus 2022. The report F I 1 j/25 re-bases 2021 instead: table 1 (PDF page 7), footnote 6, „Ab 2021 auf der Basis
  der Gebäude- und Wohnungszählung 2022.“ Hessen on 31.12.2021 is 3,125,004 there, while the Regionaldatenbank and
  the report F I 1 j/22 keep 3,102,732 on the old base. The map follows the Regionaldatenbank: the break is 2022.
- A line needs no zero base; the grid lines with labels show the scale. Chart 1 runs from 95 to 140, chart 2 from 86
  to 112 (`RENT_AXES`). Every value lies inside, the hollow dots included.
- The dwellings are red, like the subsidised part of the columns. Wish of the user: the same look as the columns.
  Red then means two things in the view, so each figure names its own lines: the end labels, and on phones the key.
  The population is black, like the text. The rents belong to the dwellings („Ich zahle Miete für meine Wohnung“), so
  they are red too: the rents of new contracts dark red, those of older contracts light red.
- The stock lines carry no dot. A dot marks a survey day of the Mietspiegel, and a stock is counted every year, on
  31.12. The rent lines carry a dot in each survey year, because only there a rent was measured. The year labels of the
  survey years are dark, the other years grey.
- The heading draws the conclusion that the numbers carry (`docs/texts.md`, Neutrality). It names no cause. The ⓘ says
  what the numbers do not show: how many people look for a fitting dwelling, and how high the rents would be without
  the new dwellings.
- The population is no measure of demand. A resident counts once, whether the dwelling fits or not. At the end of 2025,
  19,672 persons in 7,464 households were registered for a subsidised dwelling (Jahresbericht 2025 of the Amt für
  Wohnungswesen, B 223/2026 Anlage 1, page 17); registration needs a tie to Frankfurt (page 18). In 2025, 1,419
  households got one (page 25). Tenants who would move to a smaller dwelling pay more for less space
  (`research/2026-10-06-wohnungsmarkt-sozialraum-protokoll.md`, Lock-in). People who left the city or never came are in
  no count. The ⓘ names this without a number, so it needs no source and no check of its own (decision of the user,
  1.11.2026).

## Inputs
No dataset. Files in `sources/`, with their names in `pipeline/config.py`:
- `REGIONAL_COMPLETIONS_CSV`: Regionaldatenbank table 31121-01-02-4, dwellings in new residential buildings per year.
- `REGIONAL_NEW_NONRES_CSV`: Regionaldatenbank table 31121-02-02-4, dwellings in new non-residential buildings.
- `REGIONAL_ALL_DWELLINGS_CSV`: Regionaldatenbank table 31121-03-02-4, all completed dwellings.
- `HSL_COMPLETIONS_2025_PDF`: HSL report F II 2 2025, tables 15, 17 and 19, the values of 2025.
- `HSL_COMPLETIONS_2024_PDF`: HSL report F II 2 2024, tables 15, 17 and 19, only for checks.
- `REGIONAL_STOCK_CSV`: Regionaldatenbank table 31231-02-01-4, the stock of dwellings on 31.12. 2011 to 2024.
- `HSL_STOCK_2025_PDF`: HSL report F I 1 j/25, table 4, the stock on 31.12.2025.
- `HSL_STOCK_2022_OLD_BASE_PDF`: HSL report F I 1 j/22, table 4, the stock on 31.12.2022 on the Zensus 2011, for the
  chained growth and the hollow dot.
- `REGIONAL_POPULATION_CSV`: Regionaldatenbank table 12411-01-01-4, the population on 31.12. 2011 to 2025 (the file
  holds 1995 to 2025).
- `HSL_POPULATION_2022_OLD_BASE_PDF`: HSL report A I 2 mit A II, A III, A V, 2nd half of 2022, the population on
  31.12.2022 on the Zensus 2011, for the chained growth and the hollow dot.
- `HSL_POPULATION_2025_PDF`: HSL report A I 2 mit A II, A III, A V, 2nd half of 2025, the population on 31.12.2025 on
  the Zensus 2022, only for a check.
- `SUBSIDISED_B12_PDF`: B 12/2024, subsidised dwellings per year 2010 to 2023.
- `ANSWER_F_3150_2025_PDF`: FW 2 of 2023.
- `ANSWER_F_79_2026_PDF`: FW 1 and FW 2 of 2024.
- `ANSWER_F_9_2026_PDF`: FW 1 and FW 2 of 2025.
- `ANSWER_F_158_2026_PDF`: FW 1 of 2023 and a confirmation of FW 1 of 2025.
- `ANSWER_B_483_2025_PDF`: B 483/2025, all completed dwellings 2019 to 2024 as the Magistrat gives them (check).
- `MIETSPIEGEL_2022_REPORT_PDF`: Gutachten and Dokumentation of the Mietspiegel 2022. The rents of 2017 (figure 21) and
  2021, and the printed growth 2017 to 2021 (check).
- `MIETSPIEGEL_2024_REPORT_PDF`: Gutachten of the Mietspiegel 2024, the rents of 2023.
- `MIETSPIEGEL_2026_REPORT_PDF`: Dokumentation of the Mietspiegel 2026, the rents of 2025 and the printed growth 2023
  to 2025 (check).
- `MIETSPIEGEL_2018_REPORT_PDF`: Gutachten of the Mietspiegel 2018, the survey month of 2017.
- `MIETSPIEGEL_2022_PDF`, `MIETSPIEGEL_2024_PDF`, `MIETSPIEGEL_2026_PDF`: the brochures, the survey days of 2021, 2023
  and 2025.
- `HSL_PRICES_PDF`: HSL report M I 2 j/25, table 3, the Verbraucherpreisindex of Hessen per month.
- `HSL_WAGES_XLSX`: HSL press table, sheet „nach Jahren und Quartalen“, the Nominallohnindex of Hessen per quarter.
- `HOUSEHOLDS_CSV`: Melderegister, persons in households and households per Stadtbezirk 2010 to 2025 (open data of
  the city); the build takes the row `insgesamt` for 2017 and 2025.

## Output
- `new_construction` (one row per year).
- `new_construction_stock` (one row per year: `year`, `stock`, `population`, `completed`, `change`, `outflow`).
- `new_construction_rents` (one row per year 2017 to 2025: `year`, `stock`, `population`, the indices `stock_index`,
  `population_index`, `prices_index`, `wages_index`, the indices without inflation `wages_real`, `new_real`,
  `old_real`, and the rents `new` and `old` in €/m² with their indices `new_index` and `old_index`, empty outside the
  survey years).
- `new_construction_view` (data and texts of the view). The columns stand in the top level, the block of rents under the
  key `rents`. Both carry their `link` for a direct link (`docs/design.md`, Direct links): `gefoerderte-wohnungen`
  and `wohnungen-und-mieten`. Each `info` carries its written sums (`calc_examples`): `column_sum` and `share_sum` of
  the last year, `rent_sum` of the new contracts of `RENT_TO`.
- `new_construction_checks`.

The payload `rents` holds `title`, `lead`, `info`, `source` and `charts`, a list of two charts (`id` `nominal` and
`real`). A chart holds:
- `title` and `explain` (the line below the title).
- `key`: the entries for phones, one per series in the order of `end_order`, then the old base in chart `nominal`. An
  entry has `id`, `name`, `kind` (`data`, `reference` or `old_base`), `colour`, `width` and `dash` (`null` or a dash
  pattern; the old base has `1 4`, the pattern of the dotted segment to its hollow dot). A data entry
  also has `dot`, whether its swatch has a dot (rents `true`, stocks `false`). A reference entry also has `edge` (`top`
  for the reference with the higher last value, `bottom` for the other) and `band`, the colour of the band.
- `band`: `between` (the two series ids the band fills, `wages` and `prices`) and `colour`. The browser fills it through
  the values of the first series and back through the second.
- `axis`: `min`, `max`, `ticks` and `tick_texts`.
- `years`, `survey_years` (the years with a rent value, taken from the table) and `series` in drawing order, the
  references first. A series has `id`, `name`, `kind`, `colour`, `ink` (the colour of its end label: grey for a
  reference, the ink colour for a data line), `width`, `dash`, `values` (one per year, `null` where a year has no
  value), `dots` (the list of years that get a dot: the rents their survey years, a stock or a reference none),
  `end_value_text` and `end_name` (for the wages „Löhne in Hessen“).
- `end_order`: the series ids by their last value, highest first, the order of the end labels. A tie keeps the drawing
  order.
- `tips`: per year `year`, `head`, `rows`, `note` and `text`. A row is `[value_text, label, series_id]`: the browser
  draws the swatch of a row in the colour, width and dash of its series. `text` holds the whole tooltip as one string.
- `aria_label`: the title and every tooltip.
- Chart `nominal` adds `break` (year and note), `old_base` (the break year, and per stock series the index value and
  the tooltip of its hollow dot) and `old_base_note` (the note below the chart in the wide drawing).

## Checks
In another language than German only the statement checks run: „texts of the ⓘ“, „stock outflow of the last year“,
„rents heading“, „rents households“, „rents lead older contracts“ and „rents uncertainty“. The code of the language
stands in their names („rents heading (en)“). The numeric checks run once (`for_language`).
- „heading fifth“ (FAIL): the share of the last year lies from 18 % to under 20 %.
- „heading eighth“ (FAIL): every share before the last year is at most 12.5 %.
- „lead average“ (FAIL): the mean of all dwellings of the last 10 years rounds to 4,100 (2016 to 2025: 4,097.3).
- „conversions not negative“ (FAIL): conversions are not negative in any year. The drawing cannot show a negative
  part. The text names the years.
- „texts of the ⓘ“ (FAIL): rule and uncertainty name the span of the provisional years (`provisional_span`:
  „2023 bis 2025“, “2023 to 2025”).
- „gap of 2019 and 2020“ (FAIL): all dwellings of 2019 and 2020 in the table are above the totals of B 483/2025
  (3,663 and 4,349). The uncertainty of the ⓘ says that the Magistrat names lower totals for these years.
- „HSL report 2024“ (WARN): table 17 of the report 2024 gives the same value for 2024 as the Regionaldatenbank.
- „HSL report 2024 tables 15 and 19“ (WARN): table 15 gives the same all dwellings for 2024 as the Regionaldatenbank
  (4,203), table 19 the same new non-residential dwellings (17).
- „FW 1 of the last year“ (WARN): F 158/2026 gives the same FW 1 for 2025 as F 9/2026.
- „rents heading“ (FAIL): the heading starts with „Seit 2017“ (`RENT_FROM`). From 2017 to 2025 the dwellings grew faster
  than the population, published (6.63 % against 1.84 %) and chained (7.79 % against 5.34 %). The rents of new contracts
  grew faster than the dwellings in Euro (36.63 %), by more than 4 points (`RENT_MARGIN`) against the published and the
  chained growth of the dwellings. Without inflation (9.30 %) is not checked: the gap to the chained growth of the
  dwellings (1.51 points) lies within the sampling error.
- „rents households“ (FAIL): the rule of the ⓘ names the lowest and the highest persons per household of all years
  2017 to 2025, rounded to two decimals (1.8446 in 2025, 1.8741 in 2019).
- „rents lead older contracts“ (FAIL): the index of the older contracts in 2025 lies below the prices (125.0) and the
  wages (130.1) in chart 1 (116.3) and below 100 without inflation in chart 2 (93.1). The lead says „weniger als
  Preise und Löhne“.
- „rents growth rates of the reports“ (FAIL): the growth rates that the reports print equal the growth of the values
  read, rounded to one decimal (`REPORT_GROWTHS`): Gutachten 2022 (older +5.2 %, new +13.2 % against 2017),
  Dokumentation 2026 (older +7.2 %, new +6.9 % against 2023). This guards the labels of 2017, which no sentence
  prints.
- „rents survey dates“ (FAIL): the survey month read from each brochure and from the Gutachten 2018 is the month of
  `SURVEY_DATES` (June 2017, 1 July 2021, 2023, 2025; the tooltips show the date in the language of the text). The
  VPI of each survey month, as an index with 2017 = 100, equals the price index of the table within 0.05.
- „rents uncertainty“ (FAIL): the ⓘ names both base effects „25.679“ and „4.378“ (`BASE_EFFECTS`), and they match the
  data. It also names the growth since 2017 in both calculations, in the order of the text: chained 7,8 % (dwellings)
  and 5,3 % (population), then as published 6,6 % and 1,8 % (the index of the last year minus 100). The four numbers
  are constants (`SAME_BASE_GROWTH`, `PUBLISHED_GROWTH`) that the text takes; a different number or
  order fails (docs/data-rules.md, Uncertainty).
- „stock outflow“ (WARN): the outflow is not negative in any year with one base on both ends.
- „stock outflow of the last year“ (FAIL): if the outflow of the last year is below a third of the mean outflow of the
  other years with one base on both ends (`OUTFLOW_THIRD`), the ⓘ must hold the caveat sentence (phrase
  `outflow_caveat` in `texts.de.yaml`).
  2025: outflow 5, mean of the other years 167.0, so the sentence is required. The text names both numbers.
- „population report of the last year“ (WARN): the HSL report A I 2 of the 2nd half of 2025 is of 31.12.2025 and gives
  the same population of Frankfurt as the Regionaldatenbank (760,656).
- The readers stop on format drift: a missing year or content code, a region other than Frankfurt, a value without
  quality flag „e“, a year with two rows, a day other than 31.12. in the stock, a table row that does not match, a
  sum that does not add up (B 12/2024: each row, FW 1, FW 2 and the grand total), a missing phrase. `read_table_4`
  stops if it finds no table 4 with the row „412 000 Frankfurt am Main, Stadt“, or if the title names another base
  than the expected one. `read_population_report` stops if the title page names no „Basis Zensus“ of the expected
  year (2011 for the report of 2022, 2022 for the report of 2025) or no „31. Dezember“, if it finds no row of
  Frankfurt, if the parts of a row do not add up or if two rows differ.
  `stock_facts` stops if the break year has no value on the old base, for the stock or the population.
- The readers of the block of rents stop on drift too. A pinned phrase of a Mietspiegel is missing or found twice, a
  value is no number with a decimal comma, a survey month is no month. A brochure with a survey day other than the 1st
  finds no hit (the date patterns of 2021, 2023 and 2025 pin the day as `01`; that of 2017 reads the month only).
  The VPI table is missing or on two pages, a year has not 12 months, a mean and a change, or appears twice. The wage
  sheet lacks the sheet name, the headers or the base („Nominallohnindex“, „2022 = 100“), a quarter has no year, comes
  out of order, has no number or appears twice. The household CSV lacks a column, has no row `insgesamt` at all, has
  a year twice or a year without households; `rents_facts` stops on a missing year. `year_prices` and `year_wages`
  name the first month or quarter without a value. `rents_view` stops on a value outside its axis.
- `GERMAN_MONTHS` in `sources.py` reads the month names of the brochures. `SURVEY_DATES` holds (month, day) as
  numbers; `shown_date` writes them from the texts of the language.
- The step stops if an HSL report (F II 2 or F I 1) is not of the last year or a Regionaldatenbank extract has the
  last year already. The population is the exception: no report adds its last year, so `up_to_last_year` stops if
  the extract lacks the last year or has a later one. The series stop on a missing year and name the year and the
  input.
- B 12/2024 agrees with B 430/2022 for 2019 and 2020. Checked by hand in `research/2026-10-15-new-construction-data.md`;
  no check of the build guards it.
- The stock of 31.12.2024 (411,592) is the same in the Regionaldatenbank and in table 4 of the report F I 1 j/24.
  Checked by hand in `research/2026-10-25-dwelling-stock.md`. The report is not stored, so no check of the build
  guards it.
- The population of 31.12.2021 and 2024 in the Regionaldatenbank equals the HSL reports A I 2
  (`sources/README.md`, regionalstatistik). Checked by hand; no check of the build guards it. 2025 is guarded by the
  check „population report of the last year“.

## Limits
- City only. The HSL gives no Stadtteile.
- No owner type per year. „Gefördert“ says nothing about the owner.
- Conversions are a residual and a net balance. Other districts have negative values; Frankfurt has none 2011 to 2025.
  The check stops the build if one appears.
- New non-residential dwellings are few (1 to 330 per year). They count as new construction, because subsidised
  dwellings may stand in mixed-use new buildings.
- The share mixes two lists. The HSL counts new construction, the Magistrat the subsidised dwellings. Both count
  completions reported under the HBO („Fertigstellungsanzeige nach HBO“, F 79/2026). The subsidised numbers come from
  the programme lists of the city. The programmes are new-build programmes (B 12/2024). Numerator and denominator are
  not counted on exactly the same list.
- B 483/2025 gives the same totals of all dwellings for 2021–2024: 3,914, 2,951, 3,661 and 4,203. For 2019 and 2020
  it gives 3,663 and 4,349; the HSL gives 4,641 and 4,675. The ⓘ names this gap without numbers. F 3150/2025 (3,661 in
  2023) and F 79/2026 (4,203 in 2024) give the same totals.
- The Regionaldatenbank and the reports may revise single years; the build reads the current extracts.
- 2023 to 2025 are provisional. Early counts of the Magistrat were revised upwards so far.
- Wohnheime count as new dwellings, but have their own subsidy programme. They add to the denominator only.
- The uncertainty of the ⓘ is two-sided: the city counts the subsidised dwellings by its programmes, the HSL the new
  dwellings, and both counts do not match exactly.
- B 12/2024 contains an error: the table prints a Gesamt of 177 for 2023, but FW 1 90 plus FW 2 86 give 176
  (`B12_ROW_DEVIATION` in `sources.py` allows exactly this). The step does not use B 12/2024 for 2023.
- A new answer of the Magistrat or a new HSL report needs a hand update of `SUBSIDISED_SOURCES` and
  `pipeline/config.py`.
- The stock is not counted. The Fortschreibung adds the completed dwellings to a Zensus base and subtracts the
  outflow. Its error grows with the years since the base. The Zensus 2022 set a new base: 2022 has no change and no
  outflow.
- The outflow is a rest. It holds every correction of the Fortschreibung, not only Abriss and Umnutzung. In the years
  with one base on both ends it lies from 5 to 431 dwellings, mean 154.54.
- The growths since 2017 cross the break. Dwellings: published 6.63 %, chained 7.79 %. Population: published
  1.84 %, chained 5.34 %. Neither calculation is the true growth. The base effects at 2022 are −4,378 dwellings and
  −25,679 persons: the Zensus 2022 sets both below the Fortschreibung on the Zensus 2011.
- The population is not counted either. The Fortschreibung adds births and inflows to a Zensus base and subtracts
  deaths and outflows. The Zensus 2022 lowered it by 3.3 % (25,679 of 773,068), the stock by 1.1 % (4,378 of
  408,605).
- The heading names the year, because the statement depends on it. From the survey before, 2013, it holds in both
  calculations of the map too: dwellings 11.64 % published and 12.85 % chained, population 8.46 % and 12.18 %. The
  Melderegister grew by 12.69 % from 2013: more than the published growth of the dwellings and less than the chained
  one. From 2011 and 2012 the statement fails chained. From 2017 it holds against every calculation, the Melderegister
  included (5.43 %; `research/2026-11-01-rents-block-review.md`). A new base year needs a new heading, and the check
  „rents heading“ stops the build if the heading no longer holds.
- The block compares counts and rents, not need. The ⓘ names the size of households; it says nothing about vacancy
  or second homes. It names no cause. The ⓘ says that the numbers do not show how many people look for a fitting
  dwelling, nor how high the rents would be without the new dwellings.
- The Mietspiegel leaves out subsidised dwellings with a bound rent (§ 558 Abs. 2 Satz 2 BGB). The Dokumentation 2026
  (`MIETSPIEGEL_2026_REPORT_PDF`, page 10, group 2 b) lists them: „Wohnraum, dessen Miethöhe durch Gesetz oder im
  Zusammenhang mit einer Förderzusage festgelegt worden ist“, among them „Sozialwohnungen … mit öffentlichen Mitteln
  gefördert … und der Mietpreisbindung unterliegen“. The Gutachten 2024 (page 9), 2022 (page 11) and 2018 (page 7) list
  the same. Before the draw of the sample the Melderegister was cleaned of 42,989 persons in subsidised dwellings and
  special forms of housing (Dokumentation 2026, page 13). Rent limits without a formal binding, which public housing
  companies, cooperatives or private landlords set themselves, do not exclude a dwelling (footnote 1, page 10). The ⓘ
  says this in the rule.
- The mean of the Mietspiegel is not the average rent of all dwellings. It covers rents that were agreed or changed
  in the observation period. Contracts without a rent change are missing. The groups are samples of each survey, not a
  fixed set of contracts.
- The means are not adjusted for new and modernised dwellings. The Gutachten 2018 says so (page 23: „keine hedonische
  Bereinigung … der auf Neubau und Modernisierung entfallende Anteil der Preissteigerung nicht herausgerechnet“). The
  later reports print plain sample means too. New dwellings raise the mean of the new contracts. The size is unknown.
  The ⓘ names it (decision of the user, 1.11.2026). In Euro the gap of the heading is large enough: 36.63 % against at
  most 7.79 %.
- Parking: the means of 2021 probably include parking surcharges, those of 2025 do not. Both reports give the pair for
  the means of all contracts only. The Gutachten 2022 (page 89) gives 10.29 €/m² before and 10.21 after the deduction,
  and figure 21 draws 10.29. The Dokumentation 2026 (page 102) gives 12.28 after and 12.33 before the deduction; its
  figure 17 says „um Stellplatzzuschläge bereinigt“ but draws 10.29 for 2021. The report of 2018 does not say which. For
  all contracts the effect is 0.4 % (2025) to 0.8 % (2021).
- The reports print no sampling error of the means. Own rough estimate for 2017 to 2025 (95 %; relative spread from the
  deciles of all contracts, 2017 with the spread of 2021, cases of each group, design effect 1.5 assumed): new contracts
  136.6 ± 3.2 in Euro and 109.3 ± 2.6 without inflation, older contracts 116.3 ± 2.8 and 93.1 ± 2.2.
  `research/scripts/rents_block_review.py` computes it (`research/2026-11-01-rents-block-review.md`). So the heading
  compares in Euro only, with a margin of 4 points (`docs/data-rules.md`, Uncertainty). The ⓘ names no sampling error,
  because the reports print none and the estimate rests on assumptions (decision of the user, 1.11.2026).
- The observation period is four years in 2017 and six years from 2021 (§ 558 BGB since 2020). A longer period takes
  in more older rents and lowers the means somewhat. The step from 2017 to 2021 is rather too small. The size of the
  effect is unknown. The ⓘ names it.
- The values of 2023 come from the adjustment sample (Anpassungsstichprobe) of the Mietspiegel 2024, not from a survey
  like those of 2017, 2021 and 2025. The editions 2012, 2016 and 2020 carry the previous table forward with the price
  index. They are no survey, and the block reads none of them.
- Four survey years give four points per rent line. The line between two points is no measurement. A year without a
  survey has no rent, no dot and no row for it in the tooltip.
- The rents of older contracts fell without inflation above all in 2022 and 2023, when the prices rose strongly
  (index without inflation: 99.2 in 2021, 90.5 in 2023, 93.1 in 2025).
- The wages are the Nominallohnindex of Hessen, not of Frankfurt. It covers the gross monthly earnings including
  special payments. Up to 2021 it covers the branches B to S of the WZ 2008, from 2022 A to S (footnote of the HSL
  table). A year takes the mean of two quarters. The prices are those of Hessen too.
- The stocks count on 31.12., the rents, prices and wages at mid-year. In the chart they share the slot of their year,
  so a stock counts half a year later than a price in the same slot. The index of a stock starts on 31.12.2017.
- The Regionaldatenbank keeps 31.12.2021 on the old base, the report F I 1 j/25 re-bases it (table 1, footnote 6:
  „Ab 2021 auf der Basis der Gebäude- und Wohnungszählung 2022.“; Hessen 3,125,004 against 3,102,732). Frankfurt on
  31.12.2021 on the new base is in no stored source. So the series of the Regionaldatenbank breaks between 2021 and
  2022.
- The outflow of 2025 may be too low. Since the change of the HBO of 14.10.2025 (§ 63a) most demolitions need no
  permit. The HSL says that the recording of Bauabgänge may be affected and the comparability is limited (report
  F I 1 j/25, Vorbemerkungen, PDF page 4). The outflow of 2025 is 5, the mean over all 13 years 154.54. The city's
  `BT_Reinzugang.csv` counts 216 dwellings demolished in 2025 (2020–2024: 298, 300, 292, 206, 105). The ⓘ names
  the caveat.
- 2011 to 2024 of the stock come from the Regionaldatenbank, 2025 from the report F I 1 j/25. The population comes
  from the Regionaldatenbank alone; the report A I 2 of the last year checks it. A new year needs a hand update of
  `HSL_STOCK_2025_PDF`, `HSL_POPULATION_2025_PDF`, both extracts and `LAST_YEAR`. The reports F I 1 j/22 and A I 2 of
  2022 stay: they are the last ones on the Zensus 2011, and `BASE_EFFECTS` rests on them.
- The block of rents ends at `RENT_TO`, the last survey year (`max(SURVEY_DATES)`, 2025). The columns and the stock
  run to `LAST_YEAR`, and `RENT_TO <= LAST_YEAR` (a test guards it). The annual update of the HSL data without a new
  Mietspiegel survey (the next is 1.7.2027) moves `LAST_YEAR` only: the block keeps its end year and the step does
  not stop. A new survey year needs, by hand:
  - the new Mietspiegel files in `sources/` and their names in `pipeline/config.py`;
  - a new entry in `RENT_SOURCES` (a pinned phrase for the two means, one for the survey date), in `REPORT_GROWTHS`
    (the growth the report prints against the survey before) and in `SURVEY_DATES`; `RENT_TO` follows from it;
  - a price report, a wage table and a household CSV that reach the new year (`HSL_PRICES_PDF`, `HSL_WAGES_XLSX`,
    `HOUSEHOLDS_CSV`): `year_prices`, `year_wages` and `rents_facts` stop on a missing month, quarter or year;
  - a look at `RENT_AXES`: `rents_view` stops if a value lies outside;
  - the Stand line of the ⓘ (`as_of`) follows from `RENT_TO`, its entry in `SURVEY_DATES` and `WAGE_QUARTERS`; the
    rule names `PRICE_MONTH`. Check the four literal growths of the uncertainty and the source line of the ⓘ and the
    footer (`SOURCES`: the VPI report, the wage table, the Mietspiegel files).

  The readers stop on drift, and the checks stop the build until heading, lead, ⓘ and data match.
- City only, also for the stock and the population. The Fortschreibung of the HSL gives no Stadtteile.
- The wide chart 1 puts its years in slots of (760 − 46 − 200) ÷ 9 ≈ 57.1 units, because of the margins of the axis and
  the end labels. The columns above use slots of 760 ÷ 15 ≈ 50.7 units. So the years of the columns and the charts
  do not line up.
