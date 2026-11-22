from pipeline.shared.core.indicator import year_of
from pipeline.use_cases.ownership_shares.catalog import EXAMPLES, INDICATORS as BY_LANGUAGE, T, other_calc_example
from pipeline.use_cases.ownership_shares.model import OtherNumbers

INDICATORS = BY_LANGUAGE["de"]
TEXTS = T["de"]
BUILDING_LABELS = TEXTS.tree("calc_example.building_labels")
GROUP_WORDS = TEXTS.tree("calc_example.group_words")


def test_ownership_indicators():
    assert [x.id for x in INDICATORS] == ["OWN_COMPANY", "OWN_PERSON", "OWN_STATE", "OWN_NONPROFIT"]
    assert all(f"{{high_{x.id}}}" in x.uncertainty and x.estimate for x in INDICATORS)


def test_every_example_has_a_source_and_stands_in_the_text():
    """research/2026-10-14-who-are-the-private-companies.md: each name in the ⓘ has a source the build reads."""
    rule = {x.id: x for x in INDICATORS}["OWN_COMPANY"].rule
    assert [e["name"] for e in EXAMPLES] == ["Vonovia", "GWH", "Helaba", "Industria Wohnen", "Hamburg Trust"]
    assert all(e["name"] in rule and e["source"] and e["phrases"] for e in EXAMPLES)


def test_state_layer_rule_says_why_the_nassauische_heimstaette_is_not_in_it():
    """Between the shared phrases the rule names the fact about the layer: the Zensus 2022 counts the Nassauische
    Heimstätte as kommunal (docs/data-rules.md). No text of the map names the view Trend: tests/map/assembly."""
    rule = {x.id: x for x in INDICATORS}["OWN_STATE"].rule
    assert rule.startswith(TEXTS["core.quarters_rule"] + " ") and rule.endswith(" " + TEXTS["core.tip_dwellings_rule"])
    assert "Nassauische Heimstätte" in rule and year_of(TEXTS["core.z22_as_of"]) in rule and "kommun" in rule.lower()


def test_the_company_rule_names_no_vonovia_number_and_the_details_name_only_sourced_examples():
    k = {x.id: x for x in INDICATORS}
    assert "16.000" not in k["OWN_COMPANY"].rule and "Vonovia nennt" not in k["OWN_COMPANY"].rule
    named = ("Vonovia", "GWH", "Industria Wohnen")
    assert all(n in k["OWN_COMPANY"].legend_detail for n in named)
    assert set(named) <= {e["name"] for e in EXAMPLES}


def test_one_class_follows_the_mockup():
    n = OtherNumbers({"state": 102}, {"state": 10.7027}, 0.0, 917.8, 8186.0)
    e = other_calc_example("OWN_STATE", "Ginnheim", n, 11.21, TEXTS)
    assert [(r.op, r.number) for r in e.rows] == [("", 102), ("×", 10.7), ("", 1091), ("×", 0.84), ("", 918),
                                                  ("÷", 8186), ("", 11.2)]
    assert (e.rows[-2].op, e.rows[-2].number, e.rows[-2].decimals) == ("÷", 8186, 0)
    assert e.rows[0].text == BUILDING_LABELS["state"] and e.rows[1].decimals == 1
    assert e.rows[4].estimate and e.rows[4].text.endswith(GROUP_WORDS["OWN_STATE"])
    assert e.rows[-1].unit == "%" and e.rows[-1].estimate


def test_two_classes_have_one_product_row_each_and_the_2011_row():
    n = OtherNumbers({"housing_company": 64, "other_company": 61}, {"housing_company": 11.38, "other_company": 13.75},
                     179.0, 1721.5, 4006.0)
    e = other_calc_example("OWN_COMPANY", "Innenstadt", n, 42.97, TEXTS)
    # the product row names the buildings and the factor
    assert e.rows[0].text.startswith(f"64 {BUILDING_LABELS['housing_company']} × 11,4 ")
    assert [r.number for r in e.rows[:3]] == [730, 842, 1572]
    assert ("+", 179) in [(r.op, r.number) for r in e.rows]
    totals = [r for r in e.rows if r.total]
    # the last total before ÷ names the group
    assert totals[1].text == "" and totals[-2].text.endswith(GROUP_WORDS["OWN_COMPANY"])


def test_no_2011_row_where_it_rounds_to_zero():
    n = OtherNumbers({"state": 102}, {"state": 10.7027}, 0.4, 918.2, 8186.0)
    assert not any(r.op == "+" for r in other_calc_example("OWN_STATE", "Ginnheim", n, 11.21, TEXTS).rows)


def test_no_adjustment_without_buildings():
    n = OtherNumbers({"state": 0}, {"state": 10.7027}, 12.0, 12.0, 900.0)
    assert not any(r.op == "×" and r.decimals == 2 for r in other_calc_example("OWN_STATE", "X", n, 1.3, TEXTS).rows)


def test_building_count_has_a_thousands_separator():
    n = OtherNumbers({"housing_company": 1079, "other_company": 61}, {"housing_company": 2.7, "other_company": 13.75},
                     0.0, 1721.5, 4006.0)
    e = other_calc_example("OWN_COMPANY", "Innenstadt", n, 42.97, TEXTS)
    assert e.rows[0].text.startswith("1.079 ") and " × 2,7 " in e.rows[0].text


def test_divisor_rows_share_one_label_and_legend_notes_do_not_say_bekannt():
    from pipeline.use_cases.coops import catalog as coops
    from pipeline.use_cases.ownership_cells.catalog import OWN_LEGEND_NOTE, OWN_LEGEND_NOTE_COOP
    from pipeline.use_cases.public_housing import catalog as public_housing
    n = OtherNumbers({"state": 102}, {"state": 10.7027}, 0.0, 917.8, 8186.0)
    public = {"scaled_2011": 1544.1, "factor": 0.9757, "abg_scaled": 1506.2, "nh_scaled": 0.0, "new": 12.2,
              "research_new": 0.0, "public_value": 1526.5}
    coop = {"counted_2011": 712.0, "gap_2011": 155.9, "estimate_2022": 0.0, "coop_value": 867.9}
    examples = [public_housing.public_calc_example("X", public, 2482.0, 61.5, public_housing.T["de"]),
                coops.coop_calc_example("X", coop, 2482.0, 35.0, coops.T["de"])]
    examples.append(other_calc_example("OWN_STATE", "X", n, 11.2, TEXTS))
    divisors = [r.text for e in examples for r in e.rows if r.op == "÷"]
    assert len(divisors) == 3 and len(set(divisors)) == 1
    assert "bekannt" not in OWN_LEGEND_NOTE["de"] + OWN_LEGEND_NOTE_COOP["de"]


def test_example_quarters_have_a_high_share_and_public_housing_large_fills():
    from pipeline.use_cases.ownership_shares.catalog import CALC_EXAMPLE_QUARTERS
    assert CALC_EXAMPLE_QUARTERS == {"OWN_PUBLIC": "Niederrad", "OWN_COOP": "Riederwald", "OWN_COMPANY": "Innenstadt",
                                     "OWN_PERSON": "Nieder-Erlenbach", "OWN_STATE": "Ginnheim",
                                     "OWN_NONPROFIT": "Gutleutviertel"}
