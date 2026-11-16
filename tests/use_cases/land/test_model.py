import numpy as np
import pandas as pd
from shapely.geometry import box

from pipeline.use_cases.land.model import Zone, land_value_at, land_values


def test_land_value_at_averages_overlapping_zones():
    zones = [Zone(box(0, 0, 10, 10), 1000.0, ""), Zone(box(5, 0, 15, 10), 3000.0, "")]
    w = land_value_at([2, 7, 20], [5, 5, 5], zones)
    assert w[0] == 1000 and w[1] == 2000 and np.isnan(w[2])


def test_land_values_weighted_median_by_residents():
    g = pd.DataFrame({"land_value": [500.0, 2000.0, None], "pop": [10, 30, 100]})
    assert land_values(g) == {"LAND_VALUE": 2000.0}


def test_with_values_takes_the_value_of_the_same_number_and_drops_the_rest():
    from pipeline.use_cases.land.model import with_values
    zones = [Zone(box(0, 0, 1, 1), 3900.0, "W", "43391012"), Zone(box(1, 0, 2, 1), 700.0, "M", "49999999")]
    out = with_values(zones, {"43391012": 3300.0})
    assert [(z.number, z.value, z.use) for z in out] == [("43391012", 3300.0, "W")]
