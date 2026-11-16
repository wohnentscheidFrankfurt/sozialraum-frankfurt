# QA of the layers „Lage“ and „Belastung und Bestand“ (17 Oct 2026)

Seven reviewer agents checked the layers against the real sources and the code. Labels: [belegt], [eigene Auswertung].
Decisions: `docs/decisions/2026-10-17-qa-situation-burden.md`.

## Construction year

- [belegt] The 2011 grid counts dormitories as dwellings, the 2022 grid does not. Cell `CRS3035RES100mN3002900E4222800`
  (Hausen): 2011 723 dwellings, 717 of them built 1949–1978; 2022 16 dwellings and 682 residents.
- [eigene Auswertung] Script `scripts/qa_construction_year_variants.py`, result `results/qa_construction_year_variants.txt`
  and two CSV per level.
- Variants for the share of the 2022 dwellings: V0 2011 class ÷ 2022 dwellings; V1 2011 class ÷ 2011 dwellings; V2
  class capped at the 2022 dwellings per cell; V3 class scaled by 2022 ÷ 2011 dwellings; V4 building share of the 2022
  grid.
- City, 1949–1978: V0 47.6 %, V1 51.0 %, V2 45.6 %, V3 44.0 %, V4 39.8 %. Table 4000W-1008 (2022): 47.1 %.
- City, before 1919: V0 16.5 %, V2 16.4 %, V4 19.7 %. Table: 16.6 %.
- Hausen, 1949–1978: V0 86.2 %, V1 71.4 %, V2 61.7 %, V3 59.4 %, V4 48.9 %.
- The map uses V2. It needs no building share and keeps the dwelling counts. The 2022 grid has the year of construction
  only for buildings, so V4 does not answer the question.
- [unsicher] V2 misses new dwellings in old buildings since 2011.

## Vacancy

- [belegt] In the grid „–“ means „Genau Null oder auf Null geändert“ (dataset description). Reading it as 0 gives 2.66 %
  for the city; the 1 km grid has 3.06 %, table 4000W-0001 3.1 %.
- [eigene Auswertung] Script `scripts/qa_vacancy_fill.py`, result `results/qa_vacancy_fill.txt` and a CSV per level.
- Filling the „–“ cells from the 1 km rate gives 3.08 % and, market-active, 1.84 % (1 km grid 1.82 %).
- Innenstadt 8.0 %. No area with 0.0 % market-active vacancy is left.
- Negative rest in 15 of 216 1 km cells (all vacancy) and 8 of 216 (market-active), 45.8 and 47.1 dwellings in total.
- The owner rate does not need the filling. City renters 79.93 % in the 100 m grid, table 79.9 %. The rest is negative
  in 65 of 216 1 km cells.
- [unsicher] Per area the filling spreads the rest of a 1 km cell evenly by dwellings.

## Open points of the QA

- The weights of the vacancy rates (all dwellings against residential buildings without dormitories) stay.
- The Zensus marks many 1 km values as uncertain (`KLAMMERN`). The map names this in the ⓘ.
