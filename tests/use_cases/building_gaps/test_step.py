import pandas as pd
from shapely.geometry import box

from pipeline.engine.datasets import (BUILDING_GAPS_BY_DISTRICT, BUILDING_GAPS_BY_QUARTER, BUILDING_GAPS_CALC_EXAMPLES,
                                      BUILDING_GAPS_CHECKS, BUILDING_GAPS_CITY, BUILDING_GAPS_OVERLAYS)
from pipeline.shared.core.texts import LANGUAGES
from pipeline.shared.geography.model import Area
from pipeline.use_cases.building_gaps import step
from pipeline.use_cases.building_gaps.catalog import COUNT_TEXT, SITE_TEXT, T

X0, Y0 = 477000, 5550000
COVER = {"px": 600, "building": 0.0, "tree": 0.0, "green": 0.1, "open": 0.9, "nan_share": 0.0, "flight": "2025-08-19"}

TEXTS = T["de"]


def rect(x, y, w, h):
    return box(X0 + x, Y0 + y, X0 + x + w, Y0 + y + h)


def write(path, rows, columns):
    pd.DataFrame(rows, columns=columns).to_csv(path, index=False)
    return path


def world(tmp_path, monkeypatch, verdict_rows):
    # four free gaps of 30 x 20 m at a street: a counts, b does not, c needs a visit, d lies out of the housing zone
    ids = ["a", "b", "c", "d"]
    parcels = pd.DataFrame({"gml_id": ids, "kz": [f"0604661650000{i}0001__" for i in range(1, 5)],
                            "official_m2": 600.0, "created": "1990-01-01", "addresses": 1,
                            "geometry": [rect(50 * i, 0, 30, 20) for i in range(4)]})
    buildings = pd.DataFrame(columns=["gml_id", "function", "main", "geometry"])
    landuse = pd.DataFrame([
        {"gml_id": "s", "cls": "Strassenverkehr", "function": "", "housing": False, "access": True,
         "geometry": rect(-50, -10, 400, 10)},
        {"gml_id": "h", "cls": "Wohnbauflaeche", "function": "", "housing": True, "access": False,
         "geometry": rect(-50, 0, 400, 100)}])
    cover = pd.DataFrame([{"gml_id": i, **COVER} for i in ids]).set_index("gml_id")
    area = rect(-100, -100, 600, 300)
    monkeypatch.setattr(step, "read_parcels", lambda path: parcels)
    monkeypatch.setattr(step, "read_buildings", lambda path: buildings)
    monkeypatch.setattr(step, "read_landuse", lambda path: landuse)
    monkeypatch.setattr(step, "read_cover", lambda path: cover)
    monkeypatch.setattr(step, "read_zones", lambda folder: [rect(-10, -10, 150, 50)])
    monkeypatch.setattr(step, "load_districts", lambda gml, csv: [Area("d1", "Eins", "G", "S1", area)])
    monkeypatch.setattr(step, "load_quarters", lambda gml: [Area("G", "G", "", "", area)])
    meta = write(tmp_path / "meta.csv", [("portion_date", "2026-11-04"), ("parcels", "4"), ("cover_high_m", "2.5"),
                                         ("cover_ndvi_green", "0.2")], ["key", "value"])
    verdicts = write(tmp_path / "verdicts.csv", verdict_rows,
                     ["gml_id", "kz", "verdict", "reason", "note", "checked", "by"])
    reference = write(tmp_path / "parcels.csv", [("a", "060466165000010001__", 600.0, "s")],
                      ["gml_id", "kz", "official_m2", "source"])
    known = write(tmp_path / "known.csv", [("d", "dropped", "out of zone")],
                  ["gml_id", "expect", "note"])
    examples = write(tmp_path / "examples.csv",
                     [("coop", 312, 9, 25, "u", "p", 2017, "s", "q"),
                      ("house_for_all", 365, 19, "", "u", "p", 2026, "s", "q"),
                      ("student", 1270, 177, "", "u", "p", 2015, "s", "q"),
                      ("multi_family", 2000, 42, "", "u", "p", 2027, "s", "q"),
                      ("complex", 5400, 67, "", "u", "p", 2025, "s", "q")],
                     ["category", "area_m2", "number", "residents", "unit", "place", "year", "source_url", "quote"])
    return dict(ALKIS_PARCELS_CSV=None, ALKIS_BUILDINGS_CSV=None, ALKIS_LANDUSE_CSV=None, ALKIS_META_CSV=meta,
                BUILDING_GAPS_COVER_CSV=None, BUILDING_GAPS_REFERENCE_CSV=verdicts,
                BUILDING_GAPS_PARCELS_CSV=reference, BUILDING_GAPS_KNOWN_CSV=known,
                BUILDING_GAPS_EXAMPLES_CSV=examples, BORIS_DIR=None, DISTRICTS_GML=None, MONITORING_CSV=None,
                QUARTERS_GML=None)


