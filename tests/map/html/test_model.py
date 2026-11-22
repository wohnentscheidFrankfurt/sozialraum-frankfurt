import json
import math

import numpy as np
import pytest

from pipeline.map.html.model import T, clean_value, json_for_html, render_html
from pipeline.shared.core.texts import Texts

MARKERS_HTML = ("<style>/*__LEAFLET_CSS__*/</style><style>/*__FONTS__*/</style><style>/*__MAP_CSS__*/</style>"
                "<script>/*__DATA__*/</script><script>/*__LEAFLET_JS__*/</script><script>/*__MAP_JS__*/</script>")


PARTS = {"/*__LEAFLET_CSS__*/": ".leaflet{}", "/*__FONTS__*/": "", "/*__MAP_CSS__*/": "body{}",
         "/*__LEAFLET_JS__*/": "var L={};", "/*__MAP_JS__*/": "eins();\nzwei();"}
NO_TEXTS = Texts("de", {}, {})


def test_render_html_fills_every_marker():
    html = render_html(MARKERS_HTML, PARTS, {"a": 1}, NO_TEXTS)
    assert '{"a":1}' in html and html.index("eins();") < html.index("zwei();") and "/*__" not in html


def test_render_html_reports_a_missing_marker():
    with pytest.raises(ValueError, match="__"):
        render_html("<html></html>", {}, {}, NO_TEXTS)


def test_render_html_replaces_text_markers():
    texts = Texts("en", {"html.title": "A & <B>", "html.help.share": 'Say "hi"', "ui.x": "not a marker"}, {})
    template = '<html lang="{{lang}}"><title>{{title}}</title><p title="{{help.share}}">{{help.share}}</p>' + MARKERS_HTML
    html = render_html(template, PARTS, {}, texts)
    # escaped, the markup of the template stays; lang is the language tag of the page
    assert html.startswith('<html lang="en-GB"><title>A &amp; &lt;B&gt;</title><p title="Say &quot;hi&quot;">Say &quot;hi&quot;</p>')
    assert "{{" not in html and "not a marker" not in html
    assert render_html('<html lang="{{lang}}">' + MARKERS_HTML, PARTS, {}, NO_TEXTS).startswith('<html lang="de">')


def test_unknown_text_marker_raises():
    with pytest.raises(ValueError, match="help.nothing"):
        render_html("<p>{{help.nothing}}</p>" + MARKERS_HTML, PARTS, {}, NO_TEXTS)


def test_unused_html_key_raises():
    texts = Texts("de", {"html.title": "T", "html.help.left_over": "x"}, {})
    with pytest.raises(ValueError, match="help.left_over"):
        render_html("<title>{{title}}</title>" + MARKERS_HTML, PARTS, {}, texts)


def test_the_template_and_the_language_file_agree():
    from pipeline import config
    from pipeline.map.html.model import fill_text_markers
    html = fill_text_markers((config.WEB / "map.html").read_text(encoding="utf-8"), T["de"])
    assert "{{" not in html and '<html lang="de">' in html



def test_clean_value_turns_nan_into_none():
    assert clean_value(math.nan) is None and clean_value(np.float64("nan")) is None
    assert clean_value(np.int64(3)) == 3 and type(clean_value(np.int64(3))) is int and clean_value("x") == "x"


def test_json_for_html_masks_the_script_end():
    text = json_for_html({"title": 'A "B" </script><script>alert(1)</script> & C'})
    assert "</script>" not in text and json.loads(text)["title"].startswith('A "B" </script>')


def test_json_for_html_has_no_raw_less_than_sign():
    value = {"title": "x <!--<script> y </script> <b>"}
    text = json_for_html(value)
    assert "<" not in text and json.loads(text) == value


def test_json_for_html_rejects_nan():
    with pytest.raises(ValueError):
        json_for_html({"x": math.nan})


