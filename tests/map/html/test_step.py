from types import SimpleNamespace

import pandas as pd

from pipeline.engine import datasets
from pipeline.engine.steps import Context
from pipeline.map.html import step
from pipeline.use_cases.candidates.catalog import CUSTOM_NOTE


PATHS = {"de": "/sozialraum-frankfurt/", "en": "/en/sozialraum-frankfurt/"}
SITE = "https://example.org"


class FakeStore:
    """Hands out a fixed value per dataset name; records every dataset the step reads."""

    def __init__(self, values):
        self.values, self.read_names = values, []

    def read(self, dataset):
        self.read_names.append(dataset.name)
        return self.values[dataset.name]


def _store(catalog, indicators):
    return FakeStore({
        "map_catalog": catalog, "election_lists": {"lists": []}, "city_values": pd.DataFrame(),
        "indicators_districts": indicators, "indicators_quarters": indicators,
        "ownership_grid_cells": {"groups": [], "scale": 100000, "rows": []}, "ownership_history_view": {}, "new_construction_view": {"title": "Neubau"},
        "rent_burden_view": {"wage": {}, "low_income": {}},
        "protection_overlays": {k: {} for k in ("social_preservation", "social_preservation_pending", "townscape",
                                                "townscape_pending")},
        "land_overlays": {"pending_plans": {}, "land_value": {"type": "FeatureCollection", "features": []}},
        "flat_roofs_overlays": {"flat_roofs": {"type": "FeatureCollection", "features": []}},
        "building_gaps_overlays": {"building_gaps": {"type": "FeatureCollection", "features": []}}})


def test_the_payload_holds_only_what_the_browser_reads_but_the_exports_keep_every_column(tmp_path, monkeypatch):
    monkeypatch.setattr(step, "LANGUAGES", ("de",))  # the German map alone
    import json

    from shapely.geometry import Polygon
    area = SimpleNamespace(id="1", geom=Polygon([(480000, 5550000), (480100, 5550000), (480100, 5550100)]))
    indicators = pd.DataFrame({"id": ["1"], "name": ["A"], "X": [1.5], "BLD_COOP": [7]})
    catalog = {"catalog": [{"id": "X", "type": "number"}], "overlays": {}, "sources": []}
    seen = {}
    monkeypatch.setattr(step, "load_districts", lambda *a: [area])
    monkeypatch.setattr(step, "load_quarters", lambda *a: [area])
    monkeypatch.setattr(step, "city_value_dict", lambda df: {})
    monkeypatch.setattr(step, "read_web", lambda web: ("template", {}))
    monkeypatch.setattr(step, "render_html", lambda template, parts, data, texts: seen.update(data) or "<!doctype html>\n")
    config = SimpleNamespace(DISTRICTS_GML="d", MONITORING_CSV="m", QUARTERS_GML="q", WEB="w", OUTPUT=tmp_path / "out",
                             MAP_NAMES={"de": "map.html"}, EXPORTS=tmp_path / "exports",
                             ENGLISH_ONLINE=False, MAP_PATHS=PATHS, SITE=SITE)
    step.run(Context(_store(catalog, indicators), config))
    for key in ("districts", "quarters"):
        assert seen[key]["features"][0]["properties"] == {"id": "1", "name": "A", "X": 1.5}
        exported = json.loads((config.EXPORTS / f"{key}.geojson").read_text(encoding="utf-8"))
        assert exported["features"][0]["properties"] == {"id": "1", "name": "A", "X": 1.5, "BLD_COOP": 7}
        assert "BLD_COOP" in (config.EXPORTS / f"indicators_{key}.csv").read_text(encoding="utf-8").splitlines()[0]


