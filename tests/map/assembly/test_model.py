import pandas as pd
import pytest

from pipeline.map.assembly.model import add_small, join_area_table


def test_join_area_table_stops_on_a_column_from_two_tables():
    base = pd.DataFrame({"id": ["1"], "POP": [3]})
    assert join_area_table(base, pd.DataFrame({"id": ["1"], "X": [2]}))["X"].tolist() == [2]
    with pytest.raises(ValueError, match="POP"):
        join_area_table(base, pd.DataFrame({"id": ["1"], "POP": [2]}))


def test_join_area_table_stops_on_duplicate_ids():
    """A duplicate id in a table would multiply the rows of the area."""
    base = pd.DataFrame({"id": ["1", "2"], "POP": [3, 4]})
    with pytest.raises(ValueError, match="not unique|one-to-one"):
        join_area_table(base, pd.DataFrame({"id": ["1", "1"], "X": [2, 3]}))
    assert join_area_table(base, pd.DataFrame({"id": ["1"], "X": [2]}))["X"].isna().tolist() == [False, True]


def test_add_small_marks_districts_below_the_threshold():
    districts = pd.DataFrame({"id": ["1", "2", "3"], "POP_MONITORING": [5000.0, 100.0, None], "POP": [5000, 6000, 20]})
    assert add_small(districts)["small"].tolist() == [0, 1, 1]
    assert "small" not in districts.columns  # the argument stays as it is


def test_add_small_stops_when_a_table_already_holds_the_column():
    """`small` is set after the joins; a column of that name from a use case would be overwritten."""
    districts = pd.DataFrame({"id": ["1"], "POP_MONITORING": [5000.0], "POP": [5000], "small": [1]})
    with pytest.raises(ValueError, match="small"):
        add_small(districts)