def test_round_to_50_half_up():
    from pipeline.map.html.model import round_to_50
    assert [round_to_50(x) for x in (24.9, 25, 808.41, 824.99, 825, 0)] == [0, 50, 800, 800, 850, 0]
    assert all(type(round_to_50(x)) is int for x in (24.9, 808.41))
    assert round_to_50(None) is None and round_to_50(math.nan) is None


def test_round_estimates_row_changes_only_the_count_columns_and_not_the_input():
    from pipeline.map.html.model import round_estimates
    row = {"id": "632", "OWN_STATE_DWELLINGS_LOW": 74.84, "OWN_COOP_DWELLINGS": 808.41, "OWN_PUBLIC": 30.82}
    new = round_estimates(row)
    assert new == {"id": "632", "OWN_STATE_DWELLINGS_LOW": 50, "OWN_COOP_DWELLINGS": 800, "OWN_PUBLIC": 30.82}
    assert row["OWN_COOP_DWELLINGS"] == 808.41 and new is not row


def test_round_estimates_covers_every_count_column():
    from pipeline.map.html.model import round_estimates
    from pipeline.use_cases.ownership_shares.model import DWELLING_COLUMNS
    assert len(DWELLING_COLUMNS) == 18
    assert set(round_estimates({k: 74.84 for k in DWELLING_COLUMNS}).values()) == {50}


def test_round_estimates_dataframe_keeps_empty_values_empty():
    import pandas as pd
    from pipeline.map.html.model import round_estimates
    df = pd.DataFrame({"id": ["1", "2"], "OWN_STATE_DWELLINGS_LOW": [74.84, None], "OWN_COOP_DWELLINGS": [808.41, 24.9], "OWN_PUBLIC": [1.5, 2.5]})
    new = round_estimates(df)
    assert new["OWN_COOP_DWELLINGS"].tolist() == [800, 0] and new["OWN_STATE_DWELLINGS_LOW"].iloc[0] == 50 and pd.isna(new["OWN_STATE_DWELLINGS_LOW"].iloc[1])
    assert df["OWN_COOP_DWELLINGS"].tolist() == [808.41, 24.9]
    assert new.to_csv(index=False).splitlines() == ["id,OWN_STATE_DWELLINGS_LOW,OWN_COOP_DWELLINGS,OWN_PUBLIC", "1,50,800,1.5", "2,,0,2.5"]


def test_rounded_geojson_keeps_the_input(tmp_path):
    from pipeline.map.html.model import rounded_geojson
    fc = {"type": "FeatureCollection", "features": [
        {"type": "Feature", "properties": {"OWN_STATE_DWELLINGS_LOW": 74.84, "OWN_COOP_DWELLINGS": 808.41}, "geometry": {"type": "Point", "coordinates": [1, 2]}}]}
    out = rounded_geojson(fc)
    assert out["features"][0]["properties"] == {"OWN_STATE_DWELLINGS_LOW": 50, "OWN_COOP_DWELLINGS": 800}
    assert fc["features"][0]["properties"] == {"OWN_STATE_DWELLINGS_LOW": 74.84, "OWN_COOP_DWELLINGS": 808.41}
    assert out["features"][0]["geometry"] == fc["features"][0]["geometry"]


def test_cover_note_names_notice_and_date():
    from pipeline.map.html.model import cover_note
    t = cover_note("8.10.2026", T["de"])
    # CLAUDE.md: the header
    assert t.startswith("Sozialraum Frankfurt\n") and "8.10.2026" in t
    assert "--" not in t  # would end the HTML comment


def test_with_cover_note_puts_the_comment_after_the_doctype():
    from pipeline.map.html.model import cover_note, with_cover_note
    html = with_cover_note("<!doctype html>\n<html lang=\"de\"></html>\n", "8.10.2026", T["de"])
    assert html == f"<!doctype html>\n<!--\n{cover_note('8.10.2026', T['de'])}-->\n<html lang=\"de\"></html>\n"


