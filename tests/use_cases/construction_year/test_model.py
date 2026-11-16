import numpy as np
import pandas as pd
import pytest

from pipeline.use_cases.construction_year.model import construction_parts, construction_values

GRID_2011 = {"pre1919": 64223, "1949_1978": 185741}  # dwellings 2011 in the grid


def _cells():
    return pd.DataFrame({
        "dwellings": [50, 150],
        # Zensus 2011 (pipeline/use_cases/construction_year/README.md); the second cell has no 2011 row
        "dw_total_2011": [40, np.nan], "dw_pre1919_2011": [10, np.nan], "dw_1949_1978_2011": [20, np.nan]})


def test_construction_values_class_2011_over_dwellings_2022():
    g = pd.DataFrame({"dwellings": [100, 100], "dw_pre1919_2011": [30, None], "dw_1949_1978_2011": [50, 50]})
    assert construction_values(g) == {"HOU_PRE1919": 15.0, "HOU_PRE1919_DWELLINGS": 30,
                                      "HOU_1949_1978": 50.0, "HOU_1949_1978_DWELLINGS": 100}


def test_construction_values():
    """pipeline/use_cases/construction_year/README.md: dwellings of the class in 2011 ÷ dwellings in 2022 (50 + 150)."""
    k = construction_values(_cells())
    assert k["HOU_PRE1919"] == pytest.approx(5.0) and k["HOU_1949_1978"] == pytest.approx(10.0)
    assert (k["HOU_PRE1919_DWELLINGS"], k["HOU_1949_1978_DWELLINGS"]) == (10, 20)
    assert isinstance(k["HOU_PRE1919_DWELLINGS"], int)
    # new quarter: dwellings in 2022, none in the 2011 grid -> 0 %, not k. A.
    without_2011 = _cells().assign(dw_total_2011=np.nan, dw_pre1919_2011=np.nan, dw_1949_1978_2011=np.nan)
    k = construction_values(without_2011)
    assert k["HOU_PRE1919"] == 0.0 and k["HOU_1949_1978"] == 0.0 and k["HOU_PRE1919_DWELLINGS"] == 0
    # no dwellings in 2022 -> k. A.; the class counts at most the dwellings of 2022, so the count is 0
    k = construction_values(_cells().assign(dwellings=0))
    assert k["HOU_PRE1919"] is None and k["HOU_PRE1919_DWELLINGS"] == 0


def test_construction_values_caps_class_at_dwellings_2022():
    """README: a cell counts at most as many dwellings of a class as it has in 2022 (dormitories of 2011, example Hausen)."""
    g = pd.DataFrame({"dwellings": [16, 100], "dw_1949_1978_2011": [717, 30], "dw_pre1919_2011": [0, 40]})
    k = construction_values(g)
    assert k["HOU_1949_1978_DWELLINGS"] == 46
    assert k["HOU_1949_1978"] == pytest.approx(100 * 46 / 116)
    assert k["HOU_PRE1919_DWELLINGS"] == 40
    assert isinstance(k["HOU_1949_1978_DWELLINGS"], int)


def test_construction_parts_match_the_values():
    """The worked example uses the parts: class 2011 uncapped, capped, dwellings 2022."""
    g = pd.DataFrame({"dwellings": [16, 100, None], "dw_1949_1978_2011": [717, 30, 5], "dw_pre1919_2011": [0, 40, None]})
    for kid, column in (("HOU_1949_1978", "dw_1949_1978_2011"), ("HOU_PRE1919", "dw_pre1919_2011")):
        raw, capped, dwellings = construction_parts(g, column)
        values = construction_values(g)
        assert capped == values[f"{kid}_DWELLINGS"] and 100 * capped / dwellings == pytest.approx(values[kid])
        assert raw >= capped and dwellings == 116
    assert construction_parts(g, "dw_1949_1978_2011") == (752, 46, 116)
