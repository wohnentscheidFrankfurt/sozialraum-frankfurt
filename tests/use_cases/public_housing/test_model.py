"""Public housing per Stadtteil: count of 2011 × change up to 2022 (pipeline/use_cases/public_housing/README.md)."""
import numpy as np
import pandas as pd
import pytest

from pipeline.use_cases.public_housing.model import (P90_CHANGE, estimate_by_size,
                                                     ipf, new_research_sites, public_housing, public_range,
                                                     research_cells, size_tables)
from pipeline.shared.zensus.model import CLASSES, SIZES


def test_ipf_keeps_both_margins():
    seed = np.array([[4.0, 1.0], [1.0, 4.0]])
    m = ipf(seed, np.array([3.0, 7.0]), np.array([6.0, 4.0]))
    assert m.sum(axis=1) == pytest.approx([3, 7]) and m.sum(axis=0) == pytest.approx([6, 4])


def test_ipf_scales_the_size_margin_to_the_owner_total():
    # secrecy: buildings per owner and per size do not add up to the same total
    m = ipf(np.ones((2, 2)), np.array([2.0, 2.0]), np.array([1.0, 1.0]))
    assert m.sum() == pytest.approx(4) and m.sum(axis=1) == pytest.approx([2, 2])


def test_ipf_without_sizes_uses_the_seed_of_the_owners():
    seed = np.array([[1.0, 3.0], [5.0, 5.0]])
    m = ipf(seed, np.array([4.0, 0.0]), np.array([0.0, 0.0]))
    assert m[0] == pytest.approx([1, 3]) and m[1] == pytest.approx([0, 0])


def test_ipf_without_a_start_value_spreads_by_both_margins():
    # Frankfurt has no building of this owner in this size class: the margins alone decide
    seed = np.array([[0.0, 0.0], [1.0, 1.0]])
    m = ipf(seed, np.array([2.0, 0.0]), np.array([1.0, 3.0]))
    assert m[0] == pytest.approx([0.5, 1.5]) and m[1] == pytest.approx([0, 0])


def test_ipf_without_owners_is_zero():
    assert ipf(np.ones((2, 2)), np.zeros(2), np.ones(2)).sum() == 0


def _tables():
    """Frankfurt: municipal buildings have 20 dwellings in class 13+, persons 1 in class 1 and no large building."""
    zero = {s: 0 for s in SIZES}
    buildings = {k: dict(zero) for k in CLASSES}
    dwellings = {k: dict(zero) for k in CLASSES}
    buildings["municipal"]["13_plus"], dwellings["municipal"]["13_plus"] = 10, 200
    buildings["person"]["1"], dwellings["person"]["1"] = 10, 10
    return size_tables(buildings, dwellings)


def test_size_tables():
    seed, mean = _tables()
    m, p, big = CLASSES.index("municipal"), CLASSES.index("person"), SIZES.index("13_plus")
    assert seed.shape == mean.shape == (8, 5)
    assert mean[m, big] == 20 and mean[p, 0] == 1
    assert mean[p, big] == 0 and mean[0, 0] == 0  # no buildings: no mean, no division by zero


def test_estimate_by_size_gives_the_large_building_to_its_owner():
    seed, mean = _tables()
    owners = pd.DataFrame([{k: 0 for k in CLASSES} | {"municipal": 1, "person": 3}], index=["c"])
    sizes = pd.DataFrame([{s: 0 for s in SIZES} | {"1": 3, "13_plus": 1}], index=["c"])
    est = estimate_by_size(owners, sizes, pd.Series([23.0], index=["c"]), seed, mean)
    assert est.loc["c"].sum() == pytest.approx(23)
    assert est.loc["c", "municipal"] == pytest.approx(20) and est.loc["c", "person"] == pytest.approx(3)


def _cells(rows):
    base = {"quarter": "Q", "dwellings": 0, "dw_total_2011": 0}
    base |= {f"bld_{k}": 0 for k in CLASSES} | {f"dw_{k}_2011": 0 for k in CLASSES} | {f"bld_{k}_2011": 0 for k in CLASSES}
    return pd.DataFrame([base | r for r in rows]).set_index("cell_id")


def _est(values: dict[str, dict]):
    return pd.DataFrame([{k: 0.0 for k in CLASSES} | v for v in values.values()], index=list(values))


def test_count_of_2011_times_the_change_of_the_quarter():
    cells = _cells([
        {"cell_id": "a", "dwellings": 110, "dw_total_2011": 100, "bld_municipal": 10, "bld_municipal_2011": 10,
         "dw_municipal_2011": 100},
        {"cell_id": "b", "dwellings": 50, "dw_total_2011": 50, "bld_municipal": 5, "bld_state_2011": 5,
         "dw_state_2011": 50}])
    e11 = _est({"a": {"municipal": 90.0}, "b": {"state": 50.0}})
    e22 = _est({"a": {"municipal": 99.0}, "b": {"municipal": 55.0}})
    q = public_housing(cells, e11, e22, [])
    factor = (99 + 55) / (90 + 50)
    assert q.loc["Q", "factor"] == pytest.approx(factor)
    assert q.loc["Q", "abg"] == pytest.approx(100 * factor) and q.loc["Q", "nh"] == pytest.approx(50 * factor)
    assert q.loc["Q", "public"] == pytest.approx(150 * factor)
    assert q.loc["Q", "public_additive"] == pytest.approx(150 + 154 - 140)
    assert q.loc["Q", "scaled_2011"] == pytest.approx(150)  # the count the factor scales