def test_the_map_step_puts_the_map_catalog_into_the_payload_as_it_is(tmp_path, monkeypatch):
    monkeypatch.setattr(step, "LANGUAGES", ("de",))  # the German map alone
    catalog = {"catalog": [{"id": "X", "type": "number", "as_of": "Abruf 8.10.2026"}], "overlays": {"grid": {"rule": "r"}},
               "sources": [{"title": "t", "as_of": "abgerufen 8.10.2026", "license": "l"}]}
    store = _store(catalog, pd.DataFrame({"id": ["1"]}))
    seen = {}
    monkeypatch.setattr(step, "load_districts", lambda *a: [])
    monkeypatch.setattr(step, "load_quarters", lambda *a: [])
    monkeypatch.setattr(step, "area_collection", lambda areas, df, keep=None: {"features": []})
    monkeypatch.setattr(step, "city_value_dict", lambda df: {})
    monkeypatch.setattr(step, "read_web", lambda web: ("template", {}))
    monkeypatch.setattr(step, "render_html", lambda template, parts, data, texts: seen.update(data) or "<!doctype html>\n")
    config = SimpleNamespace(DISTRICTS_GML="d", MONITORING_CSV="m", QUARTERS_GML="q", WEB="w", OUTPUT=tmp_path / "out",
                             MAP_NAMES={"de": "map.html"}, EXPORTS=tmp_path / "exports",
                             ENGLISH_ONLINE=False, MAP_PATHS=PATHS, SITE=SITE)
    step.run(Context(store, config))
    assert (seen["catalog"], seen["overlays"], seen["sources"]) == (
        catalog["catalog"], catalog["overlays"], catalog["sources"])
    assert seen["ramp_teal"] == ["#e6fafa", "#b3eeee", "#66dddd", "#16cccc", "#0e8080"]  # the candidates colour by it
    assert seen["hit_border"] == "#e8590c"  # the border of a hit in the candidates, not a literal in JS
    assert seen["election_layers"] == ["ELEC_STRONGEST", "ELEC_TURNOUT"] and "land_value_zones" not in seen
    assert "land_value" in seen and "flat_roofs" in seen and "building_gaps" in seen
    assert seen["custom_note"] == CUSTOM_NOTE["de"]
    assert seen["new_construction"] == {"title": "Neubau"}  # the view of the step new_construction, as it is
    assert datasets.MAP_CATALOG.name in store.read_names
    assert {name for name in store.read_names} <= {d.name for d in step.STEP.needs}


def test_payload_has_the_key_rent_burden(tmp_path, monkeypatch):
    """The view „Miete“ of the step rent_burden, as it is."""
    monkeypatch.setattr(step, "LANGUAGES", ("de",))  # the German map alone
    store = _store({"catalog": [], "overlays": {}, "sources": []}, pd.DataFrame({"id": ["1"]}))
    seen = {}
    monkeypatch.setattr(step, "load_districts", lambda *a: [])
    monkeypatch.setattr(step, "load_quarters", lambda *a: [])
    monkeypatch.setattr(step, "area_collection", lambda areas, df, keep=None: {"features": []})
    monkeypatch.setattr(step, "city_value_dict", lambda df: {})
    monkeypatch.setattr(step, "read_web", lambda web: ("template", {}))
    monkeypatch.setattr(step, "render_html", lambda template, parts, data, texts: seen.update(data) or "<!doctype html>\n")
    config = SimpleNamespace(DISTRICTS_GML="d", MONITORING_CSV="m", QUARTERS_GML="q", WEB="w", OUTPUT=tmp_path / "out",
                             MAP_NAMES={"de": "map.html"}, EXPORTS=tmp_path / "exports",
                             ENGLISH_ONLINE=False, MAP_PATHS=PATHS, SITE=SITE)
    step.run(Context(store, config))
    assert seen["rent_burden"] == {"wage": {}, "low_income": {}}
    assert datasets.RENT_BURDEN_VIEW in step.STEP.needs


