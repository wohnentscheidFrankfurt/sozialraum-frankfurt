# building_gaps: „Baulücken“

## Shows
`GAP_AREA` (layer, topic „Boden“): area of the counted building gaps in m² per district and Stadtteil. Overlay
„Baulücken (magenta)“ (`building_gaps`): only the gaps that count or must be checked on site, with one key row
„Baulücke“. A gap judged `not` is not drawn (user, 15.11.2026: a public square has no reason to be offered on the map).
A gap without a verdict (after a new ALKIS delivery) is not drawn until judged (user, 15.11.2026: an unjudged schoolyard
must never reach the public map). Both stay in the funnel and in the checks. The tooltip says whether a gap counts
(„Zählt: Parkplatz, …“) or must be checked on site. The ⓘ of the layer shows the funnel of the whole city as a written
sum, in parcels, ending in the counted gaps and their area. An area without a counted gap shows 0 m², as `ROOF_FLAT`
shows 0 m² for an area without a counted roof.

## Formula
1. Geometry (model `find_gaps`, steps 1 to 6): a parcel (Flurstück) of the ALKIS extract is a gap if its main
   buildings cover less than max(20 m², 5 %) of it, it has at least 300 m², at least 80 % of it lies in Wohnbaufläche
   or Fläche gemischter Nutzung, a circle of 15 m fits in it, it has a front of at least 15 m, and it touches a
   neighbour main building along at least 5 m („zwischen Nachbarhäusern“) or has a front of at least 30 m
   („freistehend“). The front is the boundary within 1.5 m of a street, a way or a square (not a parking lot). Each
   connected piece of it loses 2 × 1.5 m, the part that runs up the side edges; a closed ring keeps its length.
2. Zone: the representative point lies in a BORIS zone W or M, development state B (as in `flat_roofs` and `land`).
3. Cover (measured by `update_sources`): green and tree at most 50 %, building at most 10 % (height model 2023), open
   ground (neither built nor green) at least 50 %. A gap without a valid height pixel drops as `no_cover`, never as
   „not open“.
4. Hand verdict (`reference/building_gaps_reference.csv`): `counts` (Parkplatz, Hof, Lagerplatz, Brache), `not` (with
   its reason) or `site` (needs a visit). Only `counts` counts. A gap without a verdict does not count and is not
   drawn.
5. Funnel: parcels minus every step equals the counted gaps.
6. Area: sum of the counted parcel areas (geometry area) whose representative point lies in the area.
7. Suitability: the tooltip of a counted or site gap names the largest example its area reaches (300, 365, 1,270,
   2,000, 5,400 m²; `reference/building_gaps_examples.csv`).

## Why
Gaps between houses are land for housing without new roads. A layer of candidates alone shows schoolyards, gardens and
new buildings. Every counted gap is therefore judged by hand, and the tooltip names the parcel so that a person can
find it on site. Only sealed or open land counts. Building on a garden or under old trees is a different question.
The suitability line shows what such a plot carries elsewhere. It is an illustration with real examples, not a plan.
Funnel, traps and verdicts of the first run: `research/2026-11-15-building-gaps.md`.

## Hand verdicts
- `research/scripts/building_gaps_sheet.py` draws an RGB and a CIR crop of every gap past the cover filters without a
  verdict row. Claude judges them by eye and writes one row each into `reference/building_gaps_reference.csv`
  (`by=aerial`). A doubtful gap gets `site`.
- After a visit the user sets `counts` or `not` with `by=site` and the date of the visit. The next build counts it.
- After a new ALKIS delivery a judged parcel may vanish (split, new gml_id). Its row then gives WARN „stale“, and the
  new parcel is not drawn until judged (WARN „without a verdict“).

## Inputs
No datasets of other steps. Files: the ALKIS extracts in `sources/hessen/alkis/` (parcels, buildings, land use, the
facts of the delivery of 4.11.2026) and the cover of the gaps (`building_gaps_cover.csv`, height model 2023 and
orthophoto 19.8.2025), the pages of the BORIS WFS in `sources/hessen/boris/` (zones of 1.1.2024), Stadtbezirke and
Stadtteile in `sources/frankfurt/geodata/`, the monitoring table that joins the Stadtbezirke into the 114 districts,
and in `reference/` the hand verdicts, three parcels read by hand in the raw NAS, the known cases of the user and the
suitability examples.

## Output
The six datasets `building_gaps_by_district`, `_by_quarter`, `_city` (the counted area), `_overlays` (one feature per
drawn gap, with `text` and `counts`; no gap judged `not` or not judged yet), `_calc_examples` (the funnel as a
written sum) and `_checks`.

## Checks
- The portion date of the NAS delivery is 4.11.2026, as the texts say (FAIL).
- Three parcels read by hand in the raw NAS: Kennzeichen equal and geometry area within max(1 m², 0.5 %) of the
  official area (FAIL). The geometry area is the area of the rules; on old parcels it differs from the official one.