def test_state_2011_counts_as_nh_only_where_the_cell_is_municipal_in_2022():
    cells = _cells([{"cell_id": "a", "dwellings": 40, "dw_total_2011": 40, "bld_state": 4, "bld_state_2011": 4,
                     "dw_state_2011": 40}])
    q = public_housing(cells, _est({"a": {"state": 40.0}}), _est({"a": {"state": 40.0}}), [])
    assert q.loc["Q", "nh"] == 0 and q.loc["Q", "public"] == 0


def test_factor_one_without_a_cell_known_in_both_years():
    # owners of 2011 secret: no estimate 2011, the count stays as it is
    cells = _cells([{"cell_id": "a", "dwellings": 60, "dw_total_2011": 60, "bld_municipal": 6, "dw_municipal_2011": 60}])
    q = public_housing(cells, _est({"a": {}}), _est({"a": {"municipal": 30.0}}), [])
    assert q.loc["Q", "factor"] == 1 and q.loc["Q", "public"] == 60


def test_cells_without_owner_2022_keep_the_count_up_to_their_dwellings():
    cells = _cells([{"cell_id": "a", "dwellings": 40, "dw_total_2011": 80, "bld_municipal_2011": 8,
                     "dw_municipal_2011": 60, "dw_state_2011": 20}])
    q = public_housing(cells, _est({"a": {"municipal": 60.0}}), _est({"a": {}}), [])
    assert q.loc["Q", "abg"] == pytest.approx(30) and q.loc["Q", "nh"] == pytest.approx(10)
    assert q.loc["Q", "scaled_2011"] == 0  # the factor does not scale a cell without owner 2022


def test_dwellings_without_owner_2011_get_the_municipal_share_of_2022():
    cells = _cells([
        {"cell_id": "a", "dwellings": 40, "dw_total_2011": 40, "bld_municipal": 4, "bld_municipal_2011": 3,
         "dw_municipal_2011": 30},  # 10 dwellings without owner in 2011
        {"cell_id": "b", "dwellings": 10, "dw_total_2011": 10, "bld_municipal": 1, "bld_state_2011": 1,
         "dw_state_2011": 10}])
    e = _est({"a": {"municipal": 40.0}, "b": {"municipal": 10.0}})
    q = public_housing(cells, e, e, [])
    assert q.loc["Q", "fill_2011"] == pytest.approx(10)
    # split like the counted base of the quarter: 30 ABG, 10 NH
    assert q.loc["Q", "abg"] == pytest.approx(30 + 7.5) and q.loc["Q", "nh"] == pytest.approx(10 + 2.5)


def test_new_cells_and_research_sites():
    cells = _cells([
        {"cell_id": "n1", "dwellings": 100, "bld_municipal": 2},  # new: E1 finds 40
        {"cell_id": "n2", "dwellings": 300},  # owner secret in 2022
        {"cell_id": "o", "dwellings": 50, "dw_total_2011": 50, "bld_municipal": 5, "bld_municipal_2011": 5,
         "dw_municipal_2011": 50}])
    e = _est({"n1": {"municipal": 40.0}, "n2": {}, "o": {"municipal": 50.0}})
    sites = [(100, ["n1", "n2", "o"]), (80, ["n1"]), (30, ["o"])]
    q = public_housing(cells, e, e, sites)
    assert q.loc["Q", "new"] == 40
    # first site: 100 against 40 in n1 and n2; second: its only cell is taken, E1 is used up, so all 80 count
    # (two projects in one cell); third: old stock only, its growth is in the factor
    assert q.loc["Q", "research_new"] == 60 + 80
    assert q.loc["Q", "public"] == 50 + 40 + 140


def test_quarter_without_public_stock_is_zero():
    cells = _cells([{"cell_id": "a", "quarter": "R", "dwellings": 20, "bld_person": 2}])
    q = public_housing(cells, _est({"a": {"person": 20.0}}), _est({"a": {"person": 20.0}}), [])
    r = public_range(q, 0, 0)
    assert r.loc["R", ["public", "public_value", "public_half"]].tolist() == [0, 0, 0]


