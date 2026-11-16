import pandas as pd
import pytest

from pipeline.use_cases.ownership_cells.model import GRID_GROUPS, estimate, factors, fill_from_2011, grid_rows
from pipeline.shared.zensus.model import CLASSES
from pipeline.shared.zensus.sources import COLUMNS_2011


def test_factors():
    f = factors({k: 100 for k in CLASSES}, {k: 10 for k in CLASSES} | {"nonprofit": 0})
    assert f["municipal"] == 10.0 and f["nonprofit"] == 0.0


def test_estimate_spreads_by_factor_and_scales_to_the_cell():
    z = pd.DataFrame({"cell_id": ["a", "b"], "dwellings": [120, 7], **{f"bld_{k}": [0, 0] for k in CLASSES}})
    z.loc[0, "bld_municipal"], z.loc[0, "bld_person"] = 1, 10
    f = {k: 1.0 for k in CLASSES} | {"municipal": 15.0, "person": 2.5}
    e = estimate(z, f)
    assert e.loc[0, "dw_municipal"] == pytest.approx(45) and e.loc[0, "dw_person"] == pytest.approx(75)
    assert e.loc[0, "dw_unassigned"] == 0
    assert e.loc[1, "dw_unassigned"] == 7 and e.loc[1, "dw_municipal"] == 0


def _ownership(rows: dict[str, dict]) -> pd.DataFrame:
    """rows: cell id -> {class: dwellings, 'unassigned': unassigned}"""
    return pd.DataFrame([{"cell_id": g, **{f"dw_{k}": float(w.get(k, 0)) for k in CLASSES}, "dw_unassigned": w.get("unassigned", 0)}
                         for g, w in rows.items()])


def _cells_2011(rows: dict[str, dict]) -> pd.DataFrame:
    return pd.DataFrame([{"cell_id": g, **{s: 0 for s in COLUMNS_2011[1:]},
                          **{f"dw_{k}_2011": v for k, v in w.items()}} for g, w in rows.items()])


def test_fill_shrinks_to_the_dwellings_2022():
    ownership = _ownership({"a": {"unassigned": 100}})
    e11 = _cells_2011({"a": {"municipal": 120, "person": 40, "state": 40}})  # 200 dwellings 2011
    d = fill_from_2011(ownership, pd.DataFrame({"cell_id": ["a"], "dwellings": [100]}), e11).iloc[0]
    assert d["dw_municipal"] == pytest.approx(80) and d["dw_person"] == pytest.approx(20)  # (120 + 40) / 2
    assert d["dw_state"] == 0 and d["dw_nh_2011"] == pytest.approx(20)
    assert d["dw_unassigned"] == pytest.approx(0) and d["dw_from_2011"] == pytest.approx(100)


def test_fill_spreads_no_more_than_2011_after_new_building():
    ownership = _ownership({"a": {"unassigned": 150}})
    d = fill_from_2011(ownership, pd.DataFrame({"cell_id": ["a"], "dwellings": [150]}), _cells_2011({"a": {"coop": 60, "municipal": 40}})).iloc[0]
    assert d["dw_coop"] == 60 and d["dw_municipal"] == 40 and d["dw_from_2011"] == 100
    assert d["dw_unassigned"] == pytest.approx(50) and d["dw_nh_2011"] == 0


def test_fill_keeps_cells_with_ownership_type_or_without_2011():
    ownership = _ownership({"with": {"person": 30, "state": 5}, "without11": {"unassigned": 70}, "empty11": {"unassigned": 9}})
    cells = pd.DataFrame({"cell_id": ["with", "without11", "empty11"], "dwellings": [35, 70, 9]})
    d = fill_from_2011(ownership, cells, _cells_2011({"with": {"municipal": 99}, "empty11": {}})).set_index("cell_id")
    assert d.loc["with", "dw_person"] == 30 and d.loc["with", "dw_state"] == 5 and d.loc["with", "dw_municipal"] == 0
    assert d.loc["without11", "dw_unassigned"] == 70 and d.loc["empty11", "dw_unassigned"] == 9
    assert (d[["dw_from_2011", "dw_nh_2011"]] == 0).all().all()


def test_fill_keeps_sum_order_and_index():
    ownership = _ownership({"b": {"unassigned": 40}, "a": {"person": 10}, "c": {"unassigned": 25}})
    ownership.index = [7, 3, 5]
    cells = pd.DataFrame({"cell_id": ["c", "a", "b"], "dwellings": [25, 10, 40]})
    e11 = _cells_2011({"x": {"municipal": 500}, "c": {"condo": 10, "nonprofit": 5}, "b": {"housing_company": 80, "state": 20}})
    d = fill_from_2011(ownership, cells, e11)
    assert list(d["cell_id"]) == ["b", "a", "c"] and list(d.index) == [0, 1, 2]
    total = d[[f"dw_{k}" for k in CLASSES]].sum(axis=1) + d["dw_unassigned"]
    assert total.tolist() == pytest.approx([40, 10, 25])
    assert (d[[f"dw_{k}" for k in CLASSES] + ["dw_unassigned", "dw_from_2011", "dw_nh_2011"]] >= 0).all().all()
    assert d.loc[0, "dw_municipal"] == pytest.approx(8) and d.loc[0, "dw_nh_2011"] == pytest.approx(8)


