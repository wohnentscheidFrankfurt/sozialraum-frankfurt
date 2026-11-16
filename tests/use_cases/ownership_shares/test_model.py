import re

import pandas as pd
import pytest

from pipeline import config
from pipeline.use_cases.ownership_shares.checks import check_ownership_shares
from pipeline.use_cases.ownership_shares.model import (BACKTEST_AREAS, BACKTEST_HITS, HALF_POINTS, OTHER_GROUPS,
                                                       DWELLING_COLUMNS, GROUP_IDS, building_counts, by_quarter,
                                                       city_total, group_dwellings, group_shares, half_points,
                                                       quarter_values,
                                                       require_quarters)
from pipeline.shared.zensus.model import CLASSES

ALL = ("OWN_PUBLIC", "OWN_COOP", *OTHER_GROUPS)


def _dw(**kw):
    return {**{k: 0.0 for k in CLASSES}, **kw}


def test_public_and_coop_from_their_use_cases_the_rest_split_in_proportion():
    # known 200: ABG+NH 70, coops 30; the rest 100 goes to company and person in proportion 40 : 60 of their estimate
    z = group_shares(_dw(municipal=50.0, coop=10.0, housing_company=40.0, person=60.0, condo=40.0),
                     {"value": 70.0, "half": 10.0}, {"value": 30.0, "half": 3.0}, 200.0)
    assert z["OWN_PUBLIC"] == pytest.approx(35.0) and z["OWN_COOP"] == pytest.approx(15.0)
    assert z["OWN_COMPANY"] == pytest.approx(100 * (100 * 40 / 140) / 200)
    assert z["OWN_PERSON"] == pytest.approx(100 * (100 * 100 / 140) / 200)
    assert sum(z[g] for g in ALL) == pytest.approx(100)


def test_unassigned_dwellings_go_to_the_four_other_groups():
    # known 200, total 250: ABG+NH 70 and coops 30 keep their count; the rest 150 goes 40 : 100 to company and person
    z = group_shares(_dw(municipal=50.0, coop=10.0, housing_company=40.0, person=60.0, condo=40.0),
                     {"value": 70.0, "half": 10.0}, {"value": 30.0, "half": 3.0}, 250.0)
    assert z["OWN_PUBLIC"] == pytest.approx(28.0) and z["OWN_COOP"] == pytest.approx(12.0)
    assert z["OWN_COMPANY"] == pytest.approx(100 * (150 * 40 / 140) / 250)
    assert sum(z[g] for g in ALL) == pytest.approx(100)
    assert (z["OWN_PUBLIC_LOW"], z["OWN_PUBLIC_HIGH"]) == (pytest.approx(24.0), pytest.approx(32.0))


def test_group_dwellings_add_up_to_all_dwellings():
    z = group_dwellings(_dw(municipal=300.0, housing_company=200.0, person=400.0),
                        {"value": 300.0, "half": 30.0}, {"value": 0.0, "half": 0.0}, 1000.0)
    assert sum(z[f"{g}_DWELLINGS"] for g in GROUP_IDS) == pytest.approx(1000)
    assert z["OWN_PUBLIC_DWELLINGS"] == pytest.approx(300)
    assert z["OWN_COMPANY_DWELLINGS_HIGH"] - z["OWN_COMPANY_DWELLINGS"] == pytest.approx(35.0)  # 3.5 points of 1,000


def test_quarter_values_divide_by_all_dwellings():
    # 80 of 100 dwellings have an owner: the share of Privatpersonen is 100 %, its count 100, the coverage 80 %
    g = pd.DataFrame([{**{f"dw_{k}": 0.0 for k in CLASSES}, **{f"bld_{k}": 0 for k in CLASSES},
                       "dw_person": 80.0, "bld_person": 3, "dwellings": 100}])
    z = quarter_values(g, {"value": 0.0, "half": 0.0}, {"value": 0.0, "half": 0.0})
    assert z["COV_OWN"] == pytest.approx(80.0) and z["OWN_PERSON"] == pytest.approx(100.0)
    assert z["OWN_PERSON_DWELLINGS"] == pytest.approx(100.0)


