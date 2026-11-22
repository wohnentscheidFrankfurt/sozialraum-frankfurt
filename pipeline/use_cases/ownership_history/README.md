# ownership_history: „Trend“

## Shows
No layer. The view „Trend“ with four charts: houses and dwellings per owner group with the sectors „Privat“ and
„Gemeinschaft“, company houses by decade of construction, change 2011 to 2022 per owner group, dwellings of private
companies by size of the house. Charts 1 and 3 show seven groups: the two company classes of the Zensus stay apart.
One source line (`HISTORY_SOURCE`) stands once below the charts; it travels as `history.source`. Every tooltip of a
group describes it; the tooltips of 2022 and of chart 3 also name examples.

## Formula
1. Groups of Zensus classes. „Öffentlich“ = Kommune + Bund oder Land in both years, because the Nassauische
   Heimstätte moved from „Bund oder Land“ (2011) to „Kommune“ (2022).
2. Dwellings per group and year from table 4000W-1011; buildings per group from the totals of 3000G-2007; buildings
   per size of the house from 3000G-2007 and dwellings per size from 4000W-2013; company buildings by decade of
   construction from 3000G-2001. The row labels of the decades are texts (`decade_labels`); `DECADE_KEYS` in
   `shared/zensus/tables.py` gives each decade of the source its key.
   The two company classes („Privatwirtschaftliche Wohnungsunternehmen“, „Andere privatwirtschaftliche Unternehmen“)
   are two groups, with the names of the Zensus. Their sum „Private Unternehmen“ (`company`) carries the lead lines
   and the charts „sizes“ and „decades“.
   Sectors (`SECTORS` in `catalog.py`) as in the city profile of the Rosa-Luxemburg-Stiftung
   (`sources/other/RLS_Stadtprofil_Frankfurt.pdf`, p. 1): „Privat“ = private
   companies, WEG and private persons; „Gemeinschaft“ = Öffentlich, Genossenschaften and Organisationen ohne
   Erwerbszweck. A sector is a plain sum of groups. The move of the Nassauische Heimstätte stays inside „Gemeinschaft“.
   The WEG group is called „Wohnungseigentümer*innen (WEG)“, so that it is not confused with the sector „Gemeinschaft“.
3. Facts behind every heading (`history_facts`): for example the factor of company dwellings 2022 ÷ 2011.
   „Im Schnitt am größten“ needs the smaller of the two company classes above every other group.
   The phrases the checks guard stand once, under `phrases` in `texts.<lang>.yaml`; the texts of the charts take
   them by reference, and `CHARTS` and `PHRASES` of `catalog.py` hold them per language.
4. Charts without a chart library (`web/js/06_history.js`). Text inside a bar only at a contrast of at least 4.5:1
   (`label_color` and `label_contrast` of the group, from Python) and with 4 px room on each side; else the tooltip
   carries the value. Colours as in the RLS city profile: greys for „Privat“, reds for „Gemeinschaft“ around
   `#d40000` (`pipeline/shared/core/palette.py`; the map uses the same colours for its owner groups). A thick arrow
   below 3:1 against white is darkened in its own hue (`line_color` of the group, from Python). The percent change
   in the tooltips of the arrows comes finished (`change` of the group, from Python). In chart 1 a black
   line follows the boundary between the two sectors (`SECTORS`) through both bars and the band between them. Under
   the dwellings the two labels face each other at the boundary, each in the main colour of its sector („color“).
   In 2022 a dashed grey line marks the boundary of 2011 on the dwellings („Grenze 2011“).
   Below 600 px of room the charts are drawn at their width, row labels above the bars; in chart 1 the boundary
   bends below the dwellings to where both sector labels fit. So text keeps its size and nothing scrolls sideways. In
   headings,
   lead lines and caveats a number and its „%“ stay on one line (`APP.keepUnits`, a no-break space).
5. Headings have at most 61 characters: one finding as a full sentence with a verb, modelled on statistik.aktuell
   11/2013.

## Why
The view shows how the ownership of dwellings in Frankfurt changed between the Zensus 2011 and the Zensus 2022. It
helps readers who do not explore the map. Evidence: `research/2026-10-10-buildings-and-dwellings-by-owner.md` and
`research/2026-10-14-who-are-the-private-companies.md`.
- Only this view splits the private companies, and only for the whole city. Per Stadtteil the grid splits the other
  companies only within ±87 %. Exact counts per Stadtteil would need the single records of the count.
