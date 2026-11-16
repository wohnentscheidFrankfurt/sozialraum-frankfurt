from types import SimpleNamespace

import pandas as pd
from shapely.geometry import box

from pipeline.shared.core.geometry import Feature, Site
from pipeline.engine.datasets import (CELLS_2022, PROTECTION_BY_DISTRICT, PROTECTION_BY_QUARTER, PROTECTION_CELLS,
                                      PROTECTION_CHECKS, PROTECTION_CITY, PROTECTION_OVERLAYS)
from pipeline.shared.geography.model import Area
from pipeline.use_cases.protection import step
from pipeline.engine.steps import Context
from pipeline.engine.store import Store

X0, Y0 = 477000, 5550000  # near the centre of Frankfurt, EPSG:25832


def _box(x1, y1, x2, y2):
    return box(X0 + x1, Y0 + y1, X0 + x2, Y0 + y2)


def test_step_on_a_fake_store(tmp_path, monkeypatch):
    cells = pd.DataFrame({"cell_id": ["a", "b", "e"], "edge": [0, 0, 1], "district": ["d1", "d1", None],
                          "quarter": ["Gallus", "Bornheim", None], "pop": [10, 30, 99],
                          "x25832": [X0 + 5, X0 + 125, X0 + 5], "y25832": [Y0 + 5, Y0 + 5, Y0 + 5]})
    valid = [Site("Nordend", "E9", _box(0, 0, 100, 150))]  # covers 1.5 ha of d1, the centre of a but not of b
    pending = [Site("Neu", "E70", _box(130, 0, 230, 150))]
    town = [Site("Altstadt", "O1", _box(0, 0, 100, 150), "1993-02-25")]
    town_pending = [Site("Ostend", "O2", _box(130, 0, 230, 150), "2025-12-01")]
    districts = [Area("d1", "Eins", "Gallus", "S1", _box(0, 0, 200, 200)),
                 Area("d2", "Zwei", "Gallus", "S1", _box(1000, 1000, 1100, 1100))]
    quarters = [Area("Gallus", "Gallus", "", "", _box(0, 0, 120, 200)),
                Area("Bornheim", "Bornheim", "", "", _box(120, 0, 300, 200))]
    monkeypatch.setattr(step, "read_features", lambda path: [Feature({}, valid[0].geom, path.name)])
    monkeypatch.setattr(step, "read_social_preservation",
                        lambda features: valid if features[0].raw == "social_preservation.gml" else pending)
    monkeypatch.setattr(step, "read_townscape", lambda features, date_field: town if date_field == step.IN_FORCE
                        else town_pending)
    monkeypatch.setattr(step, "load_districts", lambda gml, csv: districts)
    monkeypatch.setattr(step, "load_quarters", lambda gml: quarters)
    monkeypatch.setattr(step, "read_column", lambda path, column: ["E9"])
    store = Store(tmp_path)
    store.write(CELLS_2022, cells)
    config = SimpleNamespace(SOCIAL_PRESERVATION_GML=tmp_path / "social_preservation.gml",
                             SOCIAL_PRESERVATION_PENDING_GML=tmp_path / "pending.gml", DISTRICTS_GML=None, MONITORING_CSV=None, QUARTERS_GML=None,
                             EXPECTED_SOCIAL_PRESERVATION_CSV=None)
    step.run(Context(store, config, log=lambda text: None))
    assert store.read(PROTECTION_CELLS).to_dict("list") == {"cell_id": ["a", "b"], "in_social_preservation": [1, 0]}
    d = store.read(PROTECTION_BY_DISTRICT).set_index("id")
    assert list(d.index) == ["d1", "d2"] and d.loc["d1", "PROT_SOCIAL"] == 25.0 and pd.isna(d.loc["d2", "PROT_SOCIAL"])
    assert d.loc["d1", "social_preservation_names"] == "Nordend" and d.loc["d1", "townscape_names"] == "Altstadt"
    assert pd.isna(d.loc["d2", "social_preservation_names"])
    q = store.read(PROTECTION_BY_QUARTER).set_index("id")
    assert q["PROT_SOCIAL"].tolist() == [100.0, 0.0]
    assert q.loc["Gallus", "social_preservation_names"] == "Nordend" and pd.isna(q.loc["Bornheim", "social_preservation_names"])
    assert store.read(PROTECTION_CITY) == [{"indicator": "PROT_SOCIAL", "value": 25.0, "kind": "computed"}]
    overlays = store.read(PROTECTION_OVERLAYS)
    assert list(overlays) == ["social_preservation", "social_preservation_pending", "townscape", "townscape_pending"]
    assert [f["properties"] for f in overlays["social_preservation"]["features"]] == [
        {"title": "Nordend", "project_no": "E9"}]
    assert [f["properties"] for f in overlays["townscape"]["features"]] == [
        {"title": "Altstadt", "project_no": "O1", "date": "25.2.1993"}]
    assert [f["properties"]["project_no"] for f in overlays["social_preservation_pending"]["features"]] == ["E70"]
    assert [r["status"] for r in store.read(PROTECTION_CHECKS)] == ["OK", "OK", "OK"]
