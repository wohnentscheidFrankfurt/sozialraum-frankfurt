import pandas as pd
import pytest

from pipeline.use_cases.ownership_history import catalog
from pipeline.use_cases.ownership_history.model import (HISTORY_GROUPS, LARGE, by_size, company_buildings_by_decade,
                                                        change_text, history_data, history_facts, history_groups)
from pipeline.shared.zensus.model import SIZES

# the German texts of the view; the tests take each text from its constant
CHARTS, COMPANY_TITLE, GROUP_TEXTS, HISTORY_SOURCE, SECTORS, SIZE_LABELS = (
    getattr(catalog, name)["de"] for name in ("CHARTS", "COMPANY_TITLE", "GROUP_TEXTS", "HISTORY_SOURCE", "SECTORS",
                                              "SIZE_LABELS"))
TEXTS = catalog.T["de"]

DWELLINGS = {
    2011: {"condo": 101464, "person": 131689, "coop": 13390, "municipal": 52189, "housing_company": 27770,
           "other_company": 10077, "state": 20461, "nonprofit": 8359, "total": 365401},
    2022: {"condo": 98759, "person": 134116, "coop": 12932, "municipal": 69558, "housing_company": 57076,
           "other_company": 19264, "state": 5651, "nonprofit": 5471, "total": 402826},
}

# Real buildings per class 2011 and 2022 (3000G-2007 totals), sizes only where a test needs them
BUILDINGS = {2011: {"person": 47290, "condo": 13088, "municipal": 7140, "state": 2507, "housing_company": 3497,
                    "other_company": 1025, "coop": 1937, "nonprofit": 970, "total": 77457},
             2022: {"person": 50138, "condo": 12146, "municipal": 8508, "state": 577, "housing_company": 5173,
                    "other_company": 1623, "coop": 1795, "nonprofit": 721, "total": 80679}}


def _by_size(values, large=None):
    """Totals per class; all of a class in size '1' except the given dwellings in LARGE."""
    out = {}
    for y, classes in values.items():
        out[y] = {}
        for k, n in classes.items():
            big = (large or {}).get((y, k), 0)
            out[y][k] = {s: 0 for s in SIZES} | {"1": n - big, LARGE: big, "total": n}
    return out


LARGE_DWELLINGS = {(2011, "housing_company"): 12000, (2011, "other_company"): 3657, (2011, "total"): 100389,
                   (2022, "housing_company"): 30000, (2022, "other_company"): 10934, (2022, "total"): 127106}


def _sizes():
    return by_size(_by_size(BUILDINGS), _by_size(DWELLINGS, LARGE_DWELLINGS))


def test_history_groups_join_municipality_and_state():
    g = history_groups(DWELLINGS, _by_size(BUILDINGS))
    assert list(HISTORY_GROUPS) == ["person", "condo", "public", "housing_company", "other_company", "coop",
                                    "nonprofit"]
    v = g.set_index(["group", "year"])["dwellings"]
    assert v["public", 2011] == 72650 and v["public", 2022] == 75209
    # the two company classes stay apart
    assert v["housing_company", 2011] == 27770 and v["other_company", 2022] == 19264
    assert v["person", 2022] == 134116 and len(g) == 14


def _decades():
    decades = [{"decade": "A", "label": "Vor 1919", "first_year": 0},
               {"decade": "B", "label": "2010–2015", "first_year": 2010}]
    buildings = {2011: {"housing_company": {"A": 100, "B": 10}, "other_company": {"A": 50, "B": 0}},
                 2022: {"housing_company": {"A": 300, "B": 40}, "other_company": {"A": 90, "B": 20}}}
    return company_buildings_by_decade(decades, buildings)


def test_company_buildings_by_decade_adds_both_company_classes():
    d = _decades().set_index(["decade", "year"])
    assert d.loc[("A", 2011), "buildings"] == 150 and d.loc[("A", 2022), "buildings"] == 390
    assert d.loc[("B", 2022), "buildings"] == 60 and d.loc[("B", 2022), "label"] == "2010–2015"


def test_history_facts():
    f = history_facts(history_groups(DWELLINGS, _by_size(BUILDINGS)), _decades(), _sizes())
    assert round(f["company_factor"], 2) == 2.02
    assert f["company_growth"] == 290 and f["company_growth_before_2010"] == 240
    assert round(f["share_before_2010"], 3) == round(240 / 290, 3)