- The two company classes stand apart, so each tooltip can name its own examples. Their sum stays for the lead lines.
- Every company heading says „privat“: „Unternehmen“ alone also fits the ABG.
- The sectors „Privat“ and „Gemeinschaft“ follow the RLS city profile. The page does not cite the RLS.
- The boundary line in chart 1 shows the shift of the sectors from 2011 to 2022 without a chart of its own.
- Examples carry no numbers, because the dates of their sources differ (2014 to 2026). No example rests on a party
  document.

## Inputs
No dataset. Files in `sources/zensus/`: tables 4000W-1011, 4000W-2013, 3000G-2001, 3000G-2007,
4000W-2002. The sources of the examples (`EXAMPLES` in `catalog.py`, paths in `pipeline/config.py`): the
Wohnungsmarktbericht 2019/2020 (B 430/2022), BT-Drs. 19/7092, three pages of the Kooperation Frankfurt and an
interview in the efo-magazin. The examples of the companies come from `ownership_shares` (`EXAMPLES`). The exception
is Sahle Wohnen, the third example of the housing companies: only the tooltips of this view name it. It has two
entries: the answer of the Magistrat F 677/2017 (owner of 915 subsidised dwellings, 31.12.2016) and the company page
„Geschäftsführung“ (family-run, active in Frankfurt).

## Output
`ownership_history`, `ownership_by_size`, `company_buildings_by_decade`, `ownership_history_view` (data and texts
of the view), `ownership_history_checks`. Each chart carries its `link` for a direct link
(`docs/design.md`, Direct links): `wem-gehoeren-die-wohnungen`, `wachstum-im-bestand`, `wer-waechst`,
`grosse-haeuser`.

## Checks
- The tables agree with each other per year (totals, sizes, classes).
- Table 4000W-1011 (2022) equals table 4000W-2002.
- Every statement of the headings and lead lines holds (`check_history_headings`).
- „meist vermietet“ in the tooltip of the WEG holds: in 2011 and in 2022 more than half of the WEG dwellings
  are rented (table 4000W-2002: 61.7 % and 53.7 %; `check_condo_rented`). Owner-occupied: 36.6 % and 43.4 %.
  „Rented“ is the Zensus class „Zu Wohnzwecken vermietet (auch mietfrei)“, so it includes rent-free use.
- Every example stands with its passage in its source (`check_examples`, FAIL).

## Limits
- A change of class may be a sale or only another classification; the data cannot tell.
- The chart tooltips (`data-tip`) are built in the browser; no check of the build guards them. The browser check
  tests the tooltips of the chart „houses“ and of one arrow.
- Examples stand only in the tooltips of 2022 and of the arrows: in 2011 Vonovia was called Deutsche Annington.
- An example shows that the owner exists in Frankfurt and belongs to the group. The Zensus class is self-reported;
  the GWH chose its class itself. The tooltips print no numbers of the examples. For Sahle Wohnen the Magistrat
  counts only subsidised dwellings of 2016 (a lower bound); the company page names 23,000 dwellings, mostly in North
  Rhine-Westphalia. Neither number stands in a tooltip.
- „Im Schnitt am größten“ holds for 2022 only. In 2011 the housing companies had 7.9 dwellings per building, below
  WEG (8.1) and the Organisationen ohne Erwerbszweck (8.6). „Verdoppelt“ holds for the sum of both company classes
  (+102 %); the other companies alone grew by 91 %.
- In chart 3 the arrows of Privatpersonen (`#919191` after `line_on` in `pipeline/shared/core/colours.py`) and WEG
  (`#8c8c8c`) look almost alike. The row labels carry identity.
- The source line stands once, so no chart has its own `source`. The keys of charts 2 and 4 name what they count:
  „Häuser 2011/2022“ and „Wohnungen 2011/2022“. The display label „Baujahr vor 1919“ is lower case; the Zensus label
  stays in the data.
- Descriptions and examples stand only in the tooltips. Screen readers get the numbers from the aria-labels, not the
  examples.
