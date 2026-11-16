# The Zensus 2022 grid overstates the living space per resident

As of 12 Oct 2026. Decision D6 of the formula review. Label: [eigene Auswertung].

- The grid mean of the living space per resident (weighted by residents) lies about a fifth above the Zensus table.
- It does so for Frankfurt (47.6 m² against 38.3 m²) and for Germany (56.2 m² against 46.3 m²).
- The aggregation of the map is right. Rent and share of renters from the same grid match their tables exactly.
- The cause lies in the source. The data description defines the same ratio as the table; a mean per dwelling instead
  of per person would explain the gap. Not provable.
- The user decided: the doubt stays, so the layer „Wohnfläche je Kopf“ (`HOU_SPACE`) is removed.

| Value | Map (grid) | Zensus table | Grid ÷ table |
|---|---|---|---|
| Mieteranteil, Frankfurt | 79.92 % | 100 − 20.1 = 79.9 % (4000W-0001) | 1.000 |
| Miete im Bestand, Frankfurt | 10.583 €/m² | 10.58 €/m² (4000W-0004) | 1.000 |
| Wohnfläche je Bewohner, Frankfurt | 47.6 m² | 38.3 m² (1000A-0004) | 1.242 |
| Wohnfläche je Bewohner, Germany (10-km grid) | 56.2 m² | 46.3 m² | 1.214 |

Cross-check Frankfurt: Wohnfläche je Haushalt 73.7 m² (5000H-0002) ÷ Haushaltsgröße 1.9 (5000H-0001) = 38.8 m². The
city building file gives 39.8 m². Both fit the table, not the grid.

Mieteranteil and Miete im Bestand stay. Their city values are checked against the tables (2 % relative) and the ⓘ
shows the table value as „Abgleich“.

Sources: `sources/02 Gebäude- und Wohnungsbestand/` (tables 1000A-0004, 4000W-0001, 4000W-0004; 5000H values stand in the
script header). Script: `analyses/space_check.py`; output: `analyses/results/space_check.txt`. Decision protocol:
`docs/decisions/2026-10-11-formula-review.md`, section „D6 result“.