def test_history_facts_for_the_lead_lines():
    decades = [{"decade": "A", "label": "1950–1959", "first_year": 1950},
               {"decade": "B", "label": "1960–1969", "first_year": 1960},
               {"decade": "C", "label": "2010–2015", "first_year": 2010}]
    buildings = {2011: {"housing_company": {"A": 100, "B": 100, "C": 0}, "other_company": {"A": 0, "B": 0, "C": 0}},
                 2022: {"housing_company": {"A": 400, "B": 150, "C": 60}, "other_company": {"A": 0, "B": 0, "C": 0}}}
    f = history_facts(history_groups(DWELLINGS, _by_size(BUILDINGS)), company_buildings_by_decade(decades, buildings),
                     _sizes())
    # base: the sum of the groups (402,827), not the printed total
    assert f["company_share_2022"] == 76340 / 402827


def test_history_groups_have_buildings():
    v = history_groups(DWELLINGS, _by_size(BUILDINGS)).set_index(["group", "year"])["buildings"]
    assert v["housing_company", 2011] == 3497 and v["other_company", 2022] == 1623
    assert v["public", 2011] == 9647 and v["public", 2022] == 9085 and v["person", 2022] == 50138


def test_by_size_joins_classes_and_keeps_all():
    s = _sizes().set_index(["group", "year", "size"])
    # seven groups, the sum of both company classes and all owners
    assert len(s) == 9 * 2 * 5
    assert s.loc[("company", 2022, LARGE), "dwellings"] == 40934 and s.loc[("all", 2022, LARGE), "dwellings"] == 127106
    assert s.loc[("public", 2022, "1"), "buildings"] == 9085


def test_history_facts_for_buildings_and_sizes():
    f = history_facts(history_groups(DWELLINGS, _by_size(BUILDINGS)), _decades(), _sizes())
    assert round(f["company_building_factor"], 3) == 1.503
    # base: the sum of the groups, as for the dwellings
    assert f["company_building_share_2022"] == 6796 / 80681
    assert round(f["company_large_share_2011"], 3) == 0.156 and round(f["company_large_share_2022"], 3) == 0.322
    assert f["company_large_growth"] == 25277 and f["company_dwelling_growth"] == 38493
    assert round(f["large_growth_share"], 3) == 0.657
    # dwellings per building 2022: the smaller company class is housing companies 57,076 / 5,173 (other companies
    # 19,264 / 1,623); next largest public 75,209 / 9,085
    assert f["smallest_company_dwellings_per_building_2022"] == 57076 / 5173
    assert f["largest_other_dwellings_per_building_2022"] == 75209 / 9085


