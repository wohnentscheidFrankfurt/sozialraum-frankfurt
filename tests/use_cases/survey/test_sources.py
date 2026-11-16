
import math

import pytest

from pipeline.use_cases.survey.sources import FIGURES, PRINTED_CITY_BURDEN, SURVEY_AREAS, read_microdata


def test_figures_place_every_area_in_one_printed_class():
    names = sorted(SURVEY_AREAS.values())
    for indicator, figure in FIGURES.items():
        assert sorted(a for members in figure["classes"].values() for a in members) == names, indicator
        assert all(lower <= upper for lower, upper in figure["classes"])
    assert FIGURES["LIF_RENT_BURDEN_RATIO"]["city"] == 29 and FIGURES["LIF_ATTACHMENT"]["city"] == 62
    assert FIGURES["LIF_RENT_BURDEN_RATIO"]["classes"][(29, 29)] == ("Innenstadt I", "Bornheim/Ostend", "Süd")
    assert FIGURES["LIF_ATTACHMENT"]["classes"][(64, 70)] == ("Kalbach/Riedberg", "Mitte-West", "Ost", "Süd")


_HEADER = ["Umfragebezirk", "weight", "WOmieig_a", "WOkami_a", "WObtrko_a", "XDhhnek_a", "XDhhgrabs_a",
           "XDhhgr017_a", "XDhhform_a"]


def _write_csv(path, rows):
    lines = [";".join(f'"{h}"' for h in _HEADER)] + [";".join(str(v) for v in row) for row in rows]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8-sig")
    return path


def _rows(rent_class=12):
    return [[2, "1,25", 1, rent_class, 1, 2, 5, 4, 3],
            [3, "0,8", 2, -42, -42, -42, -42, -42, -42],
            [13, "1,0", 1, 3, 8, 6, 1, 1, 1]]


def test_read_microdata_maps_codes_to_bounds(tmp_path):
    data = read_microdata(_write_csv(tmp_path / "m.csv", _rows()), 2025)
    row = data.iloc[0]
    assert len(data) == 3 and row["year"] == 2025
    assert row["survey_area"] == "Innenstadt II" and row["weight"] == 1.25 and row["tenant"]
    assert row["rent_low"] == 1400 and math.isnan(row["rent_high"])
    assert row["costs_low"] == 0 and row["costs_high"] == 100
    assert row["income_low"] == 1000 and row["income_high"] == 2000
    assert row["persons"] == 5 and row["children"] == 3 and row["household_form"] == "couple_children"
    last = data.iloc[2]
    assert last["rent_low"] == 500 and last["rent_high"] == 600
    assert last["costs_low"] == 400 and math.isnan(last["costs_high"])
    assert math.isnan(last["income_high"]) and last["income_low"] == 5000
    assert last["persons"] == 1 and last["children"] == 0 and last["household_form"] == "single"


def test_read_microdata_reads_minus_42_as_missing(tmp_path):
    row = read_microdata(_write_csv(tmp_path / "m.csv", _rows()), 2025).iloc[1]
    assert not row["tenant"]
    assert row["survey_area"] == "Innenstadt III"
    for column in ("rent_low", "rent_high", "costs_low", "costs_high", "income_low", "income_high", "persons",
                   "children"):
        assert math.isnan(row[column]), column
    assert row["household_form"] is None


def test_read_microdata_stops_on_an_unknown_code(tmp_path):
    with pytest.raises(ValueError, match="WOkami_a"):
        read_microdata(_write_csv(tmp_path / "m.csv", _rows(rent_class=13)), 2025)


def test_read_microdata_stops_on_an_unknown_survey_area(tmp_path):
    rows = _rows()
    rows[0][0] = 14
    with pytest.raises(ValueError, match="Umfragebezirk"):
        read_microdata(_write_csv(tmp_path / "m.csv", rows), 2025)


def test_printed_city_burden_names_the_pages_and_medians():
    assert PRINTED_CITY_BURDEN == {2025: (30, 29), 2024: (25, 29)}
