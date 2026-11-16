"""Scenarios per ownership form: how the range at the value comes about and which half range the ⓘ names
(docs/data-rules.md, Uncertainty). Every scenario checks the same rules: the half range is in percentage
points, the range is value ± half range, bounded to 0 to 100."""
import pandas as pd
import pytest

from pipeline.use_cases.ownership_shares.model import HALF_POINTS, group_shares, half_points, range_rows
from pipeline.shared.zensus.model import CLASSES


def _dw(**kw):
    return {**{k: 0.0 for k in CLASSES}, **kw}


NONE = {"value": 0.0, "half": 0.0}

# (group, scenario, dwellings per class, ABG and NH, Genossenschaften, share, half range in points)
SCENARIOS = [
    ("OWN_PUBLIC", "large stock, narrow range", _dw(municipal=300.0, person=700.0), {"value": 300.0, "half": 15.0},
     NONE, 30.0, 1.5),
    # Bonames 2022: 532 of 2,890 dwellings, half range 255 (227 the difference of the two variants, 28 the gap of 2011)
    ("OWN_PUBLIC", "small stock, wide range", _dw(municipal=532.0, person=2358.0), {"value": 532.0, "half": 255.0},
     NONE, 100 * 532 / 2890, 100 * 255 / 2890),
    ("OWN_PUBLIC", "range ends at 0", _dw(municipal=10.0, person=990.0), {"value": 10.0, "half": 20.0}, NONE, 1.0, 2.0),
    ("OWN_PUBLIC", "no stock, range from the gap", _dw(person=1000.0), {"value": 0.0, "half": 5.0}, NONE, 0.0, 0.5),
    ("OWN_COOP", "counted only, no range", _dw(coop=200.0, person=800.0), NONE, {"value": 200.0, "half": 0.0},
     20.0, 0.0),
    ("OWN_COOP", "estimated only, 34 % of the value", _dw(coop=100.0, person=900.0), NONE,
     {"value": 100.0, "half": 34.0}, 10.0, 3.4),
    ("OWN_COOP", "counted and estimated", _dw(coop=100.0, person=900.0), NONE, {"value": 100.0, "half": 6.8},
     10.0, 0.68),
    ("OWN_COMPANY", "fixed points", _dw(housing_company=150.0, other_company=50.0, person=800.0), NONE, NONE,
     20.0, 3.5),
    ("OWN_COMPANY", "range ends at 0", _dw(other_company=10.0, person=990.0), NONE, NONE, 1.0, 3.5),
    ("OWN_PERSON", "fixed points", _dw(person=300.0, condo=300.0, housing_company=400.0), NONE, NONE, 60.0, 5.4),
    ("OWN_PERSON", "range ends at 100", _dw(person=980.0, condo=20.0), NONE, NONE, 100.0, 5.4),
    ("OWN_STATE", "small share, range ends at 0", _dw(state=5.0, person=995.0), NONE, NONE, 0.5, 1.4),
    ("OWN_STATE", "no state stock", _dw(person=1000.0), NONE, NONE, 0.0, 1.4),
    # Hausen 2011: 715 dwellings of the group in 3 buildings, the estimate found 7; the range cannot catch that
    ("OWN_NONPROFIT", "fixed points", _dw(nonprofit=30.0, person=970.0), NONE, NONE, 3.0, 2.0),
]


@pytest.mark.parametrize("group, scenario, dwellings, public, coop, share, half", SCENARIOS,
                         ids=[f"{g}: {s}" for g, s, *_ in SCENARIOS])
def test_scenario(group, scenario, dwellings, public, coop, share, half):
    total = sum(dwellings.values())
    z, h = group_shares(dwellings, public, coop, total), half_points(public, coop, total)
    assert z[group] == pytest.approx(share) and h[group] == pytest.approx(half)
    assert z[f"{group}_LOW"] == pytest.approx(max(0.0, share - half))
    assert z[f"{group}_HIGH"] == pytest.approx(min(100.0, share + half))
    assert z[f"{group}_LOW"] <= z[group] <= z[f"{group}_HIGH"]


def test_every_ownership_form_has_a_scenario():
    assert {g for g, *_ in SCENARIOS} == {"OWN_PUBLIC", "OWN_COOP", *HALF_POINTS}


def test_no_dwellings_give_no_half_range():
    assert set(half_points(NONE, NONE, 0.0).values()) == {None}


def test_half_points_of_the_four_other_groups_do_not_depend_on_the_area():
    small, large = half_points(NONE, NONE, 10.0), half_points(NONE, NONE, 1e5)
    assert {g: small[g] for g in HALF_POINTS} == {g: large[g] for g in HALF_POINTS} == HALF_POINTS


def test_range_rows_name_the_smallest_and_largest_half_range():
    halves = pd.DataFrame({"id": ["A", "B", "C"], "OWN_PUBLIC": [0.57, 8.82, 1.1], "OWN_COOP": [0.0, 2.14, None],
                           "OWN_COMPANY": [3.5, 3.5, None]})
    assert range_rows(halves) == [{"indicator": "OWN_PUBLIC", "low": 0.57, "high": 8.82},
                                  {"indicator": "OWN_COOP", "low": 0.0, "high": 2.14},
                                  {"indicator": "OWN_COMPANY", "low": 3.5, "high": 3.5}]


def test_range_rows_skip_a_group_without_any_value():
    halves = pd.DataFrame({"id": ["A"], "OWN_PUBLIC": [None], "OWN_COOP": [1.0]})
    assert range_rows(halves) == [{"indicator": "OWN_COOP", "low": 1.0, "high": 1.0}]
