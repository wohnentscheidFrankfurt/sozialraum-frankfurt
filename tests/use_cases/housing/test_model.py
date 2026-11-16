import numpy as np
import pandas as pd
import pytest

from pipeline.shared.core.grid import km_cell
from pipeline.use_cases.housing.model import fill_rate, housing_coverage, housing_values, renter_parts, vacancy_parts


def _cells():
    return pd.DataFrame({
        "pop": [100, 300], "dwellings": [50, 150], "vacancy_rate": [0.0, 10.0], "owner_rate": [20.0, np.nan],
        "rent_sqm": [10.0, 14.0], "rented_dwellings": [40, 120],
        "vacancy_rate_market": [2.0, np.nan]})


def test_housing_values():
    k = housing_values(_cells())
    assert k["HOU_RENTERS"] == pytest.approx(80)            # only cell 1 has a rate
    assert housing_coverage(_cells())["COV_HOU_RENTERS"] == pytest.approx(100 * 50 / 185)
    assert k["HOU_RENT"] == pytest.approx(13.0)         # (10 * 40 + 14 * 120) / 160
    assert k["HOU_VACANT_MARKET"] == 2.0
    assert list(k) == ["HOU_RENTERS", "HOU_RENT", "HOU_VACANT_MARKET", "HOU_VACANT_ALL",
                       "HOU_VACANT_MARKET_DWELLINGS", "HOU_VACANT_ALL_DWELLINGS"]
    assert list(housing_coverage(_cells())) == ["COV_HOU_RENTERS", "COV_HOU_RENT", "COV_HOU_VACANT_MARKET",
                                                "COV_HOU_VACANT_ALL"]


def test_housing_values_vacancy_all():
    k = housing_values(_cells())
    assert k["HOU_VACANT_ALL"] == pytest.approx(7.5)      # (0 * 50 + 10 * 150) / 200, weighted by dwellings
    assert housing_coverage(_cells())["COV_HOU_VACANT_ALL"] == pytest.approx(100.0)
    z = _cells()
    z.loc[1, "vacancy_rate"] = np.nan                      # cell missing in the file: no value, not 0
    assert housing_values(z)["HOU_VACANT_ALL"] == 0.0
    assert housing_coverage(z)["COV_HOU_VACANT_ALL"] == pytest.approx(25.0)


def test_housing_values_vacant_dwellings():
    k = housing_values(_cells())
    assert k["HOU_VACANT_ALL_DWELLINGS"] == pytest.approx(15.0)      # 0 % of 50 + 10 % of 150
    assert k["HOU_VACANT_MARKET_DWELLINGS"] == pytest.approx(1.0)    # 2 % of 50; the NaN rate counts 0
    z = _cells()
    z.loc[0, "dwellings"] = np.nan                                   # NaN dwellings count 0
    assert housing_values(z)["HOU_VACANT_MARKET_DWELLINGS"] == 0.0
    z["vacancy_rate"] = np.nan                                       # no cell with a rate: no count
    z["vacancy_rate_market"] = np.nan
    k = housing_values(z)
    assert k["HOU_VACANT_ALL_DWELLINGS"] is None and k["HOU_VACANT_MARKET_DWELLINGS"] is None


def test_housing_values_weight_by_occupied_dwellings():
    g = pd.DataFrame({"dwellings": [100, 100], "vacancy_rate": [0.0, 50.0], "owner_rate": [20.0, None],
                      "rent_sqm": [10.0, 12.0], "rented_dwellings": [80, 20],
                      "pop": [200, 100], "vacancy_rate_market": [1.0, 3.0]})
    z = housing_values(g)
    assert z["HOU_RENTERS"] == pytest.approx(80.0)
    assert housing_coverage(g)["COV_HOU_RENTERS"] == pytest.approx(100 * 100 / 150)
    assert z["HOU_RENT"] == pytest.approx((80 * 10 + 20 * 12) / 100)
    assert z["HOU_VACANT_ALL"] == pytest.approx(25.0)