def test_fill_leaves_no_rounding_rest():
    ownership = _ownership({"a": {"unassigned": 1}})
    d = fill_from_2011(ownership, pd.DataFrame({"cell_id": ["a"], "dwellings": [1]}), _cells_2011({"a": {"person": 49}})).iloc[0]
    assert d["dw_unassigned"] == 0.0 and d["dw_person"] == pytest.approx(1)  # 1 - 49 * (1/49) would be 1e-16


def test_fill_accepts_integer_class_columns():
    ownership = _ownership({"a": {"unassigned": 10}, "b": {"person": 3}})
    for k in CLASSES:
        ownership[f"dw_{k}"] = ownership[f"dw_{k}"].astype(int)
    cells = pd.DataFrame({"cell_id": ["a", "b"], "dwellings": [10, 3]})
    d = fill_from_2011(ownership, cells, _cells_2011({"a": {"municipal": 30, "person": 10}}))
    assert d.loc[0, "dw_municipal"] == pytest.approx(7.5) and d.loc[0, "dw_person"] == pytest.approx(2.5)
    assert d.loc[1, "dw_person"] == 3


def test_fill_keeps_dwellings_of_a_cell_without_data_2022():
    ownership = _ownership({"a": {"unassigned": 3}})
    d = fill_from_2011(ownership, pd.DataFrame({"cell_id": ["x"], "dwellings": [5]}), _cells_2011({"a": {"person": 9}})).iloc[0]
    assert d["dw_unassigned"] == 3 and d["dw_person"] == 0  # no dwellings 2022: no fill, nothing gets lost


def _grid_cell(x, **values):
    row = {"x3035": x, "y3035": 3000050.0, **{f"dw_{k}": 0.0 for k in CLASSES}, **{f"bld_{k}": 0 for k in CLASSES},
           **{f"dw_{k}_2011": 0 for k in CLASSES}}
    return {**row, **values}


def test_grid_rows_show_counted_buildings_and_the_estimated_colour():
    cells = pd.DataFrame([_grid_cell(4000050.0, dw_municipal=60.0, dw_person=20.0, bld_municipal=1, bld_person=4)])
    row = grid_rows(cells)[0]
    assert row[4] == GRID_GROUPS.index("OWN_PUBLIC")  # colour: most estimated dwellings
    assert row[5] == 0  # counts are buildings 2022
    counts = dict(zip(GRID_GROUPS, row[6:]))
    assert counts["OWN_PUBLIC"] == 1 and counts["OWN_PERSON"] == 4 and sum(counts.values()) == 5


def test_grid_rows_of_a_cell_without_owner_2022_show_dwellings_2011():
    cells = pd.DataFrame([_grid_cell(4000050.0, dw_municipal=120.0, dw_municipal_2011=80, dw_state_2011=40)])
    row = grid_rows(cells)[0]
    counts = dict(zip(GRID_GROUPS, row[6:]))
    assert row[5] == 1 and counts["OWN_PUBLIC"] == 80 and counts["OWN_STATE"] == 40


def test_grid_rows_keep_the_threshold_of_estimated_dwellings():
    cells = pd.DataFrame([_grid_cell(4000050.0, dw_person=9.0, bld_person=5)])
    assert grid_rows(cells) == []


def test_grid_rows_compare_the_estimate_rounded_so_float_noise_does_not_decide():
    noisy = pd.DataFrame([_grid_cell(4000050.0, dw_person=10.0 - 2e-15, bld_person=5)])  # 9.999999999999998
    low = pd.DataFrame([_grid_cell(4000050.0, dw_person=9.99, bld_person=5)])
    assert len(grid_rows(noisy)) == 1 and grid_rows(low) == []


def test_grid_rows_hold_integers_that_decode_to_the_rounded_corners():
    from pipeline.shared.core.geometry import from_3035_to_wgs84
    from pipeline.use_cases.ownership_cells.model import GRID_SCALE
    xs = [4000050.0, 4000150.0, 4226850.0]
    cells = pd.DataFrame([_grid_cell(x, dw_person=30.0, bld_person=3) for x in xs])
    rows = grid_rows(cells)
    assert len(rows) == 3 and GRID_SCALE == 100000
    for x, (s, w, dn, de, *_rest) in zip(xs, rows):
        assert all(isinstance(v, int) for v in (s, w, dn, de))
        west, south = from_3035_to_wgs84(x - 50.0, 3000050.0 - 50.0)
        east, north = from_3035_to_wgs84(x + 50.0, 3000050.0 + 50.0)
        assert s / GRID_SCALE == round(float(south), 5) and w / GRID_SCALE == round(float(west), 5)
        assert (s + dn) / GRID_SCALE == round(float(north), 5) and (w + de) / GRID_SCALE == round(float(east), 5)


def test_grid_factors_match_factors():
    from pipeline.use_cases.ownership_cells.model import grid_factors
    cells = pd.DataFrame({f"bld_{k}": [1, 3] for k in CLASSES})
    dwellings = {k: 40 for k in CLASSES}
    assert grid_factors(cells, dwellings) == factors(dwellings, {k: 4 for k in CLASSES})
