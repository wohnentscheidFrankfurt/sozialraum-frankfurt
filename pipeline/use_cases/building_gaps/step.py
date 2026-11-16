"""Step building_gaps: counted building gaps per area, the overlay of the drawn gaps, the funnel as a written sum and
the checks."""
from __future__ import annotations

import pandas as pd

from pipeline.engine.datasets import (BUILDING_GAPS_BY_DISTRICT, BUILDING_GAPS_BY_QUARTER, BUILDING_GAPS_CALC_EXAMPLES,
                                      BUILDING_GAPS_CHECKS, BUILDING_GAPS_CITY, BUILDING_GAPS_OVERLAYS)
from pipeline.engine.steps import Context, Step, write_checks
from pipeline.shared.core.areas import city_rows
from pipeline.shared.core.calc_example import example_payload
from pipeline.shared.core.geometry import feature_collection
from pipeline.shared.geography.sources import load_districts, load_quarters
from pipeline.use_cases.building_gaps.catalog import funnel_calc_example, gap_text
from pipeline.use_cases.building_gaps.checks import (check_as_of, check_cover, check_examples, check_funnel,
                                                     check_known, check_parcels, check_unassigned, check_verdicts)
from pipeline.use_cases.building_gaps.model import SIMPLIFY_M, area_values, find_gaps, funnel, judge
from pipeline.use_cases.building_gaps.sources import (kz_text, read_buildings, read_cover, read_landuse, read_meta,
                                                      read_parcels, read_verdicts, read_zones)


def run(ctx: Context) -> None:
    s, c = ctx.store, ctx.config
    parcels = read_parcels(c.ALKIS_PARCELS_CSV)
    gaps, geometry_counts = find_gaps(parcels, read_buildings(c.ALKIS_BUILDINGS_CSV),
                                      read_landuse(c.ALKIS_LANDUSE_CSV))
    cover, verdicts = read_cover(c.BUILDING_GAPS_COVER_CSV), read_verdicts(c.BUILDING_GAPS_REFERENCE_CSV)
    candidates = judge(gaps, read_zones(c.BORIS_DIR), cover, verdicts)
    by_district, by_quarter, outside, no_quarter = area_values(
        candidates, load_districts(c.DISTRICTS_GML, c.MONITORING_CSV), load_quarters(c.QUARTERS_GML))
    f = funnel(geometry_counts, candidates)
    drawn = [x for x in candidates if x.drawn]
    s.write(BUILDING_GAPS_BY_DISTRICT, by_district)
    s.write(BUILDING_GAPS_BY_QUARTER, by_quarter)
    s.write(BUILDING_GAPS_CITY, city_rows({"GAP_AREA": f["counted_m2"]}))
    s.write(BUILDING_GAPS_OVERLAYS, {"building_gaps": feature_collection(
        ({"text": gap_text(x, kz_text(x.gap.kz)), "counts": int(x.counts)}, x.gap.geom, SIMPLIFY_M) for x in drawn)})
    s.write(BUILDING_GAPS_CALC_EXAMPLES, {"GAP_AREA": example_payload(funnel_calc_example(f))})
    reference = pd.read_csv(c.BUILDING_GAPS_PARCELS_CSV, dtype={"gml_id": str, "kz": str})
    known = pd.read_csv(c.BUILDING_GAPS_KNOWN_CSV, dtype=str, keep_default_na=False)
    examples = pd.read_csv(c.BUILDING_GAPS_EXAMPLES_CSV, dtype={"category": str})
    meta = read_meta(c.ALKIS_META_CSV)
    write_checks(s, BUILDING_GAPS_CHECKS, [
        check_as_of(meta), check_parcels(parcels, reference), check_cover(gaps, cover, meta),
        check_verdicts(candidates, verdicts), check_known(gaps, candidates, known, set(parcels["gml_id"])),
        check_funnel(f, by_district, by_quarter, no_quarter), check_unassigned(outside), check_examples(examples)])
    ctx.log(f"{f['parcels']:,} parcels, {len(gaps)} gaps after the geometry, {len(drawn)} drawn, "
            f"{sum(x.verdict is None for x in drawn)} of them without a verdict, {f['counted']} counted "
            f"({f['counted_m2']:,.0f} m²), {len(outside)} drawn in no district")


STEP = Step("building_gaps", run, needs=(),
            makes=(BUILDING_GAPS_BY_DISTRICT, BUILDING_GAPS_BY_QUARTER, BUILDING_GAPS_CITY, BUILDING_GAPS_OVERLAYS,
                   BUILDING_GAPS_CALC_EXAMPLES, BUILDING_GAPS_CHECKS))