def test_half_points_without_dwellings_are_empty():
    assert set(half_points({"value": 0.0, "half": 0.0}, {"value": 0.0, "half": 0.0}, 0.0)) == set(GROUP_IDS)
    assert set(half_points({"value": 0.0, "half": 0.0}, {"value": 0.0, "half": 0.0}, 0.0).values()) == {None}


def test_ranges():
    z = group_shares(_dw(person=180.0, state=1.0, nonprofit=19.0), {"value": 0.0, "half": 0.0},
                     {"value": 20.0, "half": 4.0}, 200.0)
    assert (z["OWN_COOP_LOW"], z["OWN_COOP_HIGH"]) == (pytest.approx(8.0), pytest.approx(12.0))
    assert z["OWN_PERSON_HIGH"] == pytest.approx(z["OWN_PERSON"] + HALF_POINTS["OWN_PERSON"])
    assert z["OWN_STATE_LOW"] == 0.0  # 0.45 % − 1.4 points ends at 0
    assert (z["OWN_PUBLIC_LOW"], z["OWN_PUBLIC_HIGH"]) == (0.0, 0.0)
    assert HALF_POINTS == {"OWN_COMPANY": 3.5, "OWN_PERSON": 5.4, "OWN_STATE": 1.4, "OWN_NONPROFIT": 2.0}


def test_upper_end_stops_at_100():
    z = group_shares(_dw(person=100.0), {"value": 0.0, "half": 0.0}, {"value": 0.0, "half": 0.0}, 100.0)
    assert z["OWN_PERSON"] == pytest.approx(100.0) and z["OWN_PERSON_HIGH"] == 100.0


def test_rest_without_any_other_group_is_not_divided_by_zero():
    # review focus 1: the rest cannot be distributed; the shares do not add up to 100 and the check fails later
    z = group_shares(_dw(coop=100.0), {"value": 0.0, "half": 0.0}, {"value": 60.0, "half": 0.0}, 100.0)
    assert z["OWN_COOP"] == pytest.approx(60.0) and all(z[g] == 0.0 for g in OTHER_GROUPS)
    assert check_ownership_shares(pd.DataFrame([{**z, "name": "X"}])).status == "FAIL"


def test_no_dwellings_give_no_shares():
    z = group_shares(_dw(), {"value": 0.0, "half": 0.0}, {"value": 0.0, "half": 0.0}, 0.0)
    assert z["OWN_PUBLIC"] is None and z["OWN_PUBLIC_LOW"] is None


def test_quarter_values_add_coverage_and_buildings():
    g = pd.DataFrame([{**{f"dw_{k}": 0.0 for k in CLASSES}, **{f"bld_{k}": 0 for k in CLASSES},
                       "dw_person": 80.0, "bld_person": 3, "dwellings": 100}])
    z = quarter_values(g, {"value": 0.0, "half": 0.0}, {"value": 0.0, "half": 0.0})
    assert z["COV_OWN"] == pytest.approx(80.0) and z["BLD_PERSON"] == 3 and isinstance(z["BLD_PERSON"], int)
    assert z["OWN_PERSON"] == pytest.approx(100.0)
    assert set(DWELLING_COLUMNS) <= set(z) and z["OWN_PERSON_DWELLINGS"] == pytest.approx(100.0)
    assert set(building_counts(g)) == {"BLD_CONDO", "BLD_PERSON", "BLD_COOP", "BLD_MUNICIPAL", "BLD_HOUSING_COMPANY",
                                       "BLD_OTHER_COMPANY", "BLD_STATE", "BLD_NONPROFIT"}


