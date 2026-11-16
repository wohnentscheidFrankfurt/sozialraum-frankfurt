import math

import pandas as pd

from pipeline.map.assembly.catalog import CATALOG
from pipeline.use_cases.candidates.catalog import CITY_VALUE, TEMPLATES, UPPER_END_NOTE
from pipeline.use_cases.candidates.model import evaluate, meets, shown, threshold

DECIMALS = {"SOC_MIN_INCOME": 1, "PROT_SOCIAL": 1, "OWN_PUBLIC": 1, "OWN_COOP": 1}


def test_templates_use_only_known_indicators():
    ids = {k.id for k in CATALOG}
    # a criterion on the end of a range (OWN_PUBLIC_HIGH) names its indicator in `city`
    assert {k.get("city", k["indicator"]) for v in TEMPLATES for k in v["criteria"]} <= ids
    assert [v["id"] for v in TEMPLATES] == ["social_preservation", "coop", "public_company"]


def test_every_criterion_exists_on_the_level_of_its_template():
    levels = {k.id: k.levels for k in CATALOG}
    assert [v["level"] for v in TEMPLATES] == ["district", "quarter", "quarter"]
    assert all(v["level"] in levels[k.get("city", k["indicator"])] for v in TEMPLATES for k in v["criteria"])


def test_both_ownership_templates_work_on_stadtteile():
    assert {t["id"]: t["level"] for t in TEMPLATES}["coop"] == "quarter"


def test_template_for_public_housing_companies():
    """pipeline/use_cases/candidates/README.md."""
    v = {x["id"]: x for x in TEMPLATES}["public_company"]
    assert [(k["indicator"], k["op"], k["threshold"]) for k in v["criteria"]] == [
        ("SOC_MIN_INCOME", ">=", "city_value"), ("OWN_PUBLIC_HIGH", "<", "city_value")]


def test_template_for_social_preservation_uses_old_buildings_before_1919():
    """pipeline/use_cases/construction_year/README.md: Altbau vor 1919 replaces Altbau vor 1949."""
    v = {x["id"]: x for x in TEMPLATES}["social_preservation"]
    assert [(k["indicator"], k["op"], k["threshold"]) for k in v["criteria"]] == [
        ("HOU_RENTERS", ">=", "city_value"), ("SOC_MIN_INCOME", ">=", "city_value"),
        ("HOU_PRE1919", ">=", "city_value"), ("LAND_VALUE", ">=", "city_value"), ("PROT_SOCIAL", "<", 50)]


def test_meets():
    assert meets(5, ">=", 5) and not meets(4.99, ">=", 5)
    assert meets(49.99, "<", 50) and not meets(50, "<", 50)
    assert meets(1, "==", 1) and not meets(0, "==", 1)


def test_meets_with_a_missing_value():
    assert not meets(None, ">=", 1) and not meets(math.nan, "<", 1) and not meets(3, ">=", None)


def test_threshold_city_value_or_fixed():
    assert threshold({"indicator": "SOC_MIN_INCOME", "threshold": CITY_VALUE}, {"SOC_MIN_INCOME": 11.3}) == 11.3
    assert threshold({"indicator": "PROT_SOCIAL", "threshold": 50}, {}) == 50


def test_evaluate_leaves_out_small_districts():
    districts = pd.DataFrame({"id": ["a", "b", "c"], "small": [0, 0, 1], "SOC_MIN_INCOME": [12.0, 8.0, 30.0],
                        "PROT_SOCIAL": [0.0, math.nan, 0.0]})
    criteria = [{"indicator": "SOC_MIN_INCOME", "op": ">=", "threshold": "city_value"},
                 {"indicator": "PROT_SOCIAL", "op": "<", "threshold": 50}]
    r = evaluate(districts, criteria, {"SOC_MIN_INCOME": 11.3}, DECIMALS).set_index("area")
    assert list(r.index) == ["a", "b"]
    assert r.loc["a", "met"] == 2 and r.loc["a", "full"] == 1
    assert r.loc["b", "met"] == 0 and r.loc["b", "full"] == 0


