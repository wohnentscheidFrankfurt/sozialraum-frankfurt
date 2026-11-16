import pandas as pd
from shapely.geometry import box

from pipeline.shared.core.geometry import Site
from pipeline.shared.geography.model import Area
from pipeline.use_cases.protection.model import inside, names_by_area, protection_values


def test_names_by_area_has_one_column_per_group():
    a = Area("A", "A", "S", "", box(0, 0, 1000, 1000))
    big = Site("Groß", "", box(0, 0, 500, 500))
    df = names_by_area([a], "district", {"x": [big], "y": []})
    assert df.to_dict("records") == [{"district": "A", "x": "Groß", "y": ""}]


def test_inside():
    sites = [Site("a", "", box(0, 0, 10, 10)), Site("b", "", box(20, 0, 30, 10))]
    assert inside(sites, [5, 15, 25], [5, 5, 5]).tolist() == [True, False, True]


def test_protection_values_share_of_residents_inside():
    g = pd.DataFrame({"pop": [30, 70, 0], "in_social_preservation": [1, 0, None]})
    assert protection_values(g) == {"PROT_SOCIAL": 30.0}
