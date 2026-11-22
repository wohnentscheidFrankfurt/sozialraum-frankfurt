"""Step map: builds the single HTML file and the local exports."""
from __future__ import annotations

import datetime as dt
import json

from pipeline.shared.core import palette
from pipeline.shared.core.city_values import city_value_dict
from pipeline.shared.core.colours import NAMED
from pipeline.use_cases.candidates.catalog import CUSTOM_NOTE, TEMPLATES
from pipeline.use_cases.election.catalog import ELECTION_LAYERS
from pipeline.use_cases.land.catalog import T as LAND_TEXTS
from pipeline.use_cases.ownership_cells.catalog import GROUP_DATIVE
from pipeline.engine.datasets import (BUILDING_GAPS_OVERLAYS, CITY_VALUES, ELECTION_LISTS, FLAT_ROOFS_OVERLAYS,
                                      INDICATORS_DISTRICTS,
                                      INDICATORS_QUARTERS,
                                      LAND_OVERLAYS, MAP_CATALOG, NEW_CONSTRUCTION_VIEW, OWNERSHIP_GRID_CELLS,
                                      OWNERSHIP_HISTORY_VIEW, PROTECTION_OVERLAYS, RENT_BURDEN_VIEW)
from pipeline.shared.geography.sources import load_districts, load_quarters
from pipeline.map.html.model import (MAX_BYTES, area_collection, browser_properties, clean_value, json_for_html,
                                     render_html, round_estimates, rounded_geojson, with_cover_note,
                                     with_use_names)
from pipeline.map.html.sources import read_web
from pipeline.engine.steps import Context, Step


def run(ctx: Context) -> None:
    s, c = ctx.store, ctx.config
    election = s.read(ELECTION_LISTS)
    texts = s.read(MAP_CATALOG)  # written finished by assembly
    grid = s.read(OWNERSHIP_GRID_CELLS)
    protection, land = s.read(PROTECTION_OVERLAYS), s.read(LAND_OVERLAYS)
    flat_roofs = s.read(FLAT_ROOFS_OVERLAYS)
    building_gaps = s.read(BUILDING_GAPS_OVERLAYS)
    keep = browser_properties(texts["catalog"], TEMPLATES, election["lists"])
    districts, quarters = load_districts(c.DISTRICTS_GML, c.MONITORING_CSV), load_quarters(c.QUARTERS_GML)
    indicators = {"districts": s.read(INDICATORS_DISTRICTS), "quarters": s.read(INDICATORS_QUARTERS)}
    data = {
        "created": dt.date.today().strftime("%-d.%-m.%Y"),
        "catalog": texts["catalog"],
        "ramp_teal": NAMED["teal"],  # the candidates colour the areas by it (web/js/02_candidates.js)
        "hit_border": palette.HIT_BORDER,  # and draw the border of a hit, in the map and its legend
        "lists": election["lists"],
        "election_layers": list(ELECTION_LAYERS),
        "templates": TEMPLATES,
        "custom_note": CUSTOM_NOTE,  # under the own query (web/js/02_candidates.js)
        "city_values": {k: clean_value(v) for k, v in city_value_dict(s.read(CITY_VALUES)).items()},
        "districts": area_collection(districts, indicators["districts"], keep),
        "quarters": area_collection(quarters, indicators["quarters"], keep),
        "social_preservation": protection["social_preservation"],
        "social_preservation_pending": protection["social_preservation_pending"],
        "townscape": protection["townscape"],
        "townscape_pending": protection["townscape_pending"],
        "pending_plans": land["pending_plans"],
        "land_value": with_use_names(land["land_value"], LAND_TEXTS["de"]),
        "flat_roofs": flat_roofs["flat_roofs"],
        "building_gaps": building_gaps["building_gaps"],
        "grid_groups": grid["groups"],
        "grid_dative": GROUP_DATIVE["de"],  # the group names of the grid tooltip (web/js/04_overlays.js)
        "grid_cells": {"scale": grid["scale"], "rows": grid["rows"]},
        "sources": texts["sources"],
        "overlays": texts["overlays"],
        "history": s.read(OWNERSHIP_HISTORY_VIEW),
        "new_construction": s.read(NEW_CONSTRUCTION_VIEW),
        "rent_burden": s.read(RENT_BURDEN_VIEW),
    }
    template, parts = read_web(c.WEB)
    html = with_cover_note(render_html(template, parts, data), data["created"])
    size = len(html.encode("utf-8"))
    if size > MAX_BYTES:
        sizes = {k: len(json_for_html(v)) // 1024 for k, v in data.items()}
        raise SystemExit(f"HTML is {size / 1e6:.1f} MB, the limit is 5 MB. Size in KB: {sizes}")
    c.OUTPUT.mkdir(parents=True, exist_ok=True)
    target = c.OUTPUT / c.MAP_NAME
    target.write_text(html, encoding="utf-8")
    c.EXPORTS.mkdir(parents=True, exist_ok=True)  # stays local, never goes to the target
    for key, areas in (("districts", districts), ("quarters", quarters)):  # every column, not only the payload's
        round_estimates(indicators[key]).to_csv(c.EXPORTS / f"indicators_{key}.csv", index=False)
        geojson = rounded_geojson(area_collection(areas, indicators[key]))
        (c.EXPORTS / f"{key}.geojson").write_text(json.dumps(geojson, ensure_ascii=False), encoding="utf-8")
    ctx.log(f"{target.name}: {size / 1e6:.2f} MB")


STEP = Step("map", run, needs=(ELECTION_LISTS, CITY_VALUES, INDICATORS_DISTRICTS, INDICATORS_QUARTERS,
                                OWNERSHIP_GRID_CELLS, OWNERSHIP_HISTORY_VIEW, NEW_CONSTRUCTION_VIEW, RENT_BURDEN_VIEW,
                                LAND_OVERLAYS, PROTECTION_OVERLAYS, FLAT_ROOFS_OVERLAYS, BUILDING_GAPS_OVERLAYS,
                                MAP_CATALOG))
