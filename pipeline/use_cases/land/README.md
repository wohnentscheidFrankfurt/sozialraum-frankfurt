# land: „Bodenrichtwert“, „B-Plan im Verfahren“

## Shows
`LAND_VALUE` (layer, topic „Boden“) and `LAND_PENDING_PLAN` (profile, with `pending_plan_names`, topic „Planung“).
Districts and Stadtteile.
Overlays „Bodenrichtwerte“ and „B-Pläne im Verfahren“. Their `key` names are „Bodenrichtwertzonen“ and „B-Plan im
Verfahren“. The tooltips carry no plan codes.

## Formula
1. The zones are those of the WFS 2024 (only residential and mixed zones, building land). Each zone takes the value of
   1.1.2026 of the zone with the same number at its inner point. A zone whose number does not hold there in 2026 drops
   out: no overlay, no cell value.
2. Each cell gets the land value of the zone at its centre.
3. Area: median of the cells, weighted by residents.
4. B-Plan: yes when a pending plan covers at least 1 ha of the area.

## Why
Land values show where land is expensive. Pending development plans show where land may still suit
Erbbaurecht or Konzeptvergabe. The overlays show the zones and plans themselves.

## Inputs
`cells_2022`; files `sources/hessen/boris/`: the pages of the BORIS Hessen WFS (zones of 1.1.2024) and
`values_2026.csv` (value and Stichtag of 1.1.2026 per zone number, from the WMS `hboris_feature`, GetFeatureInfo at
the inner point of each zone),
`sources/frankfurt/geodata/planAS_bebauungsplaene_bplan_iv.gml` (planAS WFS),
Stadtbezirke and Stadtteile in `sources/frankfurt/geodata/`; the monitoring table
`sources/frankfurt/offices/Monitoring2024_Stadtbezirke_nach_Umfragebezirk.csv` joins the Stadtbezirke into the 114
districts.

## Output
`land_value_cells`, `land_by_district`, `land_by_quarter`, `land_city`, `land_overlays`, `land_checks`.

## Checks
- The WFS answer of the pending plans holds areas (FAIL on an empty answer or an error message).
- Every value used has the Stichtag 01.01.2026 (FAIL). More than 2 % of the zones without a value of 2026 give WARN.
  At the switch: 762 of 765 zones.

## Limits
- The WFS exists for 2020, 2022 and 2024 only (the address for 2026 answered 404 on 20.10.2026). The WMS of 2026 gives
  values, no geometry. So the zones keep their borders of 2024.
- Where a border moved and the zone kept its number, cells near the border keep the value of the old zone. A test on
  20.10.2026 asked the WMS at every inner cell: of 6,058 inner cells with a value in the build and in the WMS, 6
  differ (771 residents). All 45 Stadtteile and the city keep their median; one of 114 districts differs (252: 3,500
  instead of 3,600 €/m²). Scripts and results: `research/2026-10-20-land-values-2026.md`.
- Overlapping zones (for example houses and blocks of flats in one mixed area) give their mean, as before.
- All pending plans count, also plans for commerce.
