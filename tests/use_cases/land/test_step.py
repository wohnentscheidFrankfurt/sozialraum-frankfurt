
import numpy as np
import pandas as pd
from shapely.geometry import box

from pipeline.shared.core.geometry import Feature, Site
from pipeline.engine.datasets import (CELLS_2022, LAND_BY_DISTRICT, LAND_BY_QUARTER, LAND_CHECKS, LAND_CITY,
                                      LAND_OVERLAYS, LAND_VALUE_CELLS)
from pipeline.shared.geography.model import Area
from pipeline.use_cases.land import step
from pipeline.use_cases.land.model import Zone

X0, Y0 = 477000, 5550000  # near the centre of Frankfurt, EPSG:25832


def _box(x1, y1, x2, y2):
    return box(X0 + x1, Y0 + y1, X0 + x2, Y0 + y2)


def test_step_on_a_fake_store(tmp_path, monkeypatch, run_step):
    cells = pd.DataFrame({"cell_id": ["a", "b", "e"], "edge": [0, 0, 1], "district": ["d1", "d1", None],
                          "quarter": ["Gallus", "Bornheim", None], "pop": [10, 30, 99],
                          "x25832": [X0 + 5, X0 + 25, X0 + 5], "y25832": [Y0 + 5, Y0 + 5, Y0 + 5]})
    # values of 2024 in the zones, of 2026 in the table; the third zone has no value of 2026 and drops out
    zones = [Zone(_box(0, 0, 10, 10), 1200.0, "W", "1", "EFH"), Zone(_box(20, 0, 30, 10), 3500.0, "M", "2"),
             Zone(_box(0, 0, 30, 10), 9999.0, "W", "3")]
    values = {"1": (1000.0, "01.01.2026"), "2": (3000.0, "01.01.2026")}
    plans = [Site("Am Bügel", "B 1", _box(0, 0, 150, 150))]  # covers 2.25 ha of d1, nothing of d2
    districts = [Area("d1", "Eins", "Gallus", "S1", _box(0, 0, 200, 200)),
                 Area("d2", "Zwei", "Gallus", "S1", _box(1000, 1000, 1100, 1100))]
    quarters = [Area("Gallus", "Gallus", "", "", _box(0, 0, 15, 15)),
                Area("Bornheim", "Bornheim", "", "", _box(15, 0, 40, 15))]
    monkeypatch.setattr(step, "read_zones", lambda folder: zones)
    monkeypatch.setattr(step, "read_values", lambda path: values)
    monkeypatch.setattr(step, "read_features", lambda path: [Feature({}, plans[0].geom, "")])
    monkeypatch.setattr(step, "read_pending_plans", lambda features: plans)
    monkeypatch.setattr(step, "load_districts", lambda gml, csv: districts)
    monkeypatch.setattr(step, "load_quarters", lambda gml: quarters)
    store, _ = run_step(tmp_path, step.STEP, {CELLS_2022: cells}, BORIS_DIR=tmp_path, BORIS_VALUES_CSV=None,
                        PENDING_PLANS_GML=tmp_path / "p.gml", DISTRICTS_GML=None, MONITORING_CSV=None, QUARTERS_GML=None)
    assert store.read(LAND_VALUE_CELLS)["cell_id"].tolist() == ["a", "b"]  # the edge cell has no land value
    d = store.read(LAND_BY_DISTRICT).set_index("id")
    assert list(d.index) == ["d1", "d2"] and d.loc["d1", "LAND_VALUE"] == 3000.0 and np.isnan(d.loc["d2", "LAND_VALUE"])
    assert d["LAND_PENDING_PLAN"].tolist() == [1, 0] and d.loc["d1", "pending_plan_names"] == "Am Bügel"
    q = store.read(LAND_BY_QUARTER).set_index("id")
    assert q["LAND_VALUE"].tolist() == [1000.0, 3000.0]
    assert store.read(LAND_CITY) == [{"indicator": "LAND_VALUE", "value": 3000.0, "kind": "computed"}]
    overlays = store.read(LAND_OVERLAYS)
    assert list(overlays) == ["pending_plans", "land_value"]
    assert [f["properties"] for f in overlays["pending_plans"]["features"]] == [
        {"title": "Am Bügel", "project_no": "B 1"}]
    assert [f["properties"] for f in overlays["land_value"]["features"]] == [
        {"land_value": 1000.0, "use": "W", "building": "EFH"}, {"land_value": 3000.0, "use": "M", "building": ""}]
    assert [(r["name"], r["status"], r["text"]) for r in store.read(LAND_CHECKS)][1] == (
        "Land values 2026: zones with a value", "WARN", "2 of 3 zones with a value of 01.01.2026")