def test_group_dwellings_value_is_share_times_total():
    z = group_dwellings(_dw(municipal=300.0, coop=100.0, housing_company=200.0, person=400.0),
                        {"value": 300.0, "half": 30.0}, {"value": 100.0, "half": 10.0}, 1000.0)
    assert z["OWN_PUBLIC_DWELLINGS"] == pytest.approx(300) and z["OWN_COOP_DWELLINGS"] == pytest.approx(100)
    assert sum(z[f"{g}_DWELLINGS"] for g in GROUP_IDS) == pytest.approx(1000)
    assert z["OWN_PUBLIC_DWELLINGS_HIGH"] == pytest.approx(330)
    assert z["OWN_COMPANY_DWELLINGS_HIGH"] - z["OWN_COMPANY_DWELLINGS"] == pytest.approx(35.0)  # 3.5 points of 1,000
    assert len(DWELLING_COLUMNS) == 18 and set(z) == set(DWELLING_COLUMNS)


def test_group_dwellings_low_is_clipped_at_zero_high_is_not():
    z = group_dwellings(_dw(person=1000.0), {"value": 0.0, "half": 0.0}, {"value": 0.0, "half": 0.0}, 1000.0)
    assert z["OWN_STATE_DWELLINGS"] == 0 and z["OWN_STATE_DWELLINGS_LOW"] == 0
    assert z["OWN_STATE_DWELLINGS_HIGH"] == pytest.approx(HALF_POINTS["OWN_STATE"] / 100 * 1000)


def test_group_dwellings_without_dwellings_are_empty():
    z = group_dwellings(_dw(), {"value": 0.0, "half": 0.0}, {"value": 0.0, "half": 0.0}, 0.0)
    assert set(z) == set(DWELLING_COLUMNS) and all(v is None for v in z.values())


def test_tables_per_quarter_and_city():
    t = pd.DataFrame({"quarter": ["A", "B"], "coop_value": [10.0, 5.0], "coop_half": [1.0, 0.0]})
    assert by_quarter(t, "coop_value", "coop_half") == {"A": {"value": 10.0, "half": 1.0},
                                                        "B": {"value": 5.0, "half": 0.0}}
    assert city_total(t, "coop_value") == {"value": 15.0, "half": 0.0}


def test_require_quarters_names_the_step():
    with pytest.raises(ValueError, match=r"Genossenschaften in \['B'\].*--step coops"):
        require_quarters(["A", "B"], {"A": {}}, "Genossenschaften", "coops")


def test_backtest_hits_follow_the_formula_review():
    """The Unsicherheit names „40 von 45“: in the backtest on 2011 the fixed half range of every group holds the count
    in 40 of 45 Stadtteile (research/results/formula_review.txt, round 2)."""
    text = (config.ROOT / "research" / "results" / "formula_review.txt").read_text(encoding="utf-8")
    found = {float(p): (int(areas), int(hits))
             for areas, p, hits in re.findall(r"Stadtteile covered of (\d+): .*?fixed (\d+\.\d) pp (\d+)", text)}
    assert {found[v] for v in HALF_POINTS.values()} == {(BACKTEST_AREAS, BACKTEST_HITS)}


def test_other_numbers_counts_filled_cells_apart():
    from pipeline.use_cases.ownership_shares.model import other_numbers
    g = pd.DataFrame({f"{p}_{k}": [0.0, 0.0] for p in ("bld", "dw") for k in CLASSES})
    g["dw_from_2011"] = [0.0, 30.0]
    g["dwellings"] = [120, 80]
    g.loc[0, ["bld_state", "dw_state"]] = [5, 50.0]
    g.loc[1, ["bld_state", "dw_state"]] = [2, 30.0]
    g.loc[1, "dw_person"] = 20.0
    n = other_numbers(g, "OWN_STATE", {k: 10.0 for k in CLASSES}, 80.0)
    assert (n.buildings, n.factors, n.from_2011, n.dwellings, n.total) == ({"state": 5}, {"state": 10.0}, 30.0, 80.0,
                                                                          200.0)