def test_with_cover_note_needs_the_doctype_first():
    from pipeline.map.html.model import with_cover_note
    with pytest.raises(ValueError, match="doctype"):
        with_cover_note("<html></html>", "8.10.2026", T["de"])


def test_with_cover_note_stops_on_a_double_dash(monkeypatch):
    import pipeline.map.html.model as map_model
    monkeypatch.setattr(map_model, "cover_note", lambda created, t: "a -- b\n")
    with pytest.raises(ValueError, match="--"):
        map_model.with_cover_note("<!doctype html>\n<html></html>", "8.10.2026", T["de"])



def test_cover_note_years_come_from_the_catalog_constants(monkeypatch):
    import datetime

    import pipeline.map.html.model as map_model
    # odd years in the constants: each one must show up in the note
    for name, value in {"SH_DATE": datetime.date(1901, 12, 31), "FIRST_YEAR": 1902, "LAST_YEAR": 1903,
                        "ELECTION_DATE": datetime.date(1904, 1, 1), "BORIS_DATE": datetime.date(1905, 1, 1),
                        "RENT_FROM": 1906, "RENT_TO": 1907}.items():
        monkeypatch.setattr(map_model, name, value)
    t = map_model.cover_note("8.10.2026", T["de"])
    assert "1901" in t and "1902–1903" in t and "1904" in t and "1905" in t and "Miete 1906–1907" in t
    # a proper list: commas, then „und“ before the last entry
    assert "Wahl 1904, Bodenrichtwerte 1905 und 3D-Gebäudemodell 2026." in t
    assert "31.12.1901" not in t and "1.1.1904" not in t and "1.1.1905" not in t  # the year alone


# --- payload whitelist ---

def _catalog_dicts():
    """The catalog as the map step reads it from map_catalog.json: plain dicts."""
    from dataclasses import asdict

    from pipeline.map.assembly.catalog import CATALOG
    return [asdict(k) for k in CATALOG["de"]]


def test_whitelist_keeps_every_property_the_browser_reads():
    import re
    from pathlib import Path

    from pipeline.map.html.model import browser_properties
    from pipeline.use_cases.candidates.catalog import TEMPLATES
    # the election layers come from the live catalog; the legend reads ELEC_STRONGEST by hand
    catalog = _catalog_dicts() + [{"id": "ELEC_STRONGEST", "type": "category"}]
    lists = [{"key": "ELEC_CDU"}, {"key": "ELEC_OTHER"}]
    keep = browser_properties(catalog, TEMPLATES["de"], lists)
    js = "".join(p.read_text(encoding="utf-8") for p in sorted(Path("web/js").glob("*.js")))
    # names after "p." that belong to other objects called p: Leaflet layers and DOM nodes, overlay features, points
    other_objects = {"hasLayer", "on", "getContainer", "x", "y", "append", "hidden", "textContent", "length",
                     "invalidateSize", "style", "className", "removeLayer", "options", "fitBounds", "update", "de", "js",
                     "use", "project_no", "title", "date", "land_value", "addLayer", "closeTooltip", "createPane",
                     "getElement", "getZoom", "latLngToContainerPoint", "offsetHeight", "offsetWidth", "openTooltip",
                     "setLatLng", "text", "counts"}
    literal = set(re.findall(r"\bp\.([A-Za-z_][A-Za-z0-9_]*)\b", js)) - other_objects
    assert literal <= keep, literal - keep
    assert {"OWN_PUBLIC_HIGH", "OWN_COOP_HIGH", "COV_OWN", "small", "OWN_PUBLIC_DWELLINGS", "OWN_NONPROFIT_DWELLINGS_HIGH", "ELEC_CDU", "ELEC_OTHER",
            "LIF_ATTACHMENT_LOWER", "LIF_RENT_BURDEN_RATIO_LOWER"} <= keep
    # the list of districts that share a monitoring value (tooltip and profile of the browser)
    assert {"SOC_UNEMPLOYED_SHARED", "SOC_MIN_INCOME_SHARED"} <= keep
    assert {c["indicator"] for t in TEMPLATES["de"] for c in t["criteria"]} <= keep


