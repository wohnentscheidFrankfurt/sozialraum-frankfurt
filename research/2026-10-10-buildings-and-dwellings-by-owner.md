# Buildings and dwellings by owner: Zensus 2011 and 2022

As of 10 Oct 2026. Sources in `sources/05 Eigentümerstruktur/`: 3000G-2007 and 4000W-2013 (by size), 3000G-2001,
4000W-1011. Labels: [belegt] = printed in the source; [eigene Auswertung] = counted by us.

## Question

"Statistik aktuell 13/2024" gives 8,434 buildings (10.7 %) for the municipality and 5,034 (6.4 %) for private
companies. Companies own about 19 % of the dwellings. Do companies own the larger buildings?

## Answer: yes

- The numbers of "Statistik aktuell" are residential buildings without dormitories, 2022 (79,004). The 5,034 are only
  "privatwirtschaftliche Wohnungsunternehmen"; "andere privatwirtschaftliche Unternehmen" own 1,435 more. Both
  numbers are reproduced exactly from 3000G-2007 by kind of building (`GEBAT3`, fetched on 10 Oct 2026, not stored in
  `sources/`). [belegt]
- On the base of the map (buildings with residential space):

| Group | Buildings 2011 → 2022 | Dwellings 2011 → 2022 | Dwellings per building |
|---|---|---|---|
| Private companies | 4,522 → 6,796 (5.8 → 8.4 %) | 37,847 → 76,340 (10.4 → 19.0 %) | 8.4 → 11.2 |
| Public | 9,647 → 9,085 (12.5 → 11.3 %) | 72,650 → 75,209 (19.9 → 18.7 %) | 7.5 → 8.3 |
| Private persons | 47,290 → 50,138 (61.1 → 62.1 %) | 131,689 → 134,116 (36.0 → 33.3 %) | 2.8 → 2.7 |
| WEG | 13,088 → 12,146 (16.9 → 15.1 %) | 101,464 → 98,759 (27.8 → 24.5 %) | 7.8 → 8.1 |
| Cooperatives | 1,937 → 1,795 (2.5 → 2.2 %) | 13,390 → 12,932 (3.7 → 3.2 %) | 6.9 → 7.2 |
| Non-profit organisations | 970 → 721 (1.3 → 0.9 %) | 8,359 → 5,471 (2.3 → 1.4 %) | 8.6 → 7.6 |

Counts [belegt]; shares (base: sum of the groups), ratios [eigene Auswertung].

- Company buildings grew by 50 %, company dwellings by 102 %. [eigene Auswertung]
- Buildings with 13 or more dwellings: companies own 15.6 % of their dwellings in 2011 and 32.2 % in 2022. [eigene
  Auswertung]
- Of the company growth (+38,493 dwellings), +25,277 lie in buildings with 13 or more dwellings (66 %), +11,346 in
  buildings with 7 to 12. [eigene Auswertung]

## Caveats

- The Zensus counts the owner of the building, not of the single dwelling. [belegt]
- The Zensus does not say whether a building was sold or only classified differently. [eigene Einschätzung]
- Dormitories fell from 721 to 155 buildings; this is likely a change of classification. [eigene Einschätzung]
- The brochure of 2013 (GWZ 2011, `sources/02 Gebäude- und Wohnungsbestand/statistik.aktuell 11-2013 …`) uses
  preliminary values and residential buildings only. [belegt]

## Consequences

- The view "2011–2022" shows buildings and dwellings side by side (spec
  `docs/specs/2026-10-10-ownership-buildings-design.md`).
- Covered for statements: "2022 gehörten privaten Unternehmen 8 % der Häuser, aber 19 % der Wohnungen." and "In
  Häusern ab 13 Wohnungen gehört Unternehmen jede dritte Wohnung." [belegt by the Zensus counts]
