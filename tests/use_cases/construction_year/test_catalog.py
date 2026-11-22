from pipeline.map.assembly.catalog import CATALOG
from pipeline.shared.core.indicator import tooltip_rounding, year_of
from pipeline.use_cases.construction_year.catalog import (CALC_EXAMPLE_QUARTERS, CONSTRUCTION_COUNT_STEP, COUNTS, T,
                                                          INDICATORS as BY_LANGUAGE,
                                                          construction_calc_example as _construction_calc_example)

INDICATORS, TEXTS = BY_LANGUAGE["de"], T["de"]
FIELD_EDGE = TEXTS["core.field_edge"]
CONSTRUCTION_RULE = TEXTS["rule"]
CONSTRUCTION_UNCERTAINTY = TEXTS["uncertainty"]
CONSTRUCTION_COUNT_ROUNDING = tooltip_rounding(TEXTS, "dwellings_phrase", CONSTRUCTION_COUNT_STEP)
SHARE_LEGEND_NOTE = TEXTS.fill("legend_note", year_2022=year_of(TEXTS["core.z22_as_of"]),
                               year_2011=year_of(TEXTS["core.z11_as_of"]))
YEARS = {k: TEXTS[f"years.{k}"] for k in ("HOU_PRE1919", "HOU_1949_1978")}


def construction_calc_example(*args):
    return _construction_calc_example(*args, TEXTS)


def test_construction_year_indicators_in_the_catalog():
    assert [k.id for k in INDICATORS] == ["HOU_PRE1919", "HOU_PRE1919_DWELLINGS", "HOU_1949_1978",
                                          "HOU_1949_1978_DWELLINGS"]
    ids = [k.id for k in CATALOG]
    i = ids.index("HOU_PRE1919")
    assert ids[i:i + 4] == [k.id for k in INDICATORS]
    assert COUNTS == frozenset({"HOU_PRE1919_DWELLINGS", "HOU_1949_1978_DWELLINGS"})


def test_shares_are_layers_and_counts_are_rounded():
    """pipeline/use_cases/construction_year/README.md: one step for text and map."""
    k = {x.id: x for x in CATALOG}
    for kid in ("HOU_PRE1919", "HOU_1949_1978"):
        assert k[kid].layer and k[kid].criterion and k[kid].unit == "%" and k[kid].ramp == "orange"
        assert not k[kid + "_DWELLINGS"].layer and not k[kid + "_DWELLINGS"].criterion
        assert k[kid + "_DWELLINGS"].unit == "Wohnungen" and k[kid + "_DWELLINGS"].decimals == 0
        assert k[kid].levels == k[kid + "_DWELLINGS"].levels == ("district", "quarter")
    assert [x.id for x in CATALOG if x.round_to and x.id.startswith("HOU_") and "VACANT" not in x.id] == [
        "HOU_PRE1919_DWELLINGS", "HOU_1949_1978_DWELLINGS"]
    assert all(k[i].round_to == 10 for i in COUNTS)


def test_construction_texts_use_the_shared_phrases_and_both_values_are_estimates():
    """README: share and count are estimates."""
    k = {x.id: x for x in INDICATORS}
    assert CONSTRUCTION_UNCERTAINTY.endswith(" " + FIELD_EDGE)
    assert "2022" in SHARE_LEGEND_NOTE and "2011" in SHARE_LEGEND_NOTE
    for kid in ("HOU_PRE1919", "HOU_1949_1978"):
        assert k[kid].estimate and k[kid + "_DWELLINGS"].estimate
        assert "{" not in k[kid].calc + k[kid].rule + k[kid].uncertainty
        assert k[kid].uncertainty == CONSTRUCTION_UNCERTAINTY and k[kid].legend_note == SHARE_LEGEND_NOTE
        assert k[kid].rule.startswith(CONSTRUCTION_RULE + " ")
    # only the class before 1919 has an extra rule: it names the oldest buildings
    assert "1870" in k["HOU_PRE1919"].rule and k["HOU_PRE1919"].rule.endswith(" " + CONSTRUCTION_COUNT_ROUNDING)
    assert "1870" not in k["HOU_1949_1978"].rule
    assert k["HOU_1949_1978"].rule == f"{CONSTRUCTION_RULE} {CONSTRUCTION_COUNT_ROUNDING}"


def test_the_count_is_a_tooltip_line_explained_by_the_share():
    """docs/texts.md, ⓘ protocol: the ⓘ of the layer explains its count."""
    k = {x.id: x for x in INDICATORS}
    for kid in ("HOU_PRE1919", "HOU_1949_1978"):
        c = k[kid + "_DWELLINGS"]
        assert c.count_of == kid and not c.rule and not c.uncertainty
        assert c.round_to == CONSTRUCTION_COUNT_STEP
    # the ⓘ names the step the tooltip rounds to
    assert str(CONSTRUCTION_COUNT_STEP) in CONSTRUCTION_COUNT_ROUNDING


def _numbers(e):
    return [(r.op, r.number) for r in e.rows]


def test_construction_example_follows_the_spec():
    e = construction_calc_example("HOU_1949_1978", "Altstadt", 1984, 1853, 2572, 72.04)
    assert e.area == "Altstadt"
    assert _numbers(e) == [("", 1984), ("−", 131), ("", 1853), ("÷", 2572), ("", 72.0)]
    # the class rows name the years of construction, the first and the divisor row the year of the count
    assert all(YEARS["HOU_1949_1978"] in e.rows[i].text for i in (0, 2))
    assert "2011" in e.rows[0].text and "2022" in e.rows[3].text and all(r.text for r in e.rows)
    assert [r.estimate for r in e.rows] == [False, False, True, False, True]
    assert [r.total for r in e.rows] == [False, False, True, False, True]
    assert e.rows[-1].unit == "%" and e.rows[-1].decimals == 1
    first = construction_calc_example("HOU_PRE1919", "X", 10, 5, 50, 10.0).rows[0].text
    assert YEARS["HOU_PRE1919"] in first and "2011" in first


def test_construction_example_without_the_cap():
    e = construction_calc_example("HOU_1949_1978", "X", 1853, 1853, 2572, 72.04)
    assert _numbers(e) == [("", 1853), ("÷", 2572), ("", 72.0)]
    # the first row is the row of 2011, as with the cap
    capped = construction_calc_example("HOU_1949_1978", "X", 1984, 1853, 2572, 72.04)
    assert e.rows[0].text == capped.rows[0].text
    assert not e.rows[0].estimate and not e.rows[0].total


def test_the_examples_carry_the_rechnung():
    k = {x.id: x for x in INDICATORS}
    assert CALC_EXAMPLE_QUARTERS == {"HOU_PRE1919": "Nordend-Ost", "HOU_1949_1978": "Altstadt"}
    assert all(k[i].calc == "" for i in CALC_EXAMPLE_QUARTERS)
    assert all(k[f"{i}_DWELLINGS"].calc for i in CALC_EXAMPLE_QUARTERS)
