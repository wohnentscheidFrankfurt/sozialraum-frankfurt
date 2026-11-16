"""Step protection: social preservation per cell and area, statute names per area, the overlays and the checks."""
from __future__ import annotations

import pandas as pd

from pipeline.shared.core.areas import city_rows, per_area
from pipeline.shared.core.checks import check_wfs
from pipeline.shared.core.geometry import feature_collection, site_properties, site_properties_with_date
from pipeline.engine.datasets import (CELLS_2022, PROTECTION_BY_DISTRICT, PROTECTION_BY_QUARTER, PROTECTION_CELLS,
                                      PROTECTION_CHECKS, PROTECTION_CITY, PROTECTION_OVERLAYS)
from pipeline.shared.geography.sources import load_districts, load_quarters
from pipeline.shared.readers.gml import count_with_area, read_features
from pipeline.shared.readers.reference import read_column
from pipeline.use_cases.protection.checks import check_social_preservation
from pipeline.use_cases.protection.model import inside, names_by_area, protection_values
from pipeline.use_cases.protection.sources import DECIDED, IN_FORCE, read_social_preservation, read_townscape
from pipeline.engine.steps import Context, Step, write_checks
from pipeline.shared.zensus.cells import inner_cells


def run(ctx: Context) -> None:
    s, c = ctx.store, ctx.config
    in_force, in_procedure = c.SOCIAL_PRESERVATION_GML, c.SOCIAL_PRESERVATION_PENDING_GML
    features_in_force, features_in_procedure = read_features(in_force), read_features(in_procedure)
    valid, pending = read_social_preservation(features_in_force), read_social_preservation(features_in_procedure)
    town, town_pending = read_townscape(features_in_force, IN_FORCE), read_townscape(features_in_procedure, DECIDED)
    cells = inner_cells(s)
    flags = pd.DataFrame({"cell_id": cells["cell_id"],
                          "in_social_preservation": inside(valid, cells["x25832"].to_numpy(),
                                                           cells["y25832"].to_numpy()).astype(int)})
    s.write(PROTECTION_CELLS, flags)
    cells_in = cells.merge(flags, on="cell_id", how="left")
    groups = {"social_preservation_names": valid, "social_preservation_pending_names": pending,
              "townscape_names": town, "townscape_pending_names": town_pending}
    for level, areas, dataset in (("district", load_districts(c.DISTRICTS_GML, c.MONITORING_CSV), PROTECTION_BY_DISTRICT),
                                  ("quarter", load_quarters(c.QUARTERS_GML), PROTECTION_BY_QUARTER)):
        names = names_by_area(areas, level, groups).rename(columns={level: "id"})
        s.write(dataset, names.merge(per_area(cells_in, level, lambda key, g: protection_values(g)), on="id", how="left"))
    s.write(PROTECTION_CITY, city_rows(protection_values(cells_in)))
    s.write(PROTECTION_OVERLAYS, {
        "social_preservation": feature_collection((site_properties(x), x.geom, 2.0) for x in valid),
        "social_preservation_pending": feature_collection((site_properties(x), x.geom, 2.0) for x in pending),
        "townscape": feature_collection((site_properties_with_date(x), x.geom, 2.0) for x in town),
        "townscape_pending": feature_collection((site_properties_with_date(x), x.geom, 2.0) for x in town_pending)})
    expected = set(read_column(c.EXPECTED_SOCIAL_PRESERVATION_CSV, "project_no"))
    write_checks(s, PROTECTION_CHECKS,
                 [check_social_preservation({x.project_no for x in valid}, expected),
                  *[check_wfs(path.name, count_with_area(features)) for path, features in
                    ((in_force, features_in_force), (in_procedure, features_in_procedure))]])
    ctx.log(f"{len(valid)} social preservation areas in force, {len(pending)} pending")
    ctx.log(f"{len(town)} townscape statutes in force, {len(town_pending)} pending")


STEP = Step("protection", run, needs=(CELLS_2022,),
            makes=(PROTECTION_CELLS, PROTECTION_BY_DISTRICT, PROTECTION_BY_QUARTER, PROTECTION_CITY,
                   PROTECTION_OVERLAYS, PROTECTION_CHECKS))
