# Low flat roofs of Frankfurt

10 Nov 2026. Question: where do low flat roofs in housing areas exist that could carry light housing modules? The
layer `ROOF_FLAT` and the overlay „Niedrige Flachdächer“ answer it (`pipeline/use_cases/flat_roofs/README.md`).
Numbers come from `research/scripts/flat_roofs_breakdown.py`, result `research/results/2026-11-10-flat-roofs.txt`.

Answer: 1,773 roofs with 733,334 m² count, after a strip of 2.5 m in front of taller walls. That is 31 % of the area of
the 4,034 candidate roofs. The module estimate is about 14,667 modules (the map shows „~14.700“). It is an own
conclusion with two assumptions. Statics, photovoltaics, planning law and ownership are unknown.

## Data check

- Source: 3D-Gebäudemodell LoD2 Hessen (HVBG), Lieferung 26.6.2026. [belegt] (`sources/hessen/lod2/`)
- Way to the data: the download center names the package through its REST API. The package holds 59 Gemarkung ZIPs
  with GML and a txt each (540 MB, in `cache/lod2/`). [belegt]
- The counts of the 59 txt files equal the buildings in the GML: 231,040. [belegt]
- 857 buildings stand in two Gemarkungen and 9 in three: 875 extra copies, counted by gml:id over the 59 GML files of
  `cache/lod2/frankfurt_lod2.zip`. 231,040 − 875 = 230,165 buildings remain. The first copy is kept. Every other copy
  has the same function and parts. [eigene Auswertung]
- Years of `creationDate`: 2020 for 93 % of the buildings, 2021 for 7 %. The delivery is of 2026, the footprints are
  not. [eigene Auswertung]
- Interior rings: counting `<gml:interior>` in all 59 raw GML files of `cache/lod2/frankfurt_lod2.zip` gives 6 in all
  surfaces. The extract keeps the exterior rings of the GroundSurface only. [eigene Auswertung]
- Three buildings read by hand in the raw GML equal the extract (check `flat_roofs`). [belegt]

## Funnel of the build

| Step | Roofs | m² |
|---|---|---|
| Candidates (a building with at least 200 m² of low flat parts) | 4,034 | 2,331,546 |
| minus: representative point in no BORIS housing zone | 2,049 | 1,420,178 |
| minus: roof under 3.2 m | 212 | 91,616 |
| minus: strip of 2.5 m in front of a wall more than 3 m higher (a part of the same or of another building within 1 m) | 897 | 86,418 |
| Counted | 1,773 | 733,334 |

- The strip takes only area. None of the 897 counted roofs with a strip loses all of it. The smallest rest is 6.0 m².
  [eigene Auswertung]
- Modules: 733,334 m² × 0.5 ÷ 25 m² ≈ 14,667. The written sum of the map rounds to hundreds: „~14.700“.
  [eigene Auswertung]
- No roof lies outside all districts. [eigene Auswertung]
- With W and M zones of any development state, 33 more roofs with 18,886 m² would count. The build keeps development
  state B only, as `land` does. [eigene Auswertung]

## Variants of the rule at taller walls

Counted m² of the city. The zone rule and the very low roofs are the same in all variants.

| Variant | Counted roofs | Counted m² |
|---|---|---|
| A: a roof next to a wall more than 3 m higher drops out as a whole (first version) | 858 | 368,571 |
| B: no rule at taller walls | 1,773 | 819,751 |
| C: strip of 3 m in front of the wall stays free | 1,773 | 716,804 |
| C: strip of 2.5 m in front of the wall stays free (build) | 1,773 | 733,334 |

- Why C with 2.5 m: it keeps the rest of the roof and takes as strip the smallest Abstandsfläche of the Hessische
  Bauordnung (§ 6 Abs. 5 Satz 4 in the version of Baupaket I, `sources/other/2025_HBO_Synopse_Baupaket_I.pdf`).
  [belegt]
- Variant A also counted a taller part of the same building that does not touch the roof. Variant C counts only
  walls within 1 m. [eigene Auswertung]

## Candidates by BORIS zone class

BORIS `art` at the representative point of the roof. Housing is W or M with development state B, as in the build.

| Class | Roofs | m² | Counted roofs | Counted m² |
|---|---|---|---|---|
| Housing (W, M) | 1,985 | 911,368 | 1,773 | 733,334 |
| Gemeinbedarf (GB) | 269 | 157,712 | 0 | 0 |
| Commerce (G, GE, GI) | 1,549 | 1,126,898 | 0 | 0 |
| Other | 231 | 135,568 | 0 | 0 |

- Commerce holds 48 % of the candidate area and counts for nothing. Reason: a zone for commerce is no housing zone.
  [eigene Auswertung]
- Gemeinbedarf holds schools, offices and the like. It stays outside by the same rule. Whether a module fits there is
  a planning question. [offen]

## Candidates by AdV function

Roofs in housing zones (all candidates in `research/results/2026-11-10-flat-roofs.txt`). Counted m² without the wall
strips:

| Function | Roofs | m² | Counted roofs | Counted m² |
|---|---|---|---|---|
| Gebäude für Wirtschaft oder Gewerbe | 642 | 335,734 | 611 | 276,409 |
| Gebäude für öffentliche Zwecke | 587 | 268,257 | 571 | 245,489 |
| Wohngebäude | 672 | 263,121 | 554 | 191,143 |
| Gebäude zum Parken | 73 | 36,930 | 27 | 14,636 |
| Parkhaus | 5 | 4,006 | 4 | 2,604 |
| other functions | 6 | 3,320 | 6 | 3,053 |

- Buildings for commerce carry 38 % of the counted area, buildings for public purposes 33 %. [eigene Auswertung]
- Excluded functions: transformers, greenhouses, churches, hospitals, towers, canopies and traffic structures.

## Traps

- The AdV functions are coarse. A supermarket, a hall and a school look alike. [belegt]
- A BORIS zone is no Bebauungsplan. It shows the usual use. [belegt]
- `measuredHeight` of a part counts from the lowest ground of the whole building (HVBG Produktbeschreibung, p. 7).
  On a slope a low part can read higher than it is. [belegt]
- The footprints are mostly of 2020. Later buildings and demolitions are missing or still there. [unsicher]
- The strip of 2.5 m is the smallest Abstandsfläche. In front of a high wall the building code asks 0.4 H. [belegt]
- Statics, photovoltaics, greening, Denkmal status and ownership of a roof are unknown. [offen]

## Open questions of the prototype handoff

- Statics: can light timber modules stand where a masonry storey fails? A structural engineer has to judge. Parking
  deck tops may hold reserves. [offen]
- Photovoltaics and greening: compare with the Solarkataster Hessen. Flat roofs compete with solar use. [offen]
- Planning law: Bebauungspläne in planAS, Flächennutzungsplan, plan information of the Regionalverband. [offen]
- Denkmalschutz. [offen]
- Ownership: public buildings are probably often municipal. The Regionalverband once counted up to 5,000 dwellings on
  supermarket sites in Rhein-Main; ask whether the list exists. [offen]
- Site visits: look at three to five candidates, as with the Baulücken. [offen]
- Access: entrance and crane. [offen]