def test_whitelist_drops_what_the_browser_never_reads():
    from pipeline.map.html.model import browser_properties
    from pipeline.use_cases.candidates.catalog import TEMPLATES
    keep = browser_properties(_catalog_dicts(), TEMPLATES["de"], [])
    assert not {"BLD_COOP", "COV_HOU_RENTERS", "POP_MONITORING", "HOUSEHOLDS", "POP_15_65", "OWN_PUBLIC_LOW",
                "OWN_PUBLIC_DWELLINGS_LOW", "PUBLIC_DWELLINGS", "SOC_RANK"} & keep


def test_area_properties_passes_only_the_kept_columns():
    import pandas as pd
    from pipeline.map.html.model import area_properties
    df = pd.DataFrame({"id": ["1", "2"], "name": ["a", "b"], "BLD_COOP": [3, 4], "X": [1.5, math.nan]})
    assert area_properties(df, {"id", "name", "X"}) == {"1": {"id": "1", "name": "a", "X": 1.5},
                                                        "2": {"id": "2", "name": "b", "X": None}}
    assert list(area_properties(df, {"id"})["1"]) == ["id"]


def test_with_use_names_spells_out_the_use_and_keeps_the_rest():
    from pipeline.map.html.model import with_use_names
    from pipeline.use_cases.land.catalog import T, use_name
    zones = {"type": "FeatureCollection", "features": [
        {"type": "Feature", "properties": {"land_value": 1000.0, "use": "W", "building": ""}, "geometry": None},
        {"type": "Feature", "properties": {"land_value": 3000.0, "use": "M", "building": "MFH"}, "geometry": None}]}
    out = with_use_names(zones, T["de"])
    assert [f["properties"] for f in out["features"]] == [{"land_value": 1000.0, "use": use_name("W", "", T["de"])},
                                                          {"land_value": 3000.0, "use": use_name("M", "MFH", T["de"])}]
    assert out["type"] == "FeatureCollection" and zones["features"][0]["properties"]["use"] == "W"


def test_whitelist_keeps_the_voters_and_the_total_they_are_shown_against():
    from pipeline.map.html.model import browser_properties
    from pipeline.use_cases.candidates.catalog import TEMPLATES
    from dataclasses import asdict

    from pipeline.use_cases.election.catalog import T as ELECTION_TEXTS, election_indicators
    keep = browser_properties(_catalog_dicts() + [asdict(k) for k in election_indicators([], ELECTION_TEXTS["de"])], TEMPLATES["de"], [])
    assert {"ELEC_VOTERS", "ELEC_ELIGIBLE"} <= keep
    assert "ELEC_ELIGIBLE" in browser_properties([{"id": "X", "type": "number", "count_total": "ELEC_ELIGIBLE"}],
                                                 [], [])


def test_shared_texts_come_from_the_monitoring_table_of_the_language():
    import pandas as pd
    from pipeline.map.html.model import with_shared_texts
    indicators = pd.DataFrame({"id": ["1", "2", "3"], "SOC_X": [1.0, 2.0, 3.0], "SOC_X_SHARED": ["1 und 3", None, "1 und 3"]})
    monitoring = pd.DataFrame({"id": ["3", "2", "1"], "SOC_X": [9.0, 9.0, 9.0], "SOC_X_SHARED": ["1 and 3", None, "1 and 3"]})
    before = indicators.copy()
    out = with_shared_texts(indicators, monitoring)
    assert out["SOC_X_SHARED"].tolist()[::2] == ["1 and 3", "1 and 3"] and pd.isna(out["SOC_X_SHARED"].iloc[1])
    assert out["SOC_X"].tolist() == [1.0, 2.0, 3.0] and list(out.columns) == list(indicators.columns)
    pd.testing.assert_frame_equal(indicators, before)  # the input stays
