# Building gaps (Baulücken) in Frankfurt

15 Nov 2026. Question: which parcels in Frankfurt are real Baulücken of sealed or open land, so that a person can find
them on site? The layer `GAP_AREA` and the overlay „Baulücken (magenta)“ answer it
(`pipeline/use_cases/building_gaps/README.md`). Numbers of the build come from `interim/building_gaps_calc_examples.json`
and `interim/building_gaps_checks.json` of the build of 15 Nov 2026, the verdicts from
`reference/building_gaps_reference.csv`.

Answer: 578 parcels pass the geometry rule. 92 of them pass zone and cover filters and were judged by hand in the
aerial image of 19.8.2025. 9 count, with 11,322 m². 14 must be checked on site (20,532 m²). 69 do not count. The map
draws the 9 and the 14. Why our own count: flurcheck.de shows schoolyards, playgrounds and gardens as gaps (walk of
the user, for example the Uhlandschule).

## Data check

- ALKIS NAS, Bestandsdatenausgabe Grundriss, Frankfurt, portion date 4.11.2026: 174,650 parcels, 227,404 buildings,
  45,262 areas of actual land use. [belegt] (`sources/hessen/alkis/alkis_meta.csv`)
- Three parcels read by hand in the raw NAS equal the extract (Kennzeichen; geometry area within max(1 m², 0.5 %) of
  the official area). [belegt] (check `building_gaps`)
- Geometry area against official area, parcels of 250 to 400 m²: median 0.3 %, 90 % under 2.5 %, 2 % over 5 %. The
  rules use the geometry area, as the map draws it. [eigene Auswertung]
- Height model DOM1 and DGM1 (flight 2023) and CIR orthophoto DOP20 (WMS): 576 of the 578 gaps lie in the flight of
  19.8.2025, two in one of 7.7.2023 (`DEHE06200001qvKo`, `DEHE06200001qwos`; both drop at a cover filter). [belegt]
  (`sources/hessen/alkis/building_gaps_cover.csv`)

## Funnel of the build

| Step | Parcels out | Left |
|---|---|---|
| Parcels | | 174,650 |
| main buildings cover at least max(20 m², 5 %) | 75,252 | 99,398 |
| under 300 m² | 53,428 | 45,970 |
| under 80 % Wohnbaufläche or Fläche gemischter Nutzung | 44,075 | 1,895 |
| narrower than 15 m | 837 | 1,058 |
| front under 15 m | 304 | 754 |
| no neighbour wall of 5 m and front under 30 m | 176 | 578 |
| outside a BORIS zone W or M, development state B | 202 | 376 |
| more than half green or tree | 224 | 152 |
| more than 10 % built (height model 2023) | 57 | 95 |
| under half open ground | 3 | 92 |
| judged `not` | 69 | 23 |
| judged `site` | 14 | 9 |
| Counted | | 9 (11,322 m²) |

- Of the 578 geometry gaps, 218 lie between neighbour houses and 360 stand free. Of the 92 judged, 34 and 58. Of the 9
  counted, 6 and 3. [eigene Auswertung]
- The spike of 15 Nov 2026 (minimum 365 m², front without the cut of the side edges) left 616 after the geometry and
  177 after the cover. The build has a minimum of 300 m² and cuts 2 × 1.5 m off each piece of front. [eigene Auswertung]
- The counted gaps lie in seven Stadtteile: Höchst 3,287 m², Griesheim 2,823 m², Kalbach-Riedberg 1,542 m²,
  Bockenheim 1,494 m², Praunheim 957 m², Ostend 844 m², Seckbach 375 m². [eigene Auswertung]
- Areas of the counted gaps: 375, 745, 761, 796, 844, 957, 1,494, 2,062 and 3,287 m². [eigene Auswertung]

## Verdicts

All 92 by eye in the aerial image 2025 (`by=aerial`), with RGB and CIR crops of
`research/scripts/building_gaps_sheet.py`. No visit yet.

