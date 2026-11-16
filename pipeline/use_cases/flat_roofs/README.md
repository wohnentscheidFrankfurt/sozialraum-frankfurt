# flat_roofs: „Niedrige Flachdächer“

## Shows
`ROOF_FLAT` (layer, topic „Boden“): counted area of low flat roofs in m² per district and Stadtteil. Overlay
„Niedrige Flachdächer (braun)“ (`flat_roofs`): the roofs themselves, with the two key rows „Niedriges Flachdach, zählt“
and „Niedriges Flachdach, zählt nicht“. The ⓘ of the layer shows the funnel of the whole city as a written sum, ending
in an estimate of light modules.

## Formula
1. A part of a building is a low flat part if its roof type is flat, its function is not excluded, and its height is
   from 2.5 m up to under 8 m.
2. A building is a roof candidate from 200 m² of low flat parts. Its area is the sum of those parts, its height the
   highest of them.
3. The candidate does not count if its representative point lies in no BORIS zone for housing or mixed use (zone rule
   as in `land`: development state B, use W or M). It does not count if the roof is under 3.2 m high. The first
   filter that fails names the reason, in this order.
4. Wall strip: a wall is a part of the same or of another building within 1 m of the low flat parts that is more than
   3 m higher than the highest of them. In front of the walls a strip of 2.5 m stays free: the low flat parts within
   2.5 m of the footprints of the walls. Its area is the share of the strip in the geometry, times the area of the
   roof (step 2). 2.5 m is the smallest Abstandsfläche of the Hessische Bauordnung (§ 6 Abs. 5 Satz 4 in the version
   of Baupaket I, 2025). The rest of the roof counts.
5. Funnel of the city: candidates − not in a housing zone − under 3.2 m − wall strips of the counted roofs = counted
   area.
6. Area: sum of the counted roofs, each without its wall strip, whose representative point lies in the area. A roof
   in no district drops out entirely, a counted roof in a district but in no Stadtteil is a FAIL.
7. Modules: counted area × 0.5 ÷ 25 m². The estimate is our own conclusion with two simple assumptions: half the area
   stays free for edge, paths and technology, one module needs 25 m². The written sum shows it rounded to hundreds.

## Why
Low flat roofs in housing areas may carry light modules for housing. The layer shows where they are many. The overlay
shows each roof and why it does or does not count. In front of a taller wall the building code keeps an Abstandsfläche
free. The map keeps the smallest one, 2.5 m, and counts the rest of the roof. Dropping the whole roof instead would
count about half the area (variants in the finding).

## Inputs
No datasets of other steps. Files: `sources/hessen/lod2/lod2_frankfurt_parts.csv.gz` (one row per building part of the
3D-Gebäudemodell LoD2 Hessen, Lieferung 26.6.2026) and `lod2_frankfurt_gemarkungen.csv` (counts and delivery date per
Gemarkung), the pages of the BORIS WFS in `sources/hessen/boris/` (zones of 1.1.2024), Stadtbezirke and Stadtteile in
`sources/frankfurt/geodata/`, the monitoring table that joins the Stadtbezirke into the 114 districts, the reference
buildings `reference/flat_roofs_reference.csv` and the synopsis of the Hessische Bauordnung
`sources/other/2025_HBO_Synopse_Baupaket_I.pdf` (only for the check of the 2.5 m).

## Output
`flat_roofs_by_district`, `flat_roofs_by_quarter`, `flat_roofs_city` (the counted area), `flat_roofs_overlays` (one
feature per candidate roof in a district, with `text` and `counts`), `flat_roofs_calc_examples` (the funnel as a written
sum), `flat_roofs_checks`.

## Checks
- Every Gemarkung holds all buildings of the delivery list (FAIL).
- One delivery date, 26.6.2026, and most footprints of 2020 (FAIL), as the texts say.
- Three buildings read by hand in the raw GML equal the extract in area (1 m²), height (0.1 m) and function (FAIL).
- Candidates minus the roofs out of a housing zone, the very low roofs and the wall strips equal the counted area, and
  districts and Stadtteile add up to it, to 1 m² (FAIL; a counted roof in no Stadtteil is named with its gml:id).
- More than 5 roofs in no district give WARN.
- No wall strip is below 0 or larger than its roof, to 0.01 m² (FAIL). The check text names the counted roofs with a
  strip and how many of them lose all of their area.
- The synopsis of Baupaket I still says „mindestens 2,50 m betragen“, built from `WALL_GAP_M` (FAIL). The old column
  says 3 m.

## Limits
- 857 buildings stand in two Gemarkungen and 9 in three (875 extra copies). The first copy is kept
  (`sources/README.md`).
- The AdV functions are coarse. A supermarket, a hall and a school look alike. Excluded are only transformers,
  greenhouses, churches, hospitals, towers, canopies and traffic structures.
- Most footprints date from 2020 (Lieferung 26.6.2026). Later buildings and demolitions are missing or still there.
- A BORIS zone is no Bebauungsplan. It shows the usual use. Same zone rule as `land` (development state B): 33 roofs in
  other W or M zones drop out.
- `measuredHeight` of a part counts from the lowest ground of the whole building (HVBG Produktbeschreibung, p. 7). On a
  slope a low part can read higher than it is.
- Statics, photovoltaics, greening and ownership of the roofs are unknown.
- The wall strip is the smallest Abstandsfläche. In front of a high wall the building code asks more (0.4 H). The
  map keeps 2.5 m everywhere, and the Unsicherheit says so. A wall is found by its footprint within 1 m. A taller
  building further away gives no strip.
- The tooltip shows the whole roof area and the strip. The height in the tooltip is rounded down to 0.1 m.
- The module estimate is an own conclusion, not a measured value (two assumptions, Formula 7).
- The funnel of the build and the findings: `research/2026-11-10-flat-roofs.md`.
