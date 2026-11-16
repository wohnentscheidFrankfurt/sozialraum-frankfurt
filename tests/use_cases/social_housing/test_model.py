import pandas as pd
import pytest

from pipeline.use_cases.social_housing.catalog import SH_AS_OF
from pipeline.use_cases.social_housing.model import city_totals, city_values_rows, indicators, merge_quarters
from pipeline.use_cases.social_housing.sources import check_report_year, read_table

HEADING = r"1\.2\.\s+Bestand"
CONTENTS = "1.2. Bestand an Wohnungen nach Stadtteil 9"
TAB = "\n".join(["Seite 9", "1.2. Bestand an Wohnungen nach Stadtteil", "Stadtteil", "Sozialwohnungen", "Altstadt", "22",
                 "-", "Sachsenhausen-Süd", "1.347", "307", "Flughafen", "-", "-", "außerhalb Frankfurts", "362", "-",
                 "Gesamt", "1.731", "307", "Fußnote"])
TWO = {"Altstadt", "Sachsenhausen-Süd und Flughafen"}


def test_read_table_takes_the_last_hit_and_reads_dashes_as_zero():
    assert read_table([CONTENTS, TAB], HEADING, 2) == {"Altstadt": [22, 0], "Sachsenhausen-Süd": [1347, 307],
                                                     "Flughafen": [0, 0], "außerhalb Frankfurts": [362, 0],
                                                     "Gesamt": [1731, 307]}


def test_read_table_stops_on_a_wrong_sum():
    with pytest.raises(ValueError, match="does not match"):
        read_table([TAB.replace("1.731", "1.732")], HEADING, 2)


def test_read_table_stops_on_a_missing_value():
    with pytest.raises(ValueError, match="wrong number"):
        read_table([TAB.replace("Altstadt\n22\n-", "Altstadt\n22")], HEADING, 2)


def test_read_table_stops_without_heading():
    with pytest.raises(ValueError, match="not found"):
        read_table(["nichts"], HEADING, 2)


def test_merge_quarters_adds_the_airport_and_splits_off_outside():
    rest, outside = merge_quarters(read_table([TAB], HEADING, 2), TWO)
    assert rest == {"Altstadt": [22, 0], "Sachsenhausen-Süd und Flughafen": [1347, 307]} and outside == [362, 0]


def test_merge_quarters_knows_outside_in_upper_case():
    t = read_table([TAB.replace("außerhalb Frankfurts", "Außerhalb Frankfurts")], HEADING, 2)
    assert merge_quarters(t, TWO)[1] == [362, 0]


def test_merge_quarters_stops_on_unknown_or_missing_quarters():
    t = read_table([TAB], HEADING, 2)
    with pytest.raises(ValueError, match=r"missing \['Bonames'\]"):
        merge_quarters(t, TWO | {"Bonames"})
    with pytest.raises(ValueError, match=r"unknown \['Altstadt'\]"):
        merge_quarters(t, {"Sachsenhausen-Süd und Flughafen"})


def test_indicators_shares():
    df = indicators({"A": [200, 10, 0], "B": [50, 0, 0]}, {"A": 1000.0, "B": 500.0}).set_index("quarter")
    assert list(df.columns) == ["SH_COUNT", "SH_SHARE"]
    assert (df.loc["A", "SH_COUNT"], df.loc["A", "SH_SHARE"]) == (200, 20.0)
    assert (df.loc["B", "SH_COUNT"], df.loc["B", "SH_SHARE"]) == (50, 10.0)


def test_city_totals_and_shares():
    assert city_totals({"A": [200, 0, 0], "B": [50, 0, 0]}, {"A": 1000.0, "B": 1500.0}) == {"SH_COUNT": 250, "SH_SHARE": 10.0}


PAGE_9 = "\n".join(["Jahresbericht 2025", "Seite 9", "1.2. Bestand an Wohnungen nach Stadtteil", "Stadtteil", "Altstadt", "22"])


def test_check_report_year_fits_the_catalog():
    check_report_year([CONTENTS, PAGE_9], SH_AS_OF[-4:])


def test_check_report_year_detects_a_new_report():
    with pytest.raises(ValueError, match="New annual report"):
        check_report_year([CONTENTS, PAGE_9.replace("Jahresbericht 2025", "Jahresbericht 2026")], SH_AS_OF[-4:])
    with pytest.raises(ValueError, match="New annual report"):
        check_report_year([CONTENTS, PAGE_9.replace("Jahresbericht 2025\n", "")], SH_AS_OF[-4:])


def _stock_xlsx(path, years=(2024, 2025), rows=(("01 - Altstadt", "2.901"), ("15 - Sachsenhausen-Süd (inkl. Flughafen)", "17.000")),
                total="19.901"):
    import openpyxl
    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    for y in years:
        ws = wb.create_sheet(f"Tabelle{y}")
        for r in (["STATISTIK.PORTAL"], [""], ["Wohnungsbestand und Räume"], ["Stadtteile …"], ["wobei …"], [""],
                  [f"Jahr = {y}"], [None], ["", "Gesamt"], [None, "Wohnungen insgesamt", "Wohnungen mit 1 Raum"],
                  *[[n, v, "1"] for n, v in rows], ["Gesamt", total, "2"], [""], ["Einschließlich Wohnheime."]):
            ws.append(r)
    wb.save(path)
    return path


def test_read_dwelling_stock_takes_the_year_and_maps_the_airport_row(tmp_path):
    from pipeline.use_cases.social_housing.sources import read_dwelling_stock
    from pipeline.use_cases.social_housing.model import stock_on_quarters
    from pipeline.use_cases.social_housing.sources import STOCK_AIRPORT_ROW
    stock = read_dwelling_stock(_stock_xlsx(tmp_path / "s.xlsx"), 2025)
    assert stock == {"Altstadt": 2901, "Sachsenhausen-Süd (inkl. Flughafen)": 17000}
    assert stock_on_quarters(stock, TWO, STOCK_AIRPORT_ROW) == {"Altstadt": 2901.0, "Sachsenhausen-Süd und Flughafen": 17000.0}
    with pytest.raises(ValueError, match="missing"):
        stock_on_quarters({"Altstadt": 1}, TWO, STOCK_AIRPORT_ROW)


def test_read_dwelling_stock_stops_on_a_missing_year_or_a_wrong_sum(tmp_path):
    from pipeline.use_cases.social_housing.sources import read_dwelling_stock
    with pytest.raises(ValueError, match="2025"):
        read_dwelling_stock(_stock_xlsx(tmp_path / "a.xlsx", years=(2024,)), 2025)
    with pytest.raises(ValueError, match="Gesamt"):
        read_dwelling_stock(_stock_xlsx(tmp_path / "b.xlsx", total="19.900"), 2025)


def test_city_values_rows_are_the_share():
    info = {"SH_COUNT": 10, "SH_SHARE": 5.9, "total_stock": [1]}
    assert city_values_rows(info) == [{"indicator": "SH_SHARE", "value": 5.9, "kind": "computed"}]
