import pandas as pd
from shapely.geometry import box

from pipeline.shared.core.geometry import Site
from pipeline.shared.geography.model import (AIRPORT_MERGED, Area, assign_points, is_small, map_quarter_name,
                                             names_in_area)


def test_assign_points():
    a = Area("A", "A", "S", "", box(0, 0, 10, 10))
    b = Area("B", "B", "S", "", box(10, 0, 20, 10))
    assert list(assign_points([5, 15, 25], [5, 5, 5], [a, b])) == ["A", "B", None]


def test_map_quarter_name_merges_the_airport():
    assert map_quarter_name("Flughafen") == AIRPORT_MERGED
    assert map_quarter_name("Sachsenhausen-Süd ") == AIRPORT_MERGED
    assert map_quarter_name("Nied") == "Nied"


def test_names_in_area_needs_one_hectare():
    area = Area("A", "A", "S", "", box(0, 0, 1000, 1000))
    large = Site("Groß", "", box(900, 0, 1100, 1000))
    edge = Site("Rand", "", box(995, 0, 1100, 1000))
    assert names_in_area(area, [large, edge]) == ["Groß"]


def test_is_small_under_1000_in_grid_or_monitoring():
    out = is_small(pd.Series([2000, 900, None, 2000]), pd.Series([2000, 2000, 2000, None]))
    assert out.tolist() == [0, 1, 1, 1]
