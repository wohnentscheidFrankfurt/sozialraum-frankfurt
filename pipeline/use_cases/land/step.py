"""Step land: land value per cell and area, pending plans per area, the overlays and the checks."""
from __future__ import annotations

import pandas as pd

from pipeline.shared.core.areas import city_rows, per_area
from pipeline.shared.core.checks import check_wfs
from pipeline.shared.core.geometry import feature_collection, site_properties
from pipeline.engine.datasets import (CELLS_2022, LAND_BY_DISTRICT, LAND_BY_QUARTER, LAND_CHECKS, LAND_CITY,
                                      LAND_OVERLAYS, LAND_VALUE_CELLS)
from pipeline.shared.geography.sources import load_districts, load_quarters
from pipeline.shared.readers.gml import count_with_area, read_features
from pipeline.use_cases.land.checks import check_values
from pipeline.use_cases.land.model import land_value_at, land_values, pending_plans_by_area, with_values
from pipeline.use_cases.land.sources import read_pending_plans, read_values, read_zones
from pipeline.engine.steps import Context, Step, write_checks
from pipeline.shared.zensus.cells import inner_cells


def run(ctx: Context) -> None:
    s, c = ctx.store, ctx.config
    zones_2024, boris_values = read_zones(c.BORIS_DIR), read_values(c.BORIS_VALUES_CSV)
    zones = with_values(zones_2024, {number: value for number, (value, _) in boris_values.items()})
    cells = inner_cells(s)
    values = pd.DataFrame({"cell_id": cells["cell_id"],
                           "land_value": land_value_at(cells["x25832"], cells["y25832"], zones)})
    s.write(LAND_VALUE_CELLS, values)
    merged = cells.merge(values, on="cell_id", how="left")
    features = read_features(c.PENDING_PLANS_GML)
    plans = read_pending_plans(features)
    for level, areas, dataset in (("district", load_districts(c.DISTRICTS_GML, c.MONITORING_CSV), LAND_BY_DISTRICT),
                                  ("quarter", load_quarters(c.QUARTERS_GML), LAND_BY_QUARTER)):
        pending = pending_plans_by_area(areas, level, plans).rename(columns={level: "id"})
        s.write(dataset, pending.merge(per_area(merged, level, lambda key, g: land_values(g)), on="id", how="left"))
    s.write(LAND_CITY, city_rows(land_values(merged)))
    s.write(LAND_OVERLAYS, {
        "pending_plans": feature_collection((site_properties(x), x.geom, 5.0) for x in plans),
        "land_value": feature_collection(({"land_value": z.value, "use": z.use, "building": z.building}, z.geom, 10.0) for z in zones)})
    write_checks(s, LAND_CHECKS, [check_wfs(c.PENDING_PLANS_GML.name, count_with_area(features)),
                                  check_values(zones_2024, boris_values)])
    ctx.log(f"{len(zones)} of {len(zones_2024)} residential and mixed zones with a value of 2026, {len(plans)} pending plans")


STEP = Step("land", run, needs=(CELLS_2022,),
            makes=(LAND_VALUE_CELLS, LAND_BY_DISTRICT, LAND_BY_QUARTER, LAND_CITY, LAND_OVERLAYS, LAND_CHECKS))
