
import pandas as pd
import pytest

from pipeline import config
from pipeline.engine.datasets import (CELLS_2011_DWELLINGS, CELLS_2022, OWNERSHIP_CELLS, OWNERSHIP_CELLS_CHECKS,
                                      OWNERSHIP_GRID_CELLS)
from pipeline.use_cases.ownership_cells.step import STEP
from pipeline.shared.zensus.model import CLASSES


def test_step_on_a_fake_store_writes_cells_grid_and_checks(tmp_path, run_step):
    base = {f"bld_{k}": 0 for k in CLASSES}
    cells = pd.DataFrame([{"cell_id": "a", "edge": 0, "dwellings": 40, "x3035": 4226750.0, "y3035": 3000650.0, **base},
                          {"cell_id": "e", "edge": 1, "dwellings": 9, "x3035": 4226850.0, "y3035": 3000650.0, **base}])
    cells.loc[0, "bld_coop"] = 2
    cells_2011 = pd.DataFrame([{"cell_id": "a", **{f"dw_{k}_2011": 0 for k in CLASSES}}])
    store, _ = run_step(tmp_path, STEP, {CELLS_2022: cells, CELLS_2011_DWELLINGS: cells_2011},
                        ZENSUS_4000W=config.ZENSUS_4000W)
    assert store.read(OWNERSHIP_CELLS).set_index("cell_id").loc["a", "dw_coop"] == pytest.approx(40)
    grid = store.read(OWNERSHIP_GRID_CELLS)
    assert len(grid["rows"]) == 1 and grid["groups"][grid["rows"][0][4]] == "OWN_COOP"
    assert grid["rows"][0][5:] == [0, 0, 0, 2, 0, 0, 0]  # flag 0, two buildings of the coop
    assert [c["status"] for c in store.read(OWNERSHIP_CELLS_CHECKS)] == ["OK", "OK"]