def test_evaluate_quarters_without_a_small_rule():
    quarters = pd.DataFrame({"id": ["Gallus", "Nied"], "SOC_MIN_INCOME": [12.0, 8.0]})
    r = evaluate(quarters, [{"indicator": "SOC_MIN_INCOME", "op": ">=", "threshold": "city_value"}], {"SOC_MIN_INCOME": 11.3}, DECIMALS)
    assert r.to_dict("records") == [{"area": "Gallus", "met": 1, "full": 1}, {"area": "Nied", "met": 0, "full": 0}]


def test_threshold_from_the_city_value_of_another_indicator():
    k = {"indicator": "OWN_PUBLIC_HIGH", "city": "OWN_PUBLIC", "op": "<", "threshold": CITY_VALUE}
    assert threshold(k, {"OWN_PUBLIC": 18.3}) == 18.3


def test_upper_end_decides():
    areas = pd.DataFrame({"id": ["Bonames", "Hausen"], "OWN_PUBLIC_HIGH": [22.5, 10.0]})
    crit = [{"indicator": "OWN_PUBLIC_HIGH", "city": "OWN_PUBLIC", "op": "<", "threshold": CITY_VALUE}]
    assert evaluate(areas, crit, {"OWN_PUBLIC": 18.3}, DECIMALS)["full"].tolist() == [0, 1]


def test_ownership_templates_check_the_upper_end():
    t = {x["id"]: x for x in TEMPLATES}

    def without_label(k):
        return {key: value for key, value in k.items() if key != "label"}

    assert {"indicator": "OWN_PUBLIC_HIGH", "city": "OWN_PUBLIC", "op": "<", "threshold": CITY_VALUE,
            "note": UPPER_END_NOTE} in [without_label(k) for k in t["public_company"]["criteria"]]
    assert without_label(t["coop"]["criteria"][0]) == {"indicator": "OWN_COOP_HIGH", "city": "OWN_COOP", "op": "<",
                                                       "threshold": CITY_VALUE, "note": UPPER_END_NOTE}


def test_shown_rounds_half_up():
    assert shown(0.25, 1) == 0.3 and shown(2.5, 0) == 3 and shown(79.94, 1) == 79.9 and shown(-0.25, 1) == -0.2


def test_equal_after_rounding_meets():
    """The map shows 79,9 for both: the area meets „at or above the city value“."""
    areas = pd.DataFrame({"id": ["a"], "HOU_RENTERS": [79.94]})
    crit = [{"indicator": "HOU_RENTERS", "op": ">=", "threshold": CITY_VALUE}]
    assert evaluate(areas, crit, {"HOU_RENTERS": 79.86}, {"HOU_RENTERS": 1})["met"].tolist() == [1]
    assert evaluate(areas.assign(HOU_RENTERS=79.86), crit, {"HOU_RENTERS": 79.94}, {"HOU_RENTERS": 1})["met"].tolist() == [1]
    assert evaluate(areas.assign(HOU_RENTERS=79.86), crit, {"HOU_RENTERS": 79.94}, {"HOU_RENTERS": 2})["met"].tolist() == [0]


def test_rank_not_rounded():
    areas = pd.DataFrame({"id": ["a"], "LAND_RANK": [44.5]})
    crit = [{"indicator": "LAND_RANK", "op": ">=", "threshold": 45}]
    assert evaluate(areas, crit, {}, {"LAND_RANK": 0}, ranked={"LAND_RANK"})["met"].tolist() == [0]
    assert evaluate(areas, crit, {}, {"LAND_RANK": 0})["met"].tolist() == [1]  # as a plain number 44.5 shows 45


def test_a_criterion_on_a_range_uses_the_decimals_of_its_city_indicator():
    areas = pd.DataFrame({"id": ["a"], "OWN_COOP_HIGH": [10.04]})
    crit = [{"indicator": "OWN_COOP_HIGH", "city": "OWN_COOP", "op": "<", "threshold": CITY_VALUE}]
    assert evaluate(areas, crit, {"OWN_COOP": 10.0}, {"OWN_COOP": 1})["met"].tolist() == [0]  # 10,0 is not below 10,0
    assert evaluate(areas, crit, {"OWN_COOP": 10.1}, {"OWN_COOP": 1})["met"].tolist() == [1]
    assert evaluate(areas, crit, {"OWN_COOP": 10.04}, {"OWN_COOP": 2})["met"].tolist() == [0]
