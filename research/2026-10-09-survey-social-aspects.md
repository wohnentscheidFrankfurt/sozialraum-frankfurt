# Survey "Leben in Frankfurt 2025": social aspects and their way onto the map

As of 9 Oct 2026. Sources: `sources/01 Umfrage Leben in Frankfurt 2025/FU_5_Leben_in_Frankfurt_2025.pdf` (report,
91 pages, published 27 Apr 2026), `codebook-2025.pdf`, `leben-in-frankfurt_2025.csv` (microdata, 8,185 cases),
`Statistikportal-Exporte/`. Page numbers are the printed ones.

Labels: [belegt] = printed in the source; [eigene Auswertung] = counted by us; [unsicher]; [offen].

## User decision

The published survey is the truth, whether or not we can recount a number. The map uses the published survey values
as printed. Spec:
`docs/specs/2026-10-09-survey-areas-design.md`.

## 1. Social aspects in the report

### By survey area (13 areas)

| Figure (page) | Content | Values |
|---|---|---|
| 4.5 (p. 27) | Rent burden ratio: warm rent per household net income | Innenstadt III 26, Innenstadt II 27, Mitte-Nord 27, West 31, Nord-West 31, Kalbach/Riedberg 32, Nord-Ost 33 [belegt, text]; Innenstadt I, Bornheim/Ostend, Süd "29–29", Mitte-West, Nord, Ost "30–30" [belegt, legend only]; city 29 [belegt] |
| 4.11 (p. 31) | Would miss the neighbourhood very or rather much | 51 (Innenstadt I, West) to 82 (Innenstadt III); city 62 [belegt] |
| 5.5 (p. 37) | Commute under 30 minutes, employed only | 49 (Nord) to 75 (Innenstadt II) [belegt] |
| 6.3 (p. 45) | Feeling safe at night in the neighbourhood, four levels | safe 62 (Innenstadt I) to 87 (Kalbach/Riedberg, Innenstadt III) [belegt] |
| 8.8 (p. 59) | Will certainly vote in the local election 2026 | 53 (Innenstadt I, Mitte-West) to 71 (Innenstadt III) [belegt] |

The text of 4.5 adds averages: warm rent Kalbach/Riedberg 1,460 €, Nord-Ost 930 €; household net income Kalbach/
Riedberg and Innenstadt II 4,750 €, Nord-Ost, Ost and West 3,050 € [belegt].

### By social group, city only

- 4.1 Renting or owning by equivalised income: under 1,000 € more than nine in ten rent.
- 4.2 Living space per person by income: median 36 m²; under 1,000 € about half of it.
- 4.3 Overcrowding by income: city 21 %, under 1,000 € 57 %.
- 4.6 Felt housing cost burden: renters 54 % high (22 very, 32 rather), owners 38 %.
- 4.7 Rent increase since 2019 by landlord: public 91 %, cooperatives 90 %, private companies 88 %, individuals 63 %.
- 5.2 Means of transport by income (car under 1,000 €: 43 %).
- 3.3 Image of the administration by age; 8.9–8.11 eligibility and intention to vote by nationality and past vote.

### City only, socially relevant

- 7.3 (new in 2025): 28 % low trust in others; 12 % without enough support in problems; 14 % rather or very bad
  economic situation; 28 % get less than their fair share.
- 7.2 Affordable housing: 92 % important, 10 % done. Fighting poverty: 86 % important, 20 % done.
- 2.3 Biggest problems: expensive housing 21 %, homelessness 6 %, cost of living 5 %.

## 2. Checks

- The microdata, weighted with `weight`, reproduces 4.11, 5.5, 6.3 and 8.8 per survey area to the whole percent
  [eigene Auswertung]. A Statistikportal export (moving plans) matches too, including the counts of answers. So the
  weight holds per survey area.
- Abb. 4.5 cannot be recounted: the microdata has only the equivalised income in 6 classes, not the household
  income [belegt, codebook].
- Abb. 8.8 keeps "keine Angabe" and "weiß nicht" in the denominator (Mitte-West 53 %; with valid answers only it
  would be 65 %). Page 4 says "weiß nicht" is usually left out. Each figure has to be checked on its own.
- The report rounds in two ways. Per area in 4.11 it rounds the total (Innenstadt II 71.6 → 72). The city value in
  the text is the sum of rounded parts (37 + 25 = 62; the microdata gives 62.5).
- Legend classes: "62–63" means over 61 up to 63. The first number is not the lower bound. The last class ends at the
  largest value, shown rounded ("71–82" means over 70 up to 82.5). Read this way, all 13 counts of 4.11 lie in their
  class: Mitte-Nord, Nord-West and Nord (61.0, 61.3, 61.6) in "62–63", Süd, Mitte-West, Ost and Kalbach/Riedberg
  (63.0, 63.4, 63.5, 69.6) in "64–70" [eigene Auswertung]. So "29–29" in 4.5 means over 28 up to 29: rounded, these
  six values can be one point lower [unsicher].
- The western strip next to Innenstadt I in Abb. 4.5 belongs to Innenstadt II (Bockenheim). `Umfragebezirke.gml`:
  Innenstadt II reaches further west than Gallus. So Innenstadt I is in "29–29".
- All 114 districts lie to at least 98 % in one survey area. Bockenheim (82.5 % Innenstadt II, 17.5 % Mitte-West) and
  Praunheim (93 % Mitte-West, 7 % Nord-West) are split [eigene Auswertung].
- Update 9 Oct 2026, evening: every district lies to 100 % in one survey area (Abb. 1.1, geometry, monitoring
  column agree). By residents, 6 % of Bockenheim (district 343) lie in Mitte-West and 20 % of Praunheim (district
  426) in Nord-West [eigene Auswertung].
- Uncertainty per survey area at 50 %: ±3.8 to ±4.1 points in Tab. 9.5; with the design effect of the weights
  (1.13–1.29) ±4.1 to ±4.5 [eigene Auswertung].
- The map's old `LIF_BURDEN` counted renters and owners: city 50.6 % instead of 54 %, Kalbach/Riedberg 50.1 %
  instead of 63.3 % for renters (only 45 % rent there) [eigene Auswertung]. Fixed: `LIF_RENTER_BURDEN`.
- `LIF_RENT_RECENT` is an own estimate. In Kalbach/Riedberg 44 % of recent renters fall in the top class "1.400 € und
  mehr"; the code assumes 1,550 €.

## 3. What is on the map since 9 Oct 2026

User decision: the resolution of the figures is enough. Fewer derived numbers, fewer errors. The level "Umfragebezirke (13)"
shows two layers, each with the classes as printed: rent burden ratio (Abb. 4.5) and attachment to the neighbourhood
(Abb. 4.11). Counted values (renter burden, income, rent of new renters) are not on the map. The counts in section 2
stay as background.

Since 9 Oct 2026, evening (spec addendum 4): no level of its own. The two layers show on the districts;
every district shows the class of its survey area, and the tooltip names the survey area.

## 4. Open

- [offen] Whether Abb. 4.5 counts only renters. Not needed for the map.
- [offen] Not on the map yet: 5.5, 6.3, 8.8 and the questions of 7.3 per survey area. All except 7.3 are printed per
  area and recountable.