def test_range_parts():
    q = pd.DataFrame({"abg_2011": [100.0, 0.0], "nh_2011": [0.0, 0.0], "abg_scaled": [80.0, 0.0],
                      "nh_scaled": [0.0, 0.0], "abg_fill": [0.0, 0.0], "nh_fill": [0.0, 0.0], "new": [10.0, 0.0],
                      "research_new": [5.0, 0.0], "public_additive": [90.0, 0.0], "fill_2011": [6.0, 0.0],
                      "no_owner_2011": [30.0, 10.0], "abg": [85.0, 0.0], "nh": [0.0, 0.0], "public": [95.0, 0.0]},
                     index=["Q", "R"])
    r = public_range(q, gap_public=46, gap_municipal=10)
    # rest of the gaps: 40 public, 4 municipal; spread 3:1
    assert r["gap_public"].tolist() == [30, 10] and r["gap_municipal"].tolist() == [3, 1]
    # change: 80 - 100 + 10 = -10; 16 % of it is 1.6, the difference to the additive variant 10 is larger
    assert r.loc["Q", "err_change"] == pytest.approx(10)
    assert r.loc["Q", "public_value"] == pytest.approx(98) and r.loc["Q", "public_half"] == pytest.approx(40)
    assert r.loc["Q", "abg_value"] == pytest.approx(85 + 5 + 3)
    assert P90_CHANGE == 0.16


def test_new_research_sites_and_their_cells():
    sites = pd.DataFrame([
        {"id": "s1", "level": "neubau", "dwellings": 100, "precision": "A", "year": 2019, "lon": 8.68, "lat": 50.11},
        {"id": "s2", "level": "neubau", "dwellings": 50, "precision": "Q", "year": 2022, "lon": 8.68, "lat": 50.11},
        {"id": "s3", "level": "bestand", "dwellings": 70, "precision": "A", "year": 2015, "lon": 8.68, "lat": 50.11},
        {"id": "s4", "level": "neubau", "dwellings": 40, "precision": "O", "year": 2015, "lon": 8.68, "lat": 50.11},
        {"id": "s5", "level": "neubau", "dwellings": 30, "precision": "A", "year": 2009, "lon": 8.68, "lat": 50.11}])
    new = new_research_sites(sites)
    assert new["id"].tolist() == ["s1"]
    x, y = new["x"].iat[0], new["y"].iat[0]
    cells = pd.DataFrame({"x25832": [x + 100, x + 200, x], "y25832": [y, y, y + 340]}, index=["near", "far", "edge"])
    assert research_cells(new, cells) == [(100, ["near"])]


def test_research_site_counts_for_the_quarter_of_its_new_cells():
    # the radius reaches more old cells of the neighbour than new cells of its own Stadtteil
    cells = _cells([{"cell_id": "n", "quarter": "A", "dwellings": 80, "bld_municipal": 1}] + [
        {"cell_id": f"o{i}", "quarter": "B", "dwellings": 10, "dw_total_2011": 10, "bld_municipal": 1,
         "bld_municipal_2011": 1, "dw_municipal_2011": 10} for i in range(3)])
    e = _est({"n": {"municipal": 20.0}, **{f"o{i}": {"municipal": 10.0} for i in range(3)}})
    q = public_housing(cells, e, e, [(80, ["n", "o0", "o1", "o2"])])
    assert q.loc["A", "research_new"] == 60 and q.loc["B", "research_new"] == 0


def _range_input(**kw):
    base = {"abg_2011": 0.0, "nh_2011": 0.0, "abg_scaled": 0.0, "nh_scaled": 0.0, "abg_fill": 0.0, "nh_fill": 0.0,
            "new": 0.0, "research_new": 0.0, "public_additive": 0.0, "fill_2011": 0.0, "no_owner_2011": 0.0,
            "abg": 0.0, "nh": 0.0, "public": 0.0}
    return pd.DataFrame([base | kw], index=["Q"])


# scenarios of a Stadtteil (docs/data-rules.md, Uncertainty): which part of the budget sets the half range
PUBLIC_SCENARIOS = [
    # stock unchanged, both variants agree: no range
    ("unchanged stock", dict(abg_2011=1000.0, abg_scaled=1000.0, public_additive=1000.0, abg=1000.0, public=1000.0),
     0, 0, 1000.0, 0.0),
    # stock grew by 500: 16 % of the change (80) is larger than the difference of the variants (20)
    ("large change", dict(abg_2011=1000.0, abg_scaled=1500.0, public_additive=1480.0, abg=1500.0, public=1500.0),
     0, 0, 1500.0, 80.0),
    # small change, the variants differ by 30: the difference sets the range
    ("variants differ", dict(abg_2011=1000.0, abg_scaled=1050.0, public_additive=1020.0, abg=1050.0, public=1050.0),
     0, 0, 1050.0, 30.0),
    # only new cells (no stock 2011): 16 % of the new dwellings
    ("new stock only", dict(new=200.0, public=200.0), 0, 0, 200.0, 32.0),
    # no stock, but the gap of 2011 sits here (all dwellings without an owner): range from the gap only
    ("gap only", dict(no_owner_2011=10.0), 50, 20, 20.0, 50.0),
]


@pytest.mark.parametrize("scenario, parts, gap_public, gap_municipal, value, half", PUBLIC_SCENARIOS,
                         ids=[s for s, *_ in PUBLIC_SCENARIOS])
def test_public_scenario(scenario, parts, gap_public, gap_municipal, value, half):
    r = public_range(_range_input(**parts), gap_public, gap_municipal).iloc[0]
    assert (r["public_value"], r["public_half"]) == (pytest.approx(value), pytest.approx(half))
