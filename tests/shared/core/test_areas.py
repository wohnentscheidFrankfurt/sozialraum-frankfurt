import pandas as pd

from pipeline.shared.core.areas import city_rows, per_area


def test_per_area_passes_the_key_and_keeps_integers():
    cells = pd.DataFrame({"district": ["a", "a", "b"], "pop": [1, 2, 5]})
    out = per_area(cells, "district", lambda key, g: {"POP": int(g["pop"].sum()), "KEY": key})
    assert out.to_dict("records") == [{"id": "a", "POP": 3, "KEY": "a"}, {"id": "b", "POP": 5, "KEY": "b"}]
    assert out["POP"].dtype.kind == "i"


def test_city_rows_skip_range_ends_and_counts():
    rows = city_rows({"OWN_PUBLIC": 18.2, "OWN_PUBLIC_LOW": 17.0, "OWN_PUBLIC_HIGH": 19.0, "OWN_PUBLIC_DWELLINGS": 5.0},
                     without=frozenset({"OWN_PUBLIC_DWELLINGS"}))
    assert rows == [{"indicator": "OWN_PUBLIC", "value": 18.2, "kind": "computed"}]
    assert city_rows({"SOC_MIN_INCOME": 11.3}, kind="published")[0]["kind"] == "published"