VERDICTS = [("a", "060466165000010001__", "counts", "parking", "", "2026-11-15", "aerial"),
            ("b", "060466165000020001__", "not", "square", "", "2026-11-15", "aerial"),
            ("c", "060466165000030001__", "site", "", "", "2026-11-15", "aerial")]


def test_step_on_a_fake_store(tmp_path, monkeypatch, run_step):
    store, logs = run_step(tmp_path, step.STEP, {}, **world(tmp_path, monkeypatch, VERDICTS))
    assert store.read(BUILDING_GAPS_BY_DISTRICT).round(2).to_dict("list") == {"id": ["d1"], "GAP_AREA": [600.0]}
    assert store.read(BUILDING_GAPS_BY_QUARTER).round(2).to_dict("list") == {"id": ["G"], "GAP_AREA": [600.0]}
    (city,) = store.read(BUILDING_GAPS_CITY)
    assert city["indicator"] == "GAP_AREA" and round(city["value"], 2) == 600.0 and city["kind"] == "computed"
    features = store.read(BUILDING_GAPS_OVERLAYS)["building_gaps"]["features"]
    # b is judged not and d lies out of the zone: neither is drawn (user, 15.11.)
    assert [f["properties"]["counts"] for f in features] == [1, 0]
    assert {f["geometry"]["type"] for f in features} <= {"Polygon", "MultiPolygon"}
    counted, site = (f["properties"]["text"] for f in features)
    first = TEXTS.fill("kz", gemarkung="0466", flur="165", number="1/1")
    assert counted.startswith(first + ". 600 m², 30 m an der Straße, ")
    assert COUNT_TEXT["de"]["parking"] in counted and "Zählt nicht" not in counted
    third = TEXTS.fill("kz", gemarkung="0466", flur="165", number="3/1")
    assert site.startswith(third + ". ") and SITE_TEXT["de"] in site and "Zählt nicht" not in site
    ex = store.read(BUILDING_GAPS_CALC_EXAMPLES)["GAP_AREA"]
    assert ex["label"] and [(r["op"], r["number"], r["total"]) for r in ex["rows"]] == [
        ("", 4, False), ("−", 1, False), ("−", 1, False), ("−", 1, False), ("", 1, True), ("", 600, True)]
    checks = store.read(BUILDING_GAPS_CHECKS)
    assert [c for c in checks if c["status"] != "OK"] == []
    # the check of the suitability examples reads the texts: once more per other language
    assert all(c["name"].startswith("Building gaps: ") for c in checks) and len(checks) == 7 + len(LANGUAGES) and logs
    assert len({c["name"] for c in checks}) == len(checks)


def test_step_without_verdicts_warns_and_counts_nothing(tmp_path, monkeypatch, run_step):
    store, _ = run_step(tmp_path, step.STEP, {}, **world(tmp_path, monkeypatch, []))
    assert store.read(BUILDING_GAPS_BY_DISTRICT)["GAP_AREA"].tolist() == [0.0]
    statuses = {c["name"]: c["status"] for c in store.read(BUILDING_GAPS_CHECKS)}
    assert [n for n, s in statuses.items() if s != "OK"] == ["Building gaps: hand verdicts"]
    assert statuses["Building gaps: hand verdicts"] == "WARN"


def test_step_fails_on_an_unknown_verdict(tmp_path, monkeypatch, run_step):
    rows = [VERDICTS[0], ("b", "060466165000020001__", "not", "parking", "", "2026-11-15", "aerial"), VERDICTS[2]]
    store, _ = run_step(tmp_path, step.STEP, {}, **world(tmp_path, monkeypatch, rows))
    failed = [c for c in store.read(BUILDING_GAPS_CHECKS) if c["status"] == "FAIL"]
    assert [c["name"] for c in failed] == ["Building gaps: hand verdicts"] and "b" in failed[0]["text"]