def test_the_map_step_writes_the_map_of_each_language_with_its_texts(tmp_path, monkeypatch):
    monkeypatch.setattr(step, "LANGUAGES", ("de",))  # the German map alone
    from pipeline.map.html.model import T
    store = _store({"catalog": [], "overlays": {}, "sources": []}, pd.DataFrame({"id": ["1"]}))
    seen = {}
    monkeypatch.setattr(step, "load_districts", lambda *a: [])
    monkeypatch.setattr(step, "load_quarters", lambda *a: [])
    monkeypatch.setattr(step, "area_collection", lambda areas, df, keep=None: {"features": []})
    monkeypatch.setattr(step, "city_value_dict", lambda df: {})
    monkeypatch.setattr(step, "read_web", lambda web: ("<!doctype html>\n<title>{{title}}</title>", {}))
    monkeypatch.setattr(step, "render_html", lambda template, parts, data, texts: seen.update(data, texts=texts)
                        or template.replace("{{title}}", texts["html.title"]))
    config = SimpleNamespace(DISTRICTS_GML="d", MONITORING_CSV="m", QUARTERS_GML="q", WEB="w", OUTPUT=tmp_path / "out",
                             MAP_NAMES={"de": "karte.html", "en": "map.html"}, EXPORTS=tmp_path / "exports",
                             ENGLISH_ONLINE=False, MAP_PATHS=PATHS, SITE=SITE)
    step.run(Context(store, config))
    assert sorted(p.name for p in config.OUTPUT.iterdir()) == ["karte.html"]  # the languages of the build only
    html = (config.OUTPUT / "karte.html").read_text(encoding="utf-8")
    assert f"<title>{T['de']['html.title']}</title>" in html and T["de"]["cover_note"].splitlines()[0] in html
    assert seen["lang"] == "de" and seen["ui"] == T["de"].tree("ui") and seen["texts"] is T["de"]
    assert seen["created"] == T["de"].date(__import__("datetime").date.today())


def test_the_map_step_writes_a_second_language_from_its_own_texts_and_datasets(tmp_path, monkeypatch):
    """With English in LANGUAGES the step writes a second map: its texts, its datasets `.en` and the texts `_SHARED` of
    its monitoring table; the exports stay German and single."""
    import datetime

    from pipeline.map.html import model
    from pipeline.shared.core.texts import package_texts
    texts = package_texts(model.__file__, languages=("de", "en"))
    monkeypatch.setattr(step, "LANGUAGES", ("de", "en"))
    indicators = pd.DataFrame({"id": ["1"], "SOC_INDEX_SHARED": ["1 und 2"]})
    store = _store({"catalog": [], "overlays": {}, "sources": []}, indicators)
    store.values["election_lists"] = {"lists": [{"name": "CDU", "key": "ELEC_CDU"}, {"name": "Sonstige", "key": "ELEC_OTHER"}]}
    store.values |= {f"{name}.en": value for name, value in store.values.items()}
    store.values["monitoring_by_district.en"] = pd.DataFrame({"id": ["1"], "SOC_INDEX_SHARED": ["1 and 2"]})
    seen = {}
    monkeypatch.setattr(step, "load_districts", lambda *a: [])
    monkeypatch.setattr(step, "load_quarters", lambda *a: [])
    monkeypatch.setattr(step, "area_collection", lambda areas, df, keep=None: {
        "features": [{"properties": r} for r in df.to_dict("records")]})
    monkeypatch.setattr(step, "city_value_dict", lambda df: {})
    monkeypatch.setattr(step, "read_web", lambda web: ("<!doctype html>\n", {}))
    monkeypatch.setattr(step, "render_html", lambda template, parts, data, t: seen.setdefault(t.lang, data) and template)
    config = SimpleNamespace(DISTRICTS_GML="d", MONITORING_CSV="m", QUARTERS_GML="q", WEB="w", OUTPUT=tmp_path / "out",
                             MAP_NAMES={"de": "karte.html", "en": "map.html"}, EXPORTS=tmp_path / "exports",
                             ENGLISH_ONLINE=False, MAP_PATHS=PATHS, SITE=SITE)
    step.run(Context(store, config))
    assert sorted(p.name for p in config.OUTPUT.iterdir()) == ["karte.html", "map.html"]
    en = seen["en"]
    assert en["lang"] == "en" and en["ui"] == texts["en"].tree("ui") and en["ui"] != seen["de"]["ui"]
    assert en["created"] == texts["en"].date(datetime.date.today())
    assert en["districts"]["features"][0]["properties"]["SOC_INDEX_SHARED"] == "1 and 2"
    assert seen["de"]["districts"]["features"][0]["properties"]["SOC_INDEX_SHARED"] == "1 und 2"
    assert {"map_catalog.en", "protection_overlays.en", "ownership_history_view.en"} <= set(store.read_names)
    note = (config.OUTPUT / "map.html").read_text(encoding="utf-8")
    assert note.startswith("<!doctype html>\n<!--\n" + texts["en"]["cover_note"].splitlines()[0])
    assert en["election_year"] == seen["de"]["election_year"] == 2026
    assert [l["name"] for l in seen["de"]["lists"]] == ["CDU", "Sonstige"]
    assert [l["name"] for l in en["lists"]] == ["CDU", "Others"]
    assert sorted(p.name for p in config.EXPORTS.iterdir()) == ["districts.geojson", "indicators_districts.csv",
                                                                "indicators_quarters.csv", "quarters.geojson"]


