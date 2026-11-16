import json

import pandas as pd
import pytest

from pipeline import config
from pipeline.engine.datasets import (CELLS_2011_BUILDINGS, CELLS_2011_DWELLINGS, CELLS_2022,
                                      PUBLIC_HOUSING_CHECKS, PUBLIC_HOUSING_QUARTERS)
from pipeline.use_cases.public_housing.step import STEP
from pipeline.shared.zensus.model import CLASSES, SIZES


def test_public_housing_step_on_a_fake_store(tmp_path, run_step):
    """Join of both 2011 extracts, secrecy gap over the inner cells, one row per quarter."""
    cells = pd.DataFrame([
        {"cell_id": "a", "edge": 0, "quarter": "Gallus", "dwellings": 100, "x25832": 0.0, "y25832": 0.0},
        {"cell_id": "b", "edge": 0, "quarter": "Bonames", "dwellings": 40, "x25832": 1000.0, "y25832": 0.0},
        {"cell_id": "e", "edge": 1, "quarter": None, "dwellings": 9, "x25832": 5000.0, "y25832": 0.0}])
    for k in CLASSES:
        cells[f"bld_{k}"] = 0
    for s in SIZES:
        cells[f"bld_size_{s}"] = 0
    cells.loc[0, ["bld_municipal", "bld_size_13_plus"]] = 5
    cells.loc[1, ["bld_person", "bld_size_1"]] = 40
    o11 = pd.DataFrame([{"cell_id": "a", **{f"dw_{k}_2011": 0 for k in CLASSES}, "dw_municipal_2011": 90, "dw_total_2011": 95}])
    b11 = pd.DataFrame([{"cell_id": "a", **{f"bld_{k}_2011": 0 for k in CLASSES}, **{f"bld_size_{s}_2011": 0 for s in SIZES},
                         "bld_municipal_2011": 5, "bld_size_13_plus_2011": 5}])
    sites = tmp_path / "sites.geojson"
    sites.write_text(json.dumps({"type": "FeatureCollection", "features": []}))
    store, _ = run_step(tmp_path, STEP, {CELLS_2022: cells, CELLS_2011_DWELLINGS: o11, CELLS_2011_BUILDINGS: b11},
                        ZENSUS_3000G_2007=config.ZENSUS_3000G_2007, ZENSUS_4000W_2013=config.ZENSUS_4000W_2013,
                        ZENSUS_4000W_1011=config.ZENSUS_4000W_1011, ABG_SITES_GEOJSON=sites,
                        ZENSUS_4000W=config.ZENSUS_4000W, CHECK_REFERENCE_CSV=config.CHECK_REFERENCE_CSV)
    q = store.read(PUBLIC_HOUSING_QUARTERS).set_index("quarter")
    assert list(q.index) == ["Bonames", "Gallus"]
    # 5 dwellings without owner in 2011 get the municipal share of 2022 (all): base 95; the cell grows from 95 to 100
    # dwellings, all municipal in both estimates: factor 100/95
    assert q.loc["Gallus", "fill_2011"] == pytest.approx(5) and q.loc["Gallus", "factor"] == pytest.approx(100 / 95)
    assert q.loc["Gallus", "public"] == pytest.approx(100)
    assert q.loc["Bonames", "public_value"] == 0
    assert store.read(PUBLIC_HOUSING_CHECKS)