def test_history_data_for_the_view():
    rows = [("person", 3, 4, 2, 2), ("condo", 1, 1, 1, 1), ("public", 5, 6, 1, 1), ("housing_company", 2, 5, 1, 1),
            ("other_company", 0, 2, 0, 1), ("coop", 1, 1, 1, 1), ("nonprofit", 1, 0, 1, 0)]
    groups = pd.DataFrame([{"group": g, "year": y, "dwellings": n, "buildings": b} for g, n11, n22, b11, b22 in rows
                           for y, n, b in ((2011, n11, b11), (2022, n22, b22))])
    sizes = pd.DataFrame([{"group": g, "year": y, "size": s, "buildings": 1, "dwellings": n}
                          for g in ("company", "all", "person") for y in (2011, 2022)
                          for s, n in zip(["1", "2", "3_6", "7_12", "13_plus"], [1, 2, 3, 4, 5 if y == 2011 else 9])])
    # the label of the source is not shown; the view takes the text of the key
    decades = pd.DataFrame([{"decade": "B", "key": "1919_1949", "label": "?", "first_year": 1919, "year": y,
                             "buildings": n} for y, n in ((2011, 888), (2022, 785))]
                           + [{"decade": "A", "key": "before_1919", "label": "?", "first_year": 0, "year": y,
                               "buildings": n} for y, n in ((2011, 510), (2022, 778))])
    h = history_data(groups, sizes, decades, TEXTS)
    assert "intro" not in h and h["source"] == HISTORY_SOURCE
    assert [g["id"] for g in h["groups"]] == ["person", "condo", "public", "housing_company", "other_company", "coop",
                                              "nonprofit"]
    texts = {k: GROUP_TEXTS["other_company"][k] for k in ("title", "lines", "about", "example")}
    assert h["groups"][4] == {"id": "other_company", **texts, "color": "#575757",
                              "values": {"2011": 0, "2022": 2}, "buildings": {"2011": 0, "2022": 1},
                              "share": {"buildings": {"2011": 0, "2022": 100 * 1 / 7},
                                        "values": {"2011": 0, "2022": 100 * 2 / 19}},
                              "line_color": "#575757", "label_color": "#ffffff",
                              "label_contrast": pytest.approx(7.226056749490168, rel=1e-12), "company": True,
                              "change": {"buildings": None, "values": None}}  # no change from a base of 0
    assert [g["company"] for g in h["groups"]] == [False, False, False, True, True, False, False]
    # a light colour gets dark text and a darker line (values of the browser, see test_colours)
    assert (h["groups"][0]["label_color"], h["groups"][0]["line_color"]) == ("#1a1a1a", "#919191")
    # the sum of both classes for the charts „sizes“ and „decades“
    assert h["company"] == {"title": COMPANY_TITLE, "values": {"2011": 2, "2022": 7},
                            "buildings": {"2011": 1, "2022": 2}}
    assert [s["label"] for s in h["sizes"]] == [SIZE_LABELS[s]["label"] for s in SIZES]
    assert h["sizes"][4] == {"size": "13_plus", **SIZE_LABELS["13_plus"],
                             "company": {"2011": 5, "2022": 9}, "all": {"2011": 5, "2022": 9},
                             "company_share": {"2011": 100.0, "2022": 100.0}}
    assert h["sizes"][0]["company_share"] == {"2011": 100.0, "2022": 100.0}
    assert [d["label"] for d in h["decades"]] == ["Vor 1919", "1919–1949"]
    assert h["decades"][1]["values"] == {"2011": 888, "2022": 785}
    assert h["bar_order"][:2] == ["housing_company", "other_company"]
    assert set(h["charts"]) == {"houses", "arrows", "sizes", "decades"}
    # the tooltip of the large buildings comes finished: +4 of +16 company dwellings in 13+ (9 - 5 = 4; 7 - 2 = 5)
    sizes_chart = h["charts"]["sizes"]
    assert "tip_large" not in sizes_chart
    assert sizes_chart["tip_large_text"] == CHARTS["sizes"]["tip_large"].format(large="4", total="5")
    assert h["sectors"] == [
        {"id": "private", "title": SECTORS["private"]["title"], "color": "#262626",
         "groups": ["housing_company", "other_company", "condo", "person"],
         "count": {"values": {"2011": 6, "2022": 12}},
         "share": {"buildings": {"2011": 100 * 4 / 7, "2022": 100 * 5 / 7},
                   "values": {"2011": 100 * 6 / 13, "2022": 100 * 12 / 19}}},
        {"id": "community", "title": SECTORS["community"]["title"], "color": "#d40000",
         "groups": ["public", "coop", "nonprofit"],
         "count": {"values": {"2011": 7, "2022": 7}},
         "share": {"buildings": {"2011": 100 * 3 / 7, "2022": 100 * 2 / 7},
                   "values": {"2011": 100 * 7 / 13, "2022": 100 * 7 / 19}}}]


@pytest.mark.parametrize("a, b, text", [(100, 112, "+12 %"), (100, 88, "−12 %"), (200, 205, "+3 %"), (200, 195, "−2 %"),
                                         (100, 100, "+0 %"), (1, 1500, "+149.900 %"), (0, 5, None)])
def test_change_text_rounds_like_the_browser_did(a, b, text):
    """Math.round of the browser rounds a half up (-2.5 to -2); the sign comes from the direction."""
    assert change_text(a, b, TEXTS) == text


def test_history_data_ships_large_growth_with_german_thousands():
    rows = [("person", 0, 0), ("condo", 0, 0), ("public", 0, 0), ("housing_company", 20000, 60000),
            ("other_company", 0, 0), ("coop", 0, 0), ("nonprofit", 0, 0)]
    groups = pd.DataFrame([{"group": g, "year": y, "dwellings": n, "buildings": 1}
                           for g, n11, n22 in rows for y, n in ((2011, n11), (2022, n22))])
    sizes = pd.DataFrame([{"group": g, "year": y, "size": s, "buildings": 1, "dwellings": n}
                          for g in ("company", "all", "person") for y in (2011, 2022)
                          for s, n in zip(["1", "2", "3_6", "7_12", "13_plus"],
                                          [1, 2, 3, 4, 10000 if y == 2011 else 35277])])
    decades = pd.DataFrame([{"decade": "A", "key": "before_1919", "label": "Vor 1919", "first_year": 0, "year": y,
                             "buildings": 1}
                            for y in (2011, 2022)])
    text = history_data(groups, sizes, decades, TEXTS)["charts"]["sizes"]["tip_large_text"]
    assert text == CHARTS["sizes"]["tip_large"].format(large="25.277", total="40.000")
