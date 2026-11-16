import pandas as pd
import pytest

from pipeline.shared.core.city_values import city_value_dict, city_values_frame


def test_city_values_frame_keeps_eight_decimals():
    df = city_values_frame([{"indicator": "POP", "value": 743529, "kind": "computed"},
                            {"indicator": "X", "value": 1.123456789123, "kind": "computed"},
                            {"indicator": "Y", "value": None, "kind": "published"}])
    assert df["value"].tolist()[:2] == [743529.0, 1.12345679] and pd.isna(df["value"].iloc[2])


def test_city_values_frame_keeps_the_rows_in_order_with_their_kind():
    df = city_values_frame([{"indicator": "B", "value": 2.0, "kind": "published"},
                            {"indicator": "A", "value": 1.0, "kind": "computed"}])
    assert list(df.columns) == ["indicator", "value", "kind"]
    assert df["indicator"].tolist() == ["B", "A"] and df["kind"].tolist() == ["published", "computed"]


def test_city_values_frame_stops_on_duplicate_indicators():
    """Two use cases must not deliver the same indicator: the later row would silently win."""
    rows = [{"indicator": "B", "value": 1.0, "kind": "computed"}, {"indicator": "A", "value": 2.0, "kind": "computed"},
            {"indicator": "B", "value": 3.0, "kind": "published"}, {"indicator": "A", "value": 4.0, "kind": "published"}]
    with pytest.raises(ValueError, match=r"duplicate indicators.*\['A', 'B'\]"):
        city_values_frame(rows)


def test_city_value_dict_turns_nan_into_none():
    df = pd.DataFrame({"indicator": ["OWN_PUBLIC", "X"], "value": [1.5, float("nan")], "kind": ["computed", "published"]})
    assert city_value_dict(df) == {"OWN_PUBLIC": 1.5, "X": None}
