"""Step assembly: joins the area tables of all use cases per level, collects the city values, checks the joined
result (population per district, ⓘ protocols)."""
from __future__ import annotations

import pandas as pd

from pipeline.map.assembly.catalog import (breakdown_numbers, catalog_numbers, map_catalog, map_catalog_payload,
                                           merge_examples, map_overlays, map_sources)
from pipeline.map.assembly.checks import check_info_protocols, check_population
from pipeline.map.assembly.model import add_small, join_area_table
from pipeline.shared.core.areas import per_area
from pipeline.shared.core.city_values import city_values_frame
from pipeline.shared.core.stats import STORED_DECIMALS
from pipeline.shared.core.texts import LANGUAGES
from pipeline.engine.datasets import (ASSEMBLY_CHECKS, BUILDING_GAPS_CALC_EXAMPLES, CELLS_2022, CITY_VALUES,
                                      CONSTRUCTION_YEAR_CALC_EXAMPLES,
                                      ELECTION_LISTS, FLAT_ROOFS_CALC_EXAMPLES, HOUSING_CALC_EXAMPLES,
                                      INDICATORS_DISTRICTS,
                                      INDICATORS_QUARTERS, MAP_CATALOG, OWNERSHIP_CALC_EXAMPLES, OWNERSHIP_RANGES,
                                      SOCIAL_HOUSING_CALC_EXAMPLES, SURVEY_CALC_EXAMPLES, SURVEY_HALF_WIDTHS, ending,
                                      in_language, languages)
from pipeline.shared.geography.sources import load_districts, load_quarters
from pipeline.engine.download import fetch_date
from pipeline.engine.steps import Context, Step, write_checks
from pipeline.shared.zensus.cells import inner_cells
from pipeline.use_cases.survey.catalog import T as SURVEY_TEXTS, half_width_numbers

# The area tables are German-named datasets and joined once. Their only text column is `*_SHARED` of
# `monitoring_by_district`, which monitoring writes per language; the HTML step takes it per language from
# `monitoring_by_district.<lang>` (phase 2). Every other column is a number.
AREA_TABLES = {"district": ending("_by_district"), "quarter": ending("_by_quarter")}
CITY_FILES = ending("_city")
EXAMPLE_FILES = (OWNERSHIP_CALC_EXAMPLES, HOUSING_CALC_EXAMPLES, CONSTRUCTION_YEAR_CALC_EXAMPLES,
                 SOCIAL_HOUSING_CALC_EXAMPLES, SURVEY_CALC_EXAMPLES,
                 FLAT_ROOFS_CALC_EXAMPLES, BUILDING_GAPS_CALC_EXAMPLES)


def run(ctx: Context) -> None:
    s, c = ctx.store, ctx.config
    cells = inner_cells(s)
    districts, quarters = load_districts(c.DISTRICTS_GML, c.MONITORING_CSV), load_quarters(c.QUARTERS_GML)
    base = {"district": pd.DataFrame([{"id": d.id, "name": d.name, "quarter": d.quarter, "survey_area": d.survey_area}
                                      for d in districts]),
            "quarter": pd.DataFrame({"id": [q.id for q in quarters], "name": [q.name for q in quarters]})}
    out = {}
    for level, frame in base.items():
        frame = join_area_table(frame, per_area(cells, level, lambda key, g: {"POP": int(g["pop"].sum())}))
        for dataset in AREA_TABLES[level]:
            frame = join_area_table(frame, s.read(dataset))
        out[level] = frame
    out["district"] = add_small(out["district"])
    s.write(INDICATORS_DISTRICTS, out["district"].round(STORED_DECIMALS))
    s.write(INDICATORS_QUARTERS, out["quarter"].round(STORED_DECIMALS))
    rows = [{"indicator": "POP", "value": int(cells["pop"].sum()), "kind": "computed"}]
    rows += [row for dataset in CITY_FILES for row in s.read(dataset)]
    s.write(CITY_VALUES, city_values_frame(rows))
    ranges = {r["indicator"]: r for r in s.read(OWNERSHIP_RANGES)}
    fetched = fetch_date(c.FETCHED_CSV, c.WFS_FILES, c.SOURCES)
    checks = check_population(s.read(INDICATORS_DISTRICTS))
    for lang in LANGUAGES:
        # the protocols checked are the ones the map shows
        numbers = {"fetch_date": fetched, **catalog_numbers(ranges, lang), **breakdown_numbers(rows, lang),
                   **half_width_numbers(s.read(SURVEY_HALF_WIDTHS), SURVEY_TEXTS[lang])}
        examples = merge_examples(*(s.read(in_language(dataset, lang)) for dataset in EXAMPLE_FILES))
        catalog = map_catalog(numbers, s.read(ELECTION_LISTS)["lists"], examples, lang)
        overlays = map_overlays(numbers, lang)
        s.write(in_language(MAP_CATALOG, lang), {"catalog": map_catalog_payload(catalog), "overlays": overlays,
                                                 "sources": map_sources(numbers, lang)})
        checks.append(check_info_protocols(catalog, overlays, lang))
    write_checks(s, ASSEMBLY_CHECKS, checks)
    ctx.log(f"{len(out['district'])} districts ({int(out['district']['small'].sum())} small), "
            f"{len(out['quarter'])} quarters, {len(rows)} city values")


STEP = Step("assembly", run,
            needs=(CELLS_2022, *AREA_TABLES["district"], *AREA_TABLES["quarter"], *CITY_FILES, ELECTION_LISTS,
                   OWNERSHIP_RANGES, SURVEY_HALF_WIDTHS, *(ds for d in EXAMPLE_FILES for ds in languages(d))),
            makes=(INDICATORS_DISTRICTS, INDICATORS_QUARTERS, CITY_VALUES, *languages(MAP_CATALOG), ASSEMBLY_CHECKS))