- Every gap has a cover row and at least one valid height pixel, and `alkis_meta.csv` names the cover thresholds of
  `model.py` (`HIGH_M`, `NDVI_GREEN`); each is a FAIL (run `update_sources`). Why: the cover file is measured by
  `update_sources`, so a threshold changed in `model.py` has no effect until it runs again, and a broken height package
  would read as 0 gaps. The most common flight is 19.8.2025 (FAIL); other flights are named. A gap with more than 5 %
  of its pixels without height gives WARN.
- Hand verdicts: an unknown verdict, reason or `by`, a reason of the wrong side, „other“ without a note, a bad date, a
  second row of a parcel or a Kennzeichen other than the gap's (a gml_id typo) is a FAIL. A gap past the cover filters
  without a verdict gives WARN, so does a stale row of a parcel that is no such gap any more (after a new delivery). A
  row `not` is not stale: its gap is not drawn, but it is still a candidate.
- Known cases of the user (`reference/building_gaps_known.csv`): FAIL if one changes; a known case `not:<reason>`
  that is not judged yet gives WARN.
- The funnel adds up, and districts and Stadtteile add up to the counted area, to 1 m² (FAIL).
- More than 5 drawn gaps in no district give WARN.
- Every suitability has its example: its area is the threshold (the first one may be larger), and the text names its
  area, its number and, where the CSV gives them, its residents („25 Menschen“) (FAIL).

## Limits
- ALKIS lags behind: new buildings of 2024 and 2025 stand on parcels without a main building. The height model of 2023
  catches part of them, the hand verdict the rest.
- August 2025 was dry. Brown meadows read as open ground. The hand verdict decides.
- Tree canopy over a parking lot counts as green. A lot more than half under trees drops.
- A counted lot may include tree crowns or lawn edges. The whole parcel area counts.
- Public squares can be Wohnbaufläche in ALKIS (Paul-Arnsberg-Platz).
- Two gaps (`DEHE06200001qvKo`, `DEHE06200001qwos`) lie in an orthophoto of 7.7.2023, not of 19.8.2025. Their tooltip
  would name that flight. Neither is drawn now: one drops as built, the other as green.
- The front is an approximation. Each connected piece of boundary near a street loses 2 × 1.5 m for the side edges.
  Where a side edge meets the street at an oblique angle, a little more or less of it lies within 1.5 m. The tooltip
  front can then be off by a few metres. A parcel with two streets or a long side along a way gets a long front
  (Paul-Arnsberg-Platz: about 200 m).
- Rules on the parcel area use the area of the geometry, not the official area of ALKIS. Of the parcels of 250 to
  400 m², 9 in 10 differ by under 2.5 %, 2 % by more than 5 %. A parcel near 300 m² may fall on the other side.
- New development areas are parcelled and empty but already planned. The hand verdict takes them out (`new_area`).
  The parcel year (2019 or later) is a hint on the sheet, not a rule.
- Tiefgarage parcels: a building 2465 under a yard is a minor building. The yard is often green or a playground. The
  hand verdict decides; a possible Tiefgarage deck gets `site`.
- Most verdicts are by eye in one aerial image. A shadow, a car park roof or a construction start after August 2025
  can mislead. The `site` gaps do not count until a visit.
- No Bebauungsplan, no Baurecht, no Erschließung, no Altlasten, no owners, no gaps inside a built parcel.

## Examples of the suitability
Every number of `SUITABILITY_TEXT` was checked against its source on 15.11.2026 (quotes, URLs and the stored copies in
`sources/other/building_gaps_examples/` in `reference/building_gaps_examples.csv`):
- Haus einer Genossenschaft: DAB 05/2025, p. 24 (312 m², Konzeptverfahren 2017, 15 adults and 10 children, so the text
  says „25 Menschen“ (column `residents`), former parking lot) and p. 25 (nine flats). The DAB names the street, not the
  number. Friedberger Landstraße 34 is the address in OpenStreetMap; the ALKIS parcel there has 313 m² official and
  312.4 m² geometry area.
- Haus für alle: PDF „Investorengespräch Kurzvorstellung“ of the Gemeinwohlbau, 06/2026, p. 1 (19 Mieter*innen,
  15 m wide) and p. 4 (table „Flächenberechnung“: Grundstück 365 qm, Nutzfläche 632.8 qm). The PDF is public; the
  source list of the map links https://gemeinwohlbau.de/idee, where a later version with the same numbers lies.
- Studierendenwohnheim: project page of gpwirth architekten (1,270 qm plot, 177 apartments, 2015, „schließt eine
  Baulücke im Blockrand“).
- Mehrfamilienhaus: press release of the ABG of 18.12.2025 („etwa 2.000 Quadratmeter“, 42 geförderte Wohnungen, all
  in Förderweg 1). The map says „rund“.
- Wohnanlage: press release of the ABG of 28.1.2025 (5,400 m², 67 frei finanzierte Mietwohnungen, ready on
  5.2.2025). No gap of the first run reaches 5,400 m², so no tooltip shows it yet.