def _km_cells(rates, dwellings, dash):
    """Cells of one 1 km cell (ids N...E4222...)."""
    return pd.DataFrame({"cell_id": [f"CRS3035RES100mN3002{i}00E4222000" for i in range(len(rates))],
                         "dwellings": dwellings, "vacancy_rate": rates, "vacancy_rate_dash": dash})


def test_fill_rate_spreads_rest_over_dash_cells():
    g = _km_cells([5.0, 0.0, 0.0], [100, 100, 200], [0, 1, 1])
    km = km_cell(g.loc[0, "cell_id"])
    out = fill_rate(g, "vacancy_rate", "vacancy_rate_dash", {km: 4.0})
    # vacant in the km cell 16, known 5, rest 11 over 300 dwellings of the dash cells
    assert list(out.index) == list(g.index)
    assert out.tolist() == pytest.approx([5.0, 100 * 11 / 300, 100 * 11 / 300])
    assert (out * g["dwellings"] / 100).sum() == pytest.approx(16.0)


def test_fill_rate_negative_rest_is_zero():
    g = _km_cells([5.0, 0.0, 0.0], [100, 100, 200], [0, 1, 1])
    out = fill_rate(g, "vacancy_rate", "vacancy_rate_dash", {km_cell(g.loc[0, "cell_id"]): 1.0})
    assert out.tolist() == [5.0, 0.0, 0.0]


def test_fill_rate_without_dash_cells_keeps_values():
    g = _km_cells([5.0, 2.0], [100, 100], [0, 0])
    out = fill_rate(g, "vacancy_rate", "vacancy_rate_dash", {km_cell(g.loc[0, "cell_id"]): 9.0})
    assert out.tolist() == [5.0, 2.0]


def test_fill_rate_balances_each_km_cell_apart():
    a = _km_cells([0.0, 4.0], [100, 100], [1, 0])
    b = a.assign(cell_id=a["cell_id"].str.replace("E4222000", "E4223000"))
    g = pd.concat([a, b], ignore_index=True)
    km_a, km_b = km_cell(a.loc[0, "cell_id"]), km_cell(b.loc[0, "cell_id"])
    out = fill_rate(g, "vacancy_rate", "vacancy_rate_dash", {km_a: 4.0, km_b: 6.0})
    assert out.tolist() == pytest.approx([4.0, 4.0, 8.0, 4.0])


def test_fill_rate_km_cell_without_rate_keeps_values():
    g = _km_cells([5.0, 0.0], [100, 100], [0, 1])
    assert fill_rate(g, "vacancy_rate", "vacancy_rate_dash", {}).tolist() == [5.0, 0.0]


def _filled():
    """Filled rates: cell 2 is a „–“ cell with a rate from the 1 km grid, cell 3 a „–“ cell without, cell 4 has no
    dwellings."""
    return pd.DataFrame({"dwellings": [100, 50, 80, np.nan], "vacancy_rate": [4.0, 10.0, np.nan, 3.0],
                         "vacancy_rate_dash": [0, 1, 1, 0], "owner_rate": [20.0, 50.0, np.nan, 10.0]})


def test_vacancy_parts_add_up_to_the_count():
    g = _filled()
    fields, km, dwellings = vacancy_parts(g, "vacancy_rate", "vacancy_rate_dash")
    k = housing_values(g.assign(vacancy_rate_market=np.nan, rent_sqm=np.nan, rented_dwellings=np.nan))
    assert (fields, km, dwellings) == pytest.approx((4.0, 5.0, 150.0))
    assert fields + km == pytest.approx(k["HOU_VACANT_ALL_DWELLINGS"])
    assert 100 * (fields + km) / dwellings == pytest.approx(k["HOU_VACANT_ALL"])


def test_renter_parts_give_the_share():
    g = _filled()
    occupied, owners = renter_parts(g)
    k = housing_values(g.assign(vacancy_rate_market=np.nan, rent_sqm=np.nan, rented_dwellings=np.nan))
    assert (occupied, owners) == pytest.approx((96 + 45, 0.2 * 96 + 0.5 * 45))  # cell 3 has no owner rate
    assert 100 - 100 * owners / occupied == pytest.approx(k["HOU_RENTERS"])