| Verdict | Reason | Gaps |
|---|---|---|
| counts | parking (Parkplatz) | 7 |
| counts | yard (Hof) | 1 |
| counts | brownfield (Brache) | 1 |
| site | – | 14 |
| not | new_area (Neubaugebiet, schon verplant) | 19 |
| not | green (Wiese, Garten) | 17 |
| not | construction (Baustelle) | 9 |
| not | other (with a note) | 8 |
| not | new_building (Neubau nach 2023) | 6 |
| not | square (öffentlicher Platz) | 5 |
| not | access (Zufahrt, Weg) | 3 |
| not | play (Spielplatz) | 2 |

- An independent second look at the images agreed with all 10 counts of the first pass. Two verdicts then went to
  `site`. `DEHE06200001biKH` went from `counts` to `site`: it may be a Tiefgarage deck. `DEHE06200001T0hA` went from
  `not` to `site`: the parcel dates from 2013 and still shows rubble and weeds in 2025, and whether the project stalled
  or is planned is unclear.
  [eigene Auswertung]
- A gap judged `not` is not drawn (user, 15 Nov 2026). It stays in the funnel and the checks.

## Traps

- ALKIS lags: many „empty“ parcels carry new buildings in the aerial image 2025. The height model 2023 catches part of
  them. 15 verdicts are `new_building` or `construction`.
- August 2025 was dry. Brown meadows and bare soil read as open ground; neither NDVI nor RGB separates them from
  asphalt. 17 verdicts are `green`.
- Tree canopy over a parking lot counts as green. The Obermain parking lot (`DEHE06200001c3ny`) drops already in the
  geometry (no neighbour wall, front under 30 m).
- Public squares can be Wohnbaufläche in ALKIS. Paul-Arnsberg-Platz (`DEHE06200001c3mk`, 3,191 m²) passes every filter
  and is judged `not`, `square`. Its front reads about 198 m: the boundary along the square's ways counts as front.
- New development areas are parcelled and empty but planned (19 `new_area`). 17 of the 92 judged parcels arose in 2019
  or later. A hint on the sheet, not a rule.
- Tiefgarage parcels: a building 2465 under a yard is minor. The yard is often green or a playground.
- Address links (`weistAuf`) and the parcel year help the verdict but are no rule.

## Examples of the suitability

Checked again on 15 Nov 2026 against the sources (`reference/building_gaps_examples.csv`):

- Friedberger Landstraße 34, Nordend, Wohnbaugenossenschaft in Frankfurt am Main eG, group „Gemeinsam suffizient
  leben“: DAB 05/2025 p. 24 „Das 312 Quadratmeter kleine Grundstück …“, 15 adults and 10 children, „den ehemaligen
  Parkplatz“; p. 25 „momentan neun Wohnungen“. [belegt] The DAB names no house number. OpenStreetMap places number 34
  on the ALKIS parcel `DEHE06200002rjU8` (313 m² official, 312.4 m² geometry). [eigene Auswertung]
- CoBeingHouse B15N.5VG, Gemeinwohlbau Berlin, PDF of 06/2026: p. 1 „Für 19 Mieter*innen“, „Breite 15 m“; p. 4,
  table „Flächenberechnung“: „Grundstück 365 qm“, Nutzfläche 632.8 qm (picture caption: 630 qm). [belegt]
- Studentenwohnheim Allersberger Straße, Nürnberg (gpwirth architekten): „Grundstück: 1.270 qm“, „Apartments: 177“,
  „Baujahr: 2015“, „schließt eine Baulücke im Blockrand“. [belegt]
- ABG, Herxheimerstraße 10, Gallus: press release of the ABG of 18.12.2025, „etwa 2.000 Quadratmeter“, 42 geförderte
  Wohnungen, all in Förderweg 1, first tenants in the fourth quarter of 2027. [belegt] The earlier source was a
  report of entwicklungsstadt.de („rund 2.000“); the ABG release replaces it.
- ABG, Am Wingertsgrund 11-21, Griesheim: press release of 28.1.2025, 5,400 m², 67 frei finanzierte Mietwohnungen,
  ready on 5.2.2025. [belegt] No gap of this run reaches 5,400 m².

## Open

- The 14 `site` gaps need a visit. The user sets `counts` or `not` with `by=site`. [offen]
- Owners are not in the open ALKIS. ABG land (`sources/other/ABG-Holding-Karte.geojson`) could mark gaps later. [offen]
- No Bebauungsplan, Baurecht, Erschließung or Altlasten. [offen]
