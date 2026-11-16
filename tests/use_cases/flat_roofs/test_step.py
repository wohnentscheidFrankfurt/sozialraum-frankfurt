import pandas as pd
from shapely.geometry import box

from pipeline.engine.datasets import (FLAT_ROOFS_BY_DISTRICT, FLAT_ROOFS_BY_QUARTER, FLAT_ROOFS_CALC_EXAMPLES,
                                      FLAT_ROOFS_CHECKS, FLAT_ROOFS_CITY, FLAT_ROOFS_OVERLAYS)
from pipeline.shared.geography.model import Area
from pipeline.use_cases.flat_roofs import step

X0, Y0 = 477000, 5550000


def part(building, x0, y0, w, h, height, use="31001_2000", flat=True):
    g = box(X0 + x0, Y0 + y0, X0 + x0 + w, Y0 + y0 + h)
    return {"building": building, "use": use, "excluded": False, "flat": flat, "height_m": height,
            "ground_m2": g.area, "gemarkung": "G", "created": "2020", "geometry": g}


def test_step_on_a_fake_store(tmp_path, monkeypatch, run_step):
    # a wall more than 3 m higher along the top of a: 2,5 x 20 = 50 m² of its 400 m² stay free
    parts = pd.DataFrame([part("a", 10, 10, 20, 20, 5.0), part("w", 10, 30, 20, 5, 9.0, flat=False),
                          part("b", 60, 10, 20, 20, 5.0), part("far", 5000, 5000, 20, 20, 5.0)])
    zones = [box(X0, Y0, X0 + 50, Y0 + 50)]  # b is no housing zone
    districts = [Area("d1", "Eins", "G", "S1", box(X0, Y0, X0 + 200, Y0 + 200))]
    quarters = [Area("G", "G", "", "", box(X0, Y0, X0 + 200, Y0 + 200))]
    gem = pd.DataFrame({"gemarkung": ["G"], "buildings": [3], "parsed": [3], "delivered": ["2026-06-26"]})
    reference = tmp_path / "reference.csv"
    pd.DataFrame({"building": ["a"], "function": ["31001_2000"], "area_m2": [400.0], "height_m": [5.0],
                  "source": ["s"]}).to_csv(reference, index=False)
    monkeypatch.setattr(step, "read_parts", lambda path: parts)
    monkeypatch.setattr(step, "read_gemarkungen", lambda path: gem)
    monkeypatch.setattr(step, "read_zones", lambda folder: zones)
    monkeypatch.setattr(step, "load_districts", lambda gml, csv: districts)
    monkeypatch.setattr(step, "load_quarters", lambda gml: quarters)
    monkeypatch.setattr(step, "read_building_code", lambda path: ["Abstandsflächen mindestens 2,50 m betragen."])
    store, logs = run_step(tmp_path, step.STEP, {}, LOD2_PARTS_CSV=None, LOD2_GEMARKUNGEN_CSV=None, BORIS_DIR=None,
                           DISTRICTS_GML=None, MONITORING_CSV=None, QUARTERS_GML=None, HBO_SYNOPSIS_PDF=None,
                           FLAT_ROOFS_REFERENCE_CSV=reference)
    assert store.read(FLAT_ROOFS_BY_DISTRICT).round(2).to_dict("list") == {"id": ["d1"], "ROOF_FLAT": [350.0]}
    assert store.read(FLAT_ROOFS_BY_QUARTER).round(2).to_dict("list") == {"id": ["G"], "ROOF_FLAT": [350.0]}
    (city,) = store.read(FLAT_ROOFS_CITY)
    assert city["indicator"] == "ROOF_FLAT" and round(city["value"], 2) == 350.0 and city["kind"] == "computed"
    overlays = store.read(FLAT_ROOFS_OVERLAYS)["flat_roofs"]["features"]
    assert [f["properties"]["counts"] for f in overlays] == [1, 0]  # the roof far away is in no district
    assert {f["geometry"]["type"] for f in overlays} <= {"Polygon", "MultiPolygon"}
    counted, other = (f["properties"]["text"] for f in overlays)
    assert "Zählt nicht" in other and "Zählt nicht" not in counted and "50 m²" in counted
    ex = store.read(FLAT_ROOFS_CALC_EXAMPLES)["ROOF_FLAT"]
    # no very low roof: its row goes; 7 modules round to 0 hundreds, so that row goes too
    assert [(r["op"], r["number"], r["total"]) for r in ex["rows"]] == [
        ("", 800, False), ("−", 400, False), ("−", 50, False), ("", 350, True), ("×", 0.5, False), ("÷", 25, False)]
    checks = store.read(FLAT_ROOFS_CHECKS)
    assert [c["status"] for c in checks if c["status"] == "FAIL"] == []
    assert len(checks) == 7 and logs


def test_step_fails_when_the_synopsis_drops_the_2_5_m(tmp_path, monkeypatch, run_step):
    parts = pd.DataFrame([part("a", 10, 10, 20, 20, 5.0)])
    gem = pd.DataFrame({"gemarkung": ["G"], "buildings": [1], "parsed": [1], "delivered": ["2026-06-26"]})
    reference = tmp_path / "reference.csv"
    pd.DataFrame({"building": ["a"], "function": ["31001_2000"], "area_m2": [400.0], "height_m": [5.0],
                  "source": ["s"]}).to_csv(reference, index=False)
    area = box(X0, Y0, X0 + 200, Y0 + 200)
    monkeypatch.setattr(step, "read_parts", lambda path: parts)
    monkeypatch.setattr(step, "read_gemarkungen", lambda path: gem)
    monkeypatch.setattr(step, "read_zones", lambda folder: [area])
    monkeypatch.setattr(step, "load_districts", lambda gml, csv: [Area("d1", "Eins", "G", "S1", area)])
    monkeypatch.setattr(step, "load_quarters", lambda gml: [Area("G", "G", "", "", area)])
    monkeypatch.setattr(step, "read_building_code", lambda path: ["Abstandsflächen mindestens 3 m betragen."])
    store, _ = run_step(tmp_path, step.STEP, {}, LOD2_PARTS_CSV=None, LOD2_GEMARKUNGEN_CSV=None, BORIS_DIR=None,
                        DISTRICTS_GML=None, MONITORING_CSV=None, QUARTERS_GML=None, FLAT_ROOFS_REFERENCE_CSV=reference,
                        HBO_SYNOPSIS_PDF=None)
    failed = [c["name"] for c in store.read(FLAT_ROOFS_CHECKS) if c["status"] == "FAIL"]
    assert failed == ["Flat roofs: HBO synopsis still says the wall strip"]
