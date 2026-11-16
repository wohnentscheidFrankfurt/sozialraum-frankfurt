---
title: "Where is the largest potential to save heat? Sources of the heat planning and the year of construction"
---

As of 11 Oct 2026. Originals in `sources/10 Wärmeplanung/`. Spec of the map change:
`docs/specs/2026-10-11-construction-year-design.md`.

# 1. Result in short

- **No source gives the saving potential per area as numbers.** All maps are pictures in PDFs, or classes in a web
  map service. Copying values from a picture cannot be checked against the source. [belegt]
- **The published maps show savings per floor area, not amounts.** They favour areas with single-family houses. In
  amounts the picture can differ; no published source gives them. [offen]
- **Data are requested.** On 11.10.2026 the Klimareferat (kwp@stadt-frankfurt.de) and Mainova were
  asked for the boundaries of the quarters (Quartiere) and the absolute savings per quarter and scenario. [offen]
- **Meanwhile the map shows the year of construction.** "Altbau vor 1919" and "Nachkriegsbau 1949–1978" replace
  "Altbau vor 1949". Both count dwellings of the Zensus 2011. [eigene Auswertung]

# 2. Sources of the heat planning

| Source | As of | Spatial level | What it gives |
|---|---|---|---|
| Masterplan 100 % Klimaschutz (Fraunhofer IBP), figure 31, PDF page 44 (printed page 43) | 2015, data about 2010 | whole city | Heat demand by building type and age class. The axis says "MWh", but the values (up to about 460) only fit GWh. |
| Konzeptstudie (e-think), annex M 118/2024 AN2 | Nov 2023 | hectare raster, only as pictures (figure 18, p. 72) | Heat density and refurbishment costs per hectare; refurbishment rates by "Gebiete mit öffentlichem Wohnbau" and monument protection (tables 17–19). |
| Presentation of the potential analysis (Fraunhofer IFAM, Mainova) | 29.9.2025 | quarters, pictures | Slides 9–12: saving 2022–2045 per floor area, three scenarios, four classes. |
| Fachgutachten "Erstellung der kommunalen Wärmeplanung", final report, annex 1 of M 109/2026 | June 2026; adopted 1.10.2026 (§ 518) | 418 quarters plus one "Sammelquartier" per Stadtteil | Chapter 4.1.1 (p. 58–63) and figures 44–47: the same maps as the presentation. Figure 43: heat use today per quarter in GWh/a (absolute, five classes). The version "Fachgutachten August 2026" on klimaschutz-frankfurt.de has the same text page by page. |
| Wärmeportal (geoportal.frankfurt.de/waermeportal-frankfurt), WMS `KWP_2026` | metadata 23.9.2026 | quarters, building blocks | Layer `Potenzial_Waermeverbrauchsreduktion_2022_bis_2045` (not yet in the portal menu). A query per point gives only the class as text, for example "> 200 - 300 MWh/ha"; no number, no geometry. |

Facts of the final report (chapter 4.1):

- Three scenarios: refurbishment rate in 2045 of 1.4 %, 1.9 % and 2.8 % full-refurbishment equivalents (KfW 55).
  Heat use falls by 14 %, 18 % and 26 % up to 2045.
- Classes of the maps: ≤ 200, 200–300, 300–400, > 400 MWh/ha (per hectare of floor area). The text on p. 59 says
  kWh/(m²·a). Open: yearly value in 2045, or sum? Asked in the mail to the Klimareferat. [offen]
- Largest potential by the text: quarters with post-war buildings and little monument protection, for example
  Niederursel, Schwanheim, Bergen-Enkheim.
- The Sammelquartiere (low heat density, loose buildings at the edge) have no value.

The WMS layer holds only the scenario "Zielwert 1,4 %" (lowest refurbishment). In this scenario almost all quarters
fall into the two lowest classes. The metadata say: "Der Zugriff erfolgt über das Wärmeportal", "© Klimareferat",
public access restricted under INSPIRE Art. 13(1)(f). The service answers only with the referer of the portal. Using
it for the map is not covered.

# 3. Year of construction (now in the map)

Zensus 2011, 100 m grid, dwellings by year of construction (feature `BAUJAHR_MZ`). Zensus 2022 has the year of
construction in the grid only for buildings. Check against table 4000W-1008 (dwellings, Frankfurt, 2011):

| Dwellings 2011 | Grid | 4000W-1008 | Difference |
|---|---|---|---|
| Vor 1919 | 64,223 | 67,328 | −4.6 % |
| 1949–1978 | 185,741 | 187,254 | −0.8 % |
| All | 364,048 | 365,401 | −0.4 % |

The old stock barely changed up to 2022: Vor 1919 −0.8 %, 1949–1978 +1.3 % (4000W-1008).

Buildings or dwellings changes the picture:

- City shares: before 1919, 18 % of the buildings (2022) and 18 % of the dwellings (2011); 1949–1978, 37 % of the
  buildings and 51 % of the dwellings.
- Most dwellings 1949–1978 [eigene Auswertung]: Sachsenhausen-Süd und Flughafen 9,609 (62 %), Bockenheim 9,557 (46 %), Ostend 8,784
  (56 %), Niederrad 7,831 (58 %), Bornheim 7,123 (39 %). Highest share: Niederursel 75 %.
- By buildings, Bergen-Enkheim, Dornbusch, Griesheim and Schwanheim rise instead; Ostend and Niederrad fall back.
- Most dwellings before 1919 [eigene Auswertung]: Nordend-West 7,290 (42 %), Sachsenhausen-Nord 6,446 (37 %), Nordend-Ost 5,878 (42 %),
  Bornheim 5,267 (29 %), Bockenheim 4,760 (23 %).

The map divides the dwellings of the class in 2011 by all dwellings in 2022 (spec addendum 1, decision of the
user). Otherwise new quarters look old: with the 2011 base Niederrad-West showed "Nachkriegsbau 70 %", because the
2011 grid holds only 17 % of its dwellings of today; with the 2022 base it shows 11.9 %. City values of the map:
16.4 % and 47.6 %; table 4000W-1008 for 2022: 16.6 % and 47.1 % [belegt]. The shares in the lists above use the 2011
base (analysis before the decision).

Traps: "Vor 1919" also holds buildings before 1870 (half-timbered village centres). A building destroyed completely
and rebuilt counts with the year of rebuilding (Altstadt mostly 1949–1978). With the 2011 base, dwellings built since 2011 are missing.

Effect on the template "Milieuschutz-Kandidat" (option 1 of the user: Altbau vor 1919 instead of Altbau vor 1949):
full matches fall from 11 to 6 districts [eigene Auswertung]. Out: Bornheim, one Gallus district, Niederrad-Nord, Riederwald,
Sachsenhausen-Nord, Westend-Nord. In: a second Innenstadt district. Remaining: Bahnhofsviertel, Gallus,
Gutleutviertel, Innenstadt (two), Rödelheim-Ost.
