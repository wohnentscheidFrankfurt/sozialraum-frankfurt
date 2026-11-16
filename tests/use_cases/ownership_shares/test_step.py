from types import SimpleNamespace

import pandas as pd
import pytest

from pipeline import config
from pipeline.use_cases.ownership_shares.catalog import EXAMPLES
from pipeline.engine.datasets import (CELLS_2022, COOPS_QUARTERS, OWNERSHIP_CALC_EXAMPLES, OWNERSHIP_CELLS, OWNERSHIP_RANGES,
                                      OWNERSHIP_SHARES_BY_DISTRICT, OWNERSHIP_SHARES_BY_QUARTER,
                                      OWNERSHIP_SHARES_CHECKS, OWNERSHIP_SHARES_CITY, PUBLIC_HOUSING_QUARTERS)
from pipeline.use_cases.ownership_shares import step
from pipeline.use_cases.ownership_shares.catalog import CALC_EXAMPLE_QUARTERS
from pipeline.use_cases.ownership_shares.step import run
from pipeline.engine.steps import Context
from pipeline.engine.store import Store
from pipeline.shared.zensus.model import CLASSES


def _store(tmp_path, public: pd.DataFrame) -> Store:
    cells = pd.DataFrame([
        {"cell_id": "a", "edge": 0, "district": "d1", "quarter": "Gallus", "dwellings": 125},
        {"cell_id": "b", "edge": 0, "district": "d2", "quarter": "Bonames", "dwellings": 50},
        {"cell_id": "e", "edge": 1, "district": None, "quarter": None, "dwellings": 9}])
    for k in CLASSES:
        cells[f"bld_{k}"] = 0
    cells.loc[0, "bld_person"] = 3
    ownership = pd.DataFrame({"cell_id": ["a", "b", "e"], "dw_from_2011": 0.0, **{f"dw_{k}": 0.0 for k in CLASSES}})
    ownership.loc[0, ["dw_person", "dw_municipal"]] = [60.0, 40.0]
    ownership.loc[1, "dw_coop"] = 50.0
    store = Store(tmp_path / "interim")
    store.write(CELLS_2022, cells)
    store.write(OWNERSHIP_CELLS, ownership)
    store.write(PUBLIC_HOUSING_QUARTERS, public)
    store.write(COOPS_QUARTERS, pd.DataFrame({"quarter": ["Gallus", "Bonames"], "coop_value": [0.0, 50.0],
                                              "coop_half": [0.0, 5.0], "counted_2011": [0.0, 40.0],
                                              "gap_2011": [0.0, 5.0], "estimate_2022": [0.0, 5.0]}))
    return store


def _run(store, monkeypatch=None) -> None:
    if monkeypatch:
        monkeypatch.setattr(step, "CALC_EXAMPLE_QUARTERS", {g: "Gallus" for g in CALC_EXAMPLE_QUARTERS})
    cfg = SimpleNamespace(QUARTERS_GML=config.QUARTERS_GML, ZENSUS_4000W=config.ZENSUS_4000W,
                          **{e["source"]: getattr(config, e["source"]) for e in EXAMPLES})
    run(Context(store, cfg, log=lambda _: None))


PUBLIC_COLUMNS = {"scaled_2011": [25.0, 0.0], "factor": [1.1, 1.0], "abg_scaled": [22.0, 0.0], "nh_scaled": [5.5, 0.0],
                  "new": [2.0, 0.0], "research_new": [0.0, 0.0]}


def test_step_stores_six_worked_examples(tmp_path, monkeypatch):
    public = pd.DataFrame({"quarter": ["Gallus", "Bonames"], "public_value": [30.0, 0.0], "public_half": [10.0, 0.0],
                           **PUBLIC_COLUMNS})
    store = _store(tmp_path, public)
    _run(store, monkeypatch)
    examples = store.read(OWNERSHIP_CALC_EXAMPLES)
    assert set(examples) == set(CALC_EXAMPLE_QUARTERS)
    assert all(e["area"] == "Gallus" and e["rows"][-1]["unit"] == "%" for e in examples.values())
    # Gallus has 125 dwellings, the estimate knows only 100: the divisor is 125
    public_rows = examples["OWN_PUBLIC"]["rows"]
    assert [r["number"] for r in public_rows if r["op"] == "÷"] == [125.0]
    assert public_rows[-1]["number"] == 24.0