def _two_maps(tmp_path, monkeypatch, online):
    """Runs the step for both languages with a template that has a head; gives (payloads by language, files by name)."""
    monkeypatch.setattr(step, "LANGUAGES", ("de", "en"))
    indicators = pd.DataFrame({"id": ["1"], "SOC_INDEX_SHARED": ["1 und 2"]})
    store = _store({"catalog": [], "overlays": {}, "sources": []}, indicators)
    store.values["election_lists"] = {"lists": []}
    store.values |= {f"{name}.en": value for name, value in store.values.items()}
    store.values["monitoring_by_district.en"] = pd.DataFrame({"id": ["1"], "SOC_INDEX_SHARED": ["1 and 2"]})
    seen = {}
    monkeypatch.setattr(step, "load_districts", lambda *a: [])
    monkeypatch.setattr(step, "load_quarters", lambda *a: [])
    monkeypatch.setattr(step, "area_collection", lambda areas, df, keep=None: {"features": []})
    monkeypatch.setattr(step, "city_value_dict", lambda df: {})
    monkeypatch.setattr(step, "read_web", lambda web: ("<!doctype html>\n<html><head></head></html>", {}))
    monkeypatch.setattr(step, "render_html", lambda template, parts, data, t: seen.setdefault(t.lang, data) and template)
    config = SimpleNamespace(DISTRICTS_GML="d", MONITORING_CSV="m", QUARTERS_GML="q", WEB="w", OUTPUT=tmp_path / "out",
                             MAP_NAMES={"de": "karte.html", "en": "map.html"}, EXPORTS=tmp_path / "exports",
                             ENGLISH_ONLINE=online, MAP_PATHS=PATHS, SITE=SITE)
    step.run(Context(store, config))
    return seen, {p.name: p.read_text(encoding="utf-8") for p in config.OUTPUT.iterdir()}


def test_german_map_has_no_switch_while_english_is_offline(tmp_path, monkeypatch):
    seen, files = _two_maps(tmp_path, monkeypatch, online=False)
    assert "switch" not in seen["de"]
    online_seen, _ = _two_maps(tmp_path / "on", monkeypatch, online=True)
    assert online_seen["de"]["switch"] == {"lang": "en", "label": "English", "file": "map.html",
                                           "path": "/en/sozialraum-frankfurt/"}


def test_english_map_always_has_its_switch(tmp_path, monkeypatch):
    for online in (False, True):
        seen, _ = _two_maps(tmp_path / str(online), monkeypatch, online=online)
        assert seen["en"]["switch"] == {"lang": "de", "label": "Deutsch", "file": "karte.html",
                                        "path": "/sozialraum-frankfurt/"}


def test_hreflang_only_when_online(tmp_path, monkeypatch):
    _, off = _two_maps(tmp_path, monkeypatch, online=False)
    assert all("hreflang" not in html for html in off.values())
    _, on = _two_maps(tmp_path / "on", monkeypatch, online=True)
    for html in on.values():
        assert '<link rel="alternate" hreflang="de" href="https://example.org/sozialraum-frankfurt/">' in html
        assert '<link rel="alternate" hreflang="en" href="https://example.org/en/sozialraum-frankfurt/">' in html
        assert html.index("hreflang") < html.index("</head>")
