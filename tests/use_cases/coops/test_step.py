
import pandas as pd
import pytest

from pipeline import config
from pipeline.use_cases.coops.step import STEP
from pipeline.engine.datasets import CELLS_2011_DWELLINGS, CELLS_2022, COOPS_CHECKS, COOPS_QUARTERS, OWNERSHIP_CELLS
from pipeline.shared.zensus.model import CLASSES


def test_step_on_a_fake_store(tmp_path, run_step):
    cells = pd.DataFrame({"cell_id": ["a", "b", "e"], "edge": [0, 0, 1], "district": ["d1", "d2", None],
                          "quarter": ["Bornheim", "Harheim", None], "dwellings": [100, 50, 9]})
    for k in CLASSES:
        cells[f"bld_{k}"] = 0
    cells.loc[0, "bld_coop"] = 2
    ownership = pd.DataFrame({"cell_id": ["a", "b", "e"], "dw_coop": [40.0, 0.0, 9.0]})
    c2011 = pd.DataFrame({"cell_id": ["a"], **{f"dw_{k}_2011": [0] for k in CLASSES}, "dw_total_2011": [100]})
    c2011.loc[0, ["dw_coop_2011", "dw_person_2011"]] = [60, 30]
    store, _ = run_step(tmp_path, STEP, {CELLS_2022: cells, OWNERSHIP_CELLS: ownership, CELLS_2011_DWELLINGS: c2011},
                        ZENSUS_4000W=config.ZENSUS_4000W)
    q = store.read(COOPS_QUARTERS).set_index("quarter")
    assert q.loc["Bornheim", "coop_value"] == pytest.approx(64.0) and q.loc["Harheim", "coop_value"] == 0
    assert store.read(COOPS_CHECKS)