def test_step_on_a_fake_store(tmp_path, monkeypatch):
    public = pd.DataFrame({"quarter": ["Gallus", "Bonames"], "public_value": [30.0, 0.0], "public_half": [10.0, 0.0],
                           **PUBLIC_COLUMNS})
    store = _store(tmp_path, public)
    _run(store, monkeypatch)
    q = store.read(OWNERSHIP_SHARES_BY_QUARTER).set_index("id")
    # Gallus: 125 dwellings, 100 in the estimate (60 person + 40 municipal); ABG+NH 30, coops 0, rest 95 all to persons
    assert q.loc["Gallus", "OWN_PUBLIC"] == pytest.approx(24.0) and q.loc["Gallus", "OWN_PERSON"] == pytest.approx(76.0)
    assert q.loc["Gallus", "OWN_PERSON_DWELLINGS"] == pytest.approx(95.0)
    assert (q.loc["Gallus", "OWN_PUBLIC_LOW"], q.loc["Gallus", "OWN_PUBLIC_HIGH"]) == (pytest.approx(16.0), pytest.approx(32.0))
    assert q.loc["Gallus", "OWN_PERSON_HIGH"] == pytest.approx(81.4) and q.loc["Gallus", "BLD_PERSON"] == 3
    assert q.loc["Bonames", "OWN_COOP"] == pytest.approx(100.0) and q.loc["Bonames", "OWN_COOP_LOW"] == pytest.approx(90.0)
    d = store.read(OWNERSHIP_SHARES_BY_DISTRICT).set_index("id")
    assert list(d.index) == ["d1", "d2"] and not [c for c in d.columns if c.startswith(("OWN_", "COV_"))]
    assert d.loc["d1", "BLD_PERSON"] == 3
    city = {r["indicator"]: r["value"] for r in store.read(OWNERSHIP_SHARES_CITY)}
    assert city["OWN_PUBLIC"] == pytest.approx(100 * 30 / 175) and city["OWN_COOP"] == pytest.approx(100 * 50 / 175)
    assert city["BLD_PERSON"] == 3 and not [k for k in city if k.endswith("_DWELLINGS")]
    assert q.loc["Gallus", "OWN_PUBLIC_DWELLINGS"] == pytest.approx(30.0)
    checks_ = {r["name"]: r["status"] for r in store.read(OWNERSHIP_SHARES_CHECKS)}
    assert checks_["Ownership: dwellings per group match the shares"] == "OK"
    assert checks_["Ownership: the six counts add up to all dwellings"] == "OK"
    checks = {r["name"]: r["status"] for r in store.read(OWNERSHIP_SHARES_CHECKS)}
    assert checks["Ownership: range at the value = value ± half range of the ⓘ"] == "OK"
    assert checks["Ownership: examples in the ⓘ of OWN_COMPANY stand in their sources"] == "OK"
    # half ranges in points: Gallus 10 of 125 dwellings (ABG and NH), Bonames 5 of 50 (Genossenschaften)
    ranges = {r["indicator"]: (r["low"], r["high"]) for r in store.read(OWNERSHIP_RANGES)}
    assert ranges["OWN_PUBLIC"] == (0.0, pytest.approx(8.0)) and ranges["OWN_COOP"] == (0.0, pytest.approx(10.0))
    assert ranges["OWN_PERSON"] == (5.4, 5.4) and len(ranges) == 6


def test_step_stops_when_a_stadtteil_has_no_public_value(tmp_path, monkeypatch):
    store = _store(tmp_path, pd.DataFrame({"quarter": ["Gallus"], "public_value": [30.0], "public_half": [10.0],
                                           "abg_2011": [20.0], "nh_2011": [5.0]}))
    with pytest.raises(ValueError, match=r"\['Bonames'\].*--step public_housing"):
        _run(store, monkeypatch)


def test_step_stops_when_a_stadtteil_has_no_coop_value(tmp_path, monkeypatch):
    store = _store(tmp_path, pd.DataFrame({"quarter": ["Gallus", "Bonames"], "public_value": [30.0, 0.0],
                                           "public_half": [10.0, 0.0], **PUBLIC_COLUMNS}))
    store.write(COOPS_QUARTERS, pd.DataFrame({"quarter": ["Gallus"], "coop_value": [0.0], "coop_half": [0.0]}))
    with pytest.raises(ValueError, match=r"\['Bonames'\].*--step coops"):
        _run(store, monkeypatch)
