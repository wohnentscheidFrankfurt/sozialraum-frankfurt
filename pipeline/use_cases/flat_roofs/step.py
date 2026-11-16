"""Step flat_roofs: low flat roofs per area, the overlay of the roofs, the funnel as a written sum and the checks."""
from __future__ import annotations

import pandas as pd

from pipeline.engine.datasets import (FLAT_ROOFS_BY_DISTRICT, FLAT_ROOFS_BY_QUARTER, FLAT_ROOFS_CALC_EXAMPLES,
                                      FLAT_ROOFS_CHECKS, FLAT_ROOFS_CITY, FLAT_ROOFS_OVERLAYS)
from pipeline.engine.steps import Context, Step, write_checks
from pipeline.shared.core.areas import city_rows
from pipeline.shared.core.calc_example import example_payload
from pipeline.shared.core.geometry import feature_collection
from pipeline.shared.geography.sources import load_districts, load_quarters
from pipeline.use_cases.flat_roofs.catalog import funnel_calc_example, roof_text
from pipeline.use_cases.flat_roofs.checks import (check_as_of, check_building_code, check_counts, check_funnel,
                                                  check_reference, check_unassigned, check_wall_strip)
from pipeline.use_cases.flat_roofs.model import SIMPLIFY_M, area_values, find_roofs, funnel
from pipeline.use_cases.flat_roofs.sources import (name_of, read_building_code, read_gemarkungen, read_parts,
                                                   read_zones)


def run(ctx: Context) -> None:
    s, c = ctx.store, ctx.config
    parts = read_parts(c.LOD2_PARTS_CSV)
    all_roofs = find_roofs(parts, read_zones(c.BORIS_DIR))
    by_district, by_quarter, outside, no_quarter = area_values(
        all_roofs, load_districts(c.DISTRICTS_GML, c.MONITORING_CSV), load_quarters(c.QUARTERS_GML))
    lost = {id(r) for r in outside}
    roofs = [r for r in all_roofs if id(r) not in lost]  # a roof in no district is neither counted nor drawn
    f = funnel(roofs)
    s.write(FLAT_ROOFS_BY_DISTRICT, by_district)
    s.write(FLAT_ROOFS_BY_QUARTER, by_quarter)
    s.write(FLAT_ROOFS_CITY, city_rows({"ROOF_FLAT": f["counted_m2"]}))
    s.write(FLAT_ROOFS_OVERLAYS, {"flat_roofs": feature_collection(
        ({"text": roof_text(r, name_of(r.use)), "counts": int(r.counts)}, r.geom, SIMPLIFY_M) for r in roofs)})
    s.write(FLAT_ROOFS_CALC_EXAMPLES, {"ROOF_FLAT": example_payload(funnel_calc_example(f))})
    gemarkungen = read_gemarkungen(c.LOD2_GEMARKUNGEN_CSV)
    reference = pd.read_csv(c.FLAT_ROOFS_REFERENCE_CSV, dtype={"building": str, "function": str})
    write_checks(s, FLAT_ROOFS_CHECKS, [
        check_counts(gemarkungen), check_as_of(gemarkungen, parts["created"]), check_reference(all_roofs, reference),
        check_funnel(f, by_district, by_quarter, no_quarter), check_unassigned(outside), check_wall_strip(roofs),
        check_building_code(read_building_code(c.HBO_SYNOPSIS_PDF))])
    ctx.log(f"{len(all_roofs)} candidates ({f['candidates_m2'] + sum(r.area_m2 for r in outside):,.0f} m²), "
            f"{len(outside)} in no district, {sum(r.counts for r in roofs)} counted ({f['counted_m2']:,.0f} m² after "
            f"{f['wall_m2']:,.0f} m² of wall strips, {f['modules']:,.0f} modules), {len(no_quarter)} counted in no "
            f"quarter")


STEP = Step("flat_roofs", run, needs=(),
            makes=(FLAT_ROOFS_BY_DISTRICT, FLAT_ROOFS_BY_QUARTER, FLAT_ROOFS_CITY, FLAT_ROOFS_OVERLAYS,
                   FLAT_ROOFS_CALC_EXAMPLES, FLAT_ROOFS_CHECKS))
