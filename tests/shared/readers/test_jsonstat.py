import pytest

from pipeline.shared.readers.jsonstat import long_csv, long_rows

STRUCTURE = {"variableValues": {"A1": {"label": {"de": "Eins"}}, "A2": {"label": {"de": "Zwei"}},
                                "06412": {"label": {"de": "Frankfurt am Main"}}}}
# JSON-stat as the GENESIS web clients send it: an index is an object (code -> position) or a list of codes; values and
# status are lists or objects keyed by the flat position
BY_VAR = {"id": ["statistic", "content", "VAR", "KREISE"], "size": [1, 1, 2, 2],
          "dimension": {"statistic": {"category": {"index": {"S": 0}}}, "content": {"category": {"index": ["C$QMU"]}},
                        "VAR": {"category": {"index": {"A1": 0, "A2": 1}}},
                        "KREISE": {"category": {"index": ["06412", "06411"]}}},
          "value": [1, 2, 3, 4], "status": {"0": "e"}}
TOTAL = {"id": ["statistic", "content", "KREISE"], "size": [1, 1, 2],
         "dimension": {"statistic": {"category": {"index": ["S"]}}, "content": {"category": {"index": ["C$QMU"]}},
                       "KREISE": {"category": {"index": {"06412": 0, "06411": 1}}}},
         "value": {"0": 10.0}, "status": ["e", "e"]}
GERMANY = {"id": ["statistic", "content", "DINSG"], "size": [1, 1, 1],
           "dimension": {"statistic": {"category": {"index": ["S"]}}, "content": {"category": {"index": ["C$QMU"]}},
                         "DINSG": {"category": {"index": ["DG"]}}},
           "value": [99]}


def test_long_rows_keep_the_region_and_skip_datasets_without_it():
    rows = long_rows(STRUCTURE, {"data": [BY_VAR, GERMANY, TOTAL]}, "T", "KREISE", "06412", "region")
    # the datasets in the order of their ids, whatever the order of the answer
    assert rows == [
        {"table": "T", "region": "06412", "content": "C$QMU", "content_label": "", "value": 10.0, "quality": "e"},
        {"table": "T", "region": "06412", "content": "C$QMU", "content_label": "", "VAR": "A1", "VAR_label": "Eins",
         "value": 1, "quality": "e"},
        {"table": "T", "region": "06412", "content": "C$QMU", "content_label": "", "VAR": "A2", "VAR_label": "Zwei",
         "value": 3, "quality": ""}]


def test_long_rows_take_the_region_variable_by_its_exact_name():
    geo = {**TOTAL, "id": ["statistic", "content", "GEOGM4"],
           "dimension": {**TOTAL["dimension"], "GEOGM4": TOTAL["dimension"]["KREISE"]}}
    rows = long_rows(STRUCTURE, {"data": [geo, TOTAL]}, "T", "GEOGM4", "06412", "municipality")
    assert [(r["municipality"], r["value"]) for r in rows] == [("06412", 10.0)]
    with pytest.raises(ValueError):
        long_rows(STRUCTURE, {"data": [geo]}, "T", "GEO", "06412", "municipality")


def test_long_rows_order_datasets_with_the_same_variables_by_their_codes():
    def per_content(code, value):
        return {**TOTAL, "dimension": {**TOTAL["dimension"], "content": {"category": {"index": [code]}}},
                "value": [value, 0]}
    first, second = per_content("A$QMU", 1), per_content("B$QMU", 2)
    for data in ([first, second], [second, first]):
        rows = long_rows(STRUCTURE, {"data": data}, "T", "KREISE", "06412", "region")
        assert [r["content"] for r in rows] == ["A$QMU", "B$QMU"]


def test_a_missing_value_stays_empty():
    gap = {**TOTAL, "value": {"1": 5.0}}
    rows = long_rows(STRUCTURE, {"data": [gap]}, "T", "KREISE", "06412", "region")
    assert rows[0]["value"] is None
    assert long_csv(rows).splitlines()[1] == "T;06412;C$QMU;;;e"


def test_long_rows_stop_when_the_api_changed_or_the_region_is_missing():
    with pytest.raises(ValueError, match="variableValues"):
        long_rows({}, {"data": [TOTAL]}, "T", "KREISE", "06412", "region")
    with pytest.raises(ValueError, match="no values for 99999 in T"):
        long_rows(STRUCTURE, {"data": [TOTAL]}, "T", "KREISE", "99999", "region")


def test_long_csv_writes_every_column_once_in_the_order_of_appearance():
    rows = long_rows(STRUCTURE, {"data": [BY_VAR, TOTAL]}, "T", "KREISE", "06412", "region")
    assert long_csv(rows).splitlines() == [
        "table;region;content;content_label;value;quality;VAR;VAR_label",
        "T;06412;C$QMU;;10.0;e;;",
        "T;06412;C$QMU;;1;e;A1;Eins",
        "T;06412;C$QMU;;3;;A2;Zwei"]
    assert long_csv(rows).endswith("\r\n")  # line ends of the csv module, as in the extracts in sources/


def test_long_csv_sorts_by_the_given_columns_only():
    rows = long_rows(STRUCTURE, {"data": [BY_VAR, TOTAL]}, "T", "KREISE", "06412", "region")
    lines = long_csv(rows, order=("VAR",)).splitlines()
    assert [line.split(";")[6] for line in lines[1:]] == ["", "A1", "A2"]
    # the columns follow the rows before the sort
    header = long_csv(list(reversed(rows)), order=("VAR",)).splitlines()[0]
    assert header.startswith("table;region;content;content_label;VAR")
