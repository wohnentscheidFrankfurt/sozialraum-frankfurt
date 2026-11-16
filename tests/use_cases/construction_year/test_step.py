
import pandas as pd
import pytest

from pipeline import config
from pipeline.use_cases.construction_year import step
from pipeline.use_cases.construction_year.step import STEP
from pipeline.engine.datasets import (CELLS_2011_DWELLINGS, CELLS_2022, CONSTRUCTION_YEAR_BY_DISTRICT,
                                      CONSTRUCTION_YEAR_BY_QUARTER, CONSTRUCTION_YEAR_CALC_EXAMPLES,
                                      CONSTRUCTION_YEAR_CHECKS, CONSTRUCTION_YEAR_CITY)


def _run(tmp_path, run_step):
    cells = pd.DataFrame({"cell_id": ["a", "b", "e"], "edge": [0, 0, 1], "district": ["d1", "d2", None],
                          "quarter": ["Gallus", "Gallus", None], "dwellings": [50, 150, 9]})
    cells_2011 = pd.DataFrame({"cell_id": ["a", "e"], "dw_total_2011": [40, 9], "dw_pre1919_2011": [10, 9],
                               "dw_1949_1978_2011": [20, 0]})  # cell b has no 2011 row; the edge cell does not count
    store, _ = run_step(tmp_path, STEP, {CELLS_2022: cells, CELLS_2011_DWELLINGS: cells_2011},
                        ZENSUS_4000W_1008=config.ZENSUS_4000W_1008)
    return store


def test_step_on_a_fake_store(tmp_path, run_step, monkeypatch):
    monkeypatch.setattr(step, "CALC_EXAMPLE_QUARTERS", dict.fromkeys(step.CALC_EXAMPLE_QUARTERS, "Gallus"))
    store = _run(tmp_path, run_step)
    d = store.read(CONSTRUCTION_YEAR_BY_DISTRICT).set_index("id")
    assert list(d.index) == ["d1", "d2"] and d.loc["d1", "HOU_PRE1919"] == pytest.approx(20.0)
    assert d.loc["d2", "HOU_PRE1919_DWELLINGS"] == 0
    q = store.read(CONSTRUCTION_YEAR_BY_QUARTER).set_index("id")
    assert list(q.index) == ["Gallus"] and q.loc["Gallus", "HOU_1949_1978"] == pytest.approx(10.0)
    assert q.loc["Gallus", "HOU_1949_1978_DWELLINGS"] == 20
    city = {r["indicator"]: r for r in store.read(CONSTRUCTION_YEAR_CITY)}
    assert set(city) == {"HOU_PRE1919", "HOU_1949_1978"}  # no counts
    assert city["HOU_PRE1919"]["value"] == pytest.approx(5.0) and city["HOU_PRE1919"]["kind"] == "computed"
    assert store.read(CONSTRUCTION_YEAR_CHECKS)


def test_step_writes_the_worked_examples(tmp_path, run_step, monkeypatch):
    monkeypatch.setattr(step, "CALC_EXAMPLE_QUARTERS", dict.fromkeys(step.CALC_EXAMPLE_QUARTERS, "Gallus"))
    store = _run(tmp_path, run_step)
    q = store.read(CONSTRUCTION_YEAR_BY_QUARTER).set_index("id")
    examples = store.read(CONSTRUCTION_YEAR_CALC_EXAMPLES)
    assert set(examples) == {"HOU_PRE1919", "HOU_1949_1978"}
    for kid, e in examples.items():
        assert e["area"] == "Gallus" and e["rows"][-1]["number"] == round(q.loc["Gallus", kid], 1), kid
    # no cap in the fake data: the 2011 count stays below the dwellings of 2022
    assert [r["number"] for r in examples["HOU_PRE1919"]["rows"]] == [10, 200, 5.0]


def test_step_fails_without_the_example_stadtteil(tmp_path, run_step):
    with pytest.raises(ValueError, match="no Stadtteil Nordend-Ost"):
        _run(tmp_path, run_step)
