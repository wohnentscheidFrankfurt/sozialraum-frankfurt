import pytest

from pipeline import config
from pipeline.shared.zensus.model import SIZES
from pipeline.shared.zensus.tables import (OWNER_RATE, RENT_SQM, VACANCY_RATE, read_4000w, read_buildings_by_decade,
                                           read_buildings_by_size, read_city_value, read_condo_use,
                                           read_dwellings_by_construction_year,
                                           read_dwellings_by_size, read_dwellings_history, read_vacancy_4000w)


HEAD_2002 = "table;municipality;STAG;STAG_label;content;content_label;WHGNZ2;WHGNZ2_label;GEBEG1;GEBEG1_label;value;quality"
CLASS_CODES = ["EIG-GEMEIN", "EIG-PRIVAT", "EIG-GENOSS", "EIG-KOMMUN", "EIG-UNT-PRIVAT1", "EIG-UNT-PRIVAT2",
               "EIG-BUND-LAND", "EIG-ORGA", "%TOTAL%"]


def _table_2002(totals=(98759, 134116, 12932, 69558, 57076, 19264, 5651, 5471, 402826), uses=(), days=("2022-05-15",)):
    """Long rows of table 4000W-2002: all uses by ownership type, and uses = [(use code, value for all owners)]."""
    rows = [HEAD_2002]
    for day in days:
        for code, v in zip(CLASS_CODES, totals):
            rows.append(f"4000W-2002;064120000000;{day};x;WHG002$ID0004;;%TOTAL%;x;{code};x;{v}.0;e")
            rows.append(f"4000W-2002;064120000000;{day};x;WHG002$PO0004;;%TOTAL%;x;{code};x;1.0;e")
        rows.append(f"4000W-2002;064120000000;{day};x;WHG002$ID0004;;NUTZ-EIGEN;x;EIG-PRIVAT;x;33684.0;e")
        for use, v in uses:
            rows.append(f"4000W-2002;064120000000;{day};x;WHG002$ID0004;;{use};x;%TOTAL%;x;{v}.0;e")
    return "\n".join(rows)


USES = [("NUTZ-EIGEN", 76585), ("NUTZ-MIETE", 312915), ("NUTZ-LEER", 12893), ("NUTZ-FERIEN", 430)]


def test_read_4000w_takes_only_the_rows_of_all_uses():
    w = read_4000w(_table_2002())
    assert w["total"] == 402826 and w["municipal"] == 69558 and w["person"] == 134116 and len(w) == 9


def test_read_4000w_reports_missing_classes():
    text = "\n".join(l for l in _table_2002().splitlines() if "EIG-ORGA" not in l)
    with pytest.raises(ValueError, match="nonprofit"):
        read_4000w(text)


def test_read_4000w_takes_the_year_2022_only():
    assert read_4000w(_table_2002(days=("2011-05-09", "2022-05-15")))["total"] == 402826
    with pytest.raises(ValueError, match="2022"):
        read_4000w(_table_2002(days=("2011-05-09",)))


def test_read_vacancy_4000w():
    assert read_vacancy_4000w(_table_2002(uses=USES)) == {"vacant": 12893, "occupied_and_vacant": 76585 + 312915 + 12893}


def test_read_vacancy_4000w_reports_missing_rows():
    with pytest.raises(ValueError, match="vacant"):
        read_vacancy_4000w(_table_2002())


def test_4000w_2002_long_equals_the_history_table():
    new = read_4000w(config.ZENSUS_4000W.read_text(encoding="utf-8"))
    assert new["total"] == 402826 and new["municipal"] == 69558 and new["coop"] == 12932
    assert new == read_dwellings_history(config.ZENSUS_4000W_1011.read_text(encoding="utf-8"))[2022]
    assert read_vacancy_4000w(config.ZENSUS_4000W.read_text(encoding="utf-8")) == {
        "vacant": 12893, "occupied_and_vacant": 76585 + 312915 + 12893}


def test_read_condo_use_takes_the_weg_dwellings_of_both_years():
    use = read_condo_use(config.ZENSUS_4000W.read_text(encoding="utf-8"))
    assert use == {2011: {"owner": 37175, "rented": 62620, "total": 101464},
                   2022: {"owner": 42903, "rented": 53076, "total": 98759}}


def test_long_values_stops_on_a_double_or_a_blank_value():
    row = [l for l in _table_2002().splitlines() if "ID0004" in l and "EIG-ORGA" in l][0]
    with pytest.raises(ValueError, match="twice"):
        read_4000w(_table_2002() + "\n" + row)
    with pytest.raises(ValueError, match="no value"):
        read_4000w(_table_2002().replace("5471.0", ""))


HEAD_W = "table;municipality;STAG;STAG_label;content;content_label;GEBEG1;GEBEG1_label;value;quality"
CODES = ["EIG-GEMEIN", "EIG-PRIVAT", "EIG-GENOSS", "EIG-KOMMUN", "EIG-UNT-PRIVAT1", "EIG-UNT-PRIVAT2",
         "EIG-BUND-LAND", "EIG-ORGA", "%TOTAL%"]


def _history_text(values_2011, values_2022):
    rows = [HEAD_W]
    for day, values in (("2011-05-09", values_2011), ("2022-05-15", values_2022)):
        for code, v in zip(CODES, values):
            rows.append(f"4000W-1011;064120000000;{day};x;WHG002$ID0004;;{code};x;{v}.0;e")
            rows.append(f"4000W-1011;064120000000;{day};x;WHG002$PO0004;;{code};x;1.0;e")
    return "\n".join(rows)


def test_read_dwellings_history_takes_counts_per_year_and_class():
    text = _history_text([1, 2, 3, 4, 5, 6, 7, 8, 36], [10, 20, 30, 40, 50, 60, 70, 80, 360])
    h = read_dwellings_history(text)
    assert set(h) == {2011, 2022}
    assert h[2011]["condo"] == 1 and h[2011]["other_company"] == 6 and h[2011]["total"] == 36
    assert h[2022]["state"] == 70 and h[2022]["nonprofit"] == 80 and len(h[2022]) == 9


def test_read_dwellings_history_reports_a_missing_class():
    text = "\n".join(l for l in _history_text([1] * 9, [1] * 9).splitlines() if "EIG-ORGA" not in l or "2011" not in l)
    with pytest.raises(ValueError, match="2011"):
        read_dwellings_history(text)


HEAD_G = "table;municipality;content;content_label;STAG;STAG_label;GEBEG1;GEBEG1_label;GEBBJ5;GEBBJ5_label;value;quality"
DECADES = [("%TOTAL%", "Insgesamt"), ("BAU0000B1918", "Vor 1919"), ("BAU1919B1949", "1919 - 1949"),
           ("BAU2010B2015", "2010 - 2015"), ("BAU2016BXXXX", "2016 und später")]


def _decade_text():
    rows = [HEAD_G]
    for day in ("2011-05-09", "2022-05-15"):
        for i, code in enumerate(CODES):
            for j, (decade, label) in enumerate(DECADES):
                value = 0 if day.startswith("2011") and decade == "BAU2016BXXXX" else 100 * i + j
                quality = "-" if value == 0 else "e"
                rows.append(f"3000G-2001;064120000000;GEB001$QMU;;{day};x;{code};x;{decade};{label};{value}.0;{quality}")
    return "\n".join(rows)


def test_read_buildings_by_decade_keeps_order_labels_and_first_years():
    decades, values = read_buildings_by_decade(_decade_text())
    assert [d["decade"] for d in decades] == ["BAU0000B1918", "BAU1919B1949", "BAU2010B2015", "BAU2016BXXXX"]
    assert [d["label"] for d in decades] == ["Vor 1919", "1919–1949", "2010–2015", "2016 und später"]
    assert [d["first_year"] for d in decades] == [0, 1919, 2010, 2016]
    assert values[2022]["housing_company"]["BAU1919B1949"] == 402 and values[2011]["total"]["total"] == 800
    assert values[2011]["condo"]["BAU2016BXXXX"] == 0


def test_real_extracts_hold_the_known_values():
    h = read_dwellings_history(config.ZENSUS_4000W_1011.read_text(encoding="utf-8"))
    assert h[2011]["housing_company"] + h[2011]["other_company"] == 37847 and h[2022]["total"] == 402826
    decades, b = read_buildings_by_decade(config.ZENSUS_3000G_2001.read_text(encoding="utf-8"))
    assert len(decades) == 10 and b[2022]["total"]["total"] == 80679


HEAD_S = "table;municipality;content;content_label;STAG;STAG_label;GEBWG2;GEBWG2_label;GEBEG1;GEBEG1_label;value;quality"
SIZE_ROWS = [("%TOTAL%", "Insgesamt"), ("WOHN01", "1 Wohnung"), ("WOHN02", "2 Wohnungen"),
             ("WOHN03B06", "3 - 6 Wohnungen"), ("WOHN07B12", "7 - 12 Wohnungen"), ("WOHN13UM", "13 und mehr Wohnungen")]


def _size_text(table, content, skip=lambda day, code, size: False):
    rows = [HEAD_S]
    for day in ("2011-05-09", "2022-05-15"):
        for i, code in enumerate(CODES):
            for j, (size, label) in enumerate(SIZE_ROWS):
                if skip(day, code, size):
                    continue
                value = 0 if size == "WOHN01" and code == "EIG-GEMEIN" else 10 * i + j
                quality = "-" if value == 0 else "e"
                rows.append(f"{table};064120000000;{content};;{day};x;{size};{label};{code};x;{value}.0;{quality}")
    return "\n".join(rows)


def test_read_buildings_by_size_maps_codes_to_sizes():
    v = read_buildings_by_size(_size_text("3000G-2007", "GEB001$QMU"))
    assert SIZES == ["1", "2", "3_6", "7_12", "13_plus"]
    assert set(v) == {2011, 2022} and set(v[2022]["housing_company"]) == set(SIZES) | {"total"}
    assert v[2022]["condo"]["1"] == 0 and v[2011]["housing_company"]["13_plus"] == 45


def test_read_dwellings_by_size_reads_its_own_content():
    v = read_dwellings_by_size(_size_text("4000W-2013", "WHG002$QMU"))
    assert v[2011]["total"]["total"] == 80
    with pytest.raises(ValueError, match="WHG002"):
        read_dwellings_by_size(_size_text("3000G-2007", "GEB001$QMU"))


def test_read_by_size_reports_a_missing_size():
    text = _size_text("3000G-2007", "GEB001$QMU", lambda day, code, size: day.startswith("2022") and size == "WOHN13UM"
                      and code == "EIG-ORGA")
    with pytest.raises(ValueError, match="2022 nonprofit has no values for \\['13_plus'\\]"):
        read_buildings_by_size(text)


def test_read_by_size_reports_a_missing_year():
    text = _size_text("3000G-2007", "GEB001$QMU", lambda day, code, size: day.startswith("2011"))
    with pytest.raises(ValueError, match="2011"):
        read_buildings_by_size(text)


def test_real_size_extracts_hold_the_known_values():
    b = read_buildings_by_size(config.ZENSUS_3000G_2007.read_text(encoding="utf-8"))
    d = read_dwellings_by_size(config.ZENSUS_4000W_2013.read_text(encoding="utf-8"))
    assert b[2022]["total"]["total"] == 80679 and b[2022]["municipal"]["total"] == 8508
    assert d[2022]["total"]["13_plus"] == 127106
    assert d[2022]["housing_company"]["13_plus"] + d[2022]["other_company"]["13_plus"] == 40934


def test_read_by_size_rejects_a_blank_cell():
    text = _size_text("3000G-2007", "GEB001$QMU").replace(";WOHN02;2 Wohnungen;EIG-ORGA;x;72.0;e", ";WOHN02;2 Wohnungen;EIG-ORGA;x;;e", 1)
    with pytest.raises(ValueError, match="table 3000G-2007: 2011 nonprofit size 2 has no value"):
        read_buildings_by_size(text)


def test_read_by_size_names_an_unknown_code():
    text = _size_text("3000G-2007", "GEB001$QMU").replace("WOHN13UM", "WOHN13B20", 1)
    with pytest.raises(ValueError, match="table 3000G-2007: unknown GEBWG2 code WOHN13B20"):
        read_buildings_by_size(text)


def test_read_dwellings_by_construction_year_from_the_source():
    text = config.ZENSUS_4000W_1008.read_text(encoding="utf-8")
    t = read_dwellings_by_construction_year(text)
    assert t == {2011: {"pre1919": 67328, "1949_1978": 187254, "total": 365401},
                 2022: {"pre1919": 66790, "1949_1978": 189598, "total": 402826}}
    without_2022 = "\n".join(line for line in text.splitlines() if "2022-05-15" not in line)
    with pytest.raises(ValueError, match="2022"):
        read_dwellings_by_construction_year(without_2022)


LONG = ("table;municipality;STAG;STAG_label;content;content_label;value;quality\n"
        "4000W-0001;064120000000;2011-05-09;09.05.2011;WHG007$QMU;;20.7;e\n"
        "4000W-0001;064120000000;2022-05-15;15.05.2022;WHG007$QMU;;20.1;e\n"
        "4000W-0001;064120000000;2022-05-15;15.05.2022;WHG009$QMU;;3.1;e\n")


def test_read_city_value_takes_the_row_of_the_day():
    assert read_city_value(LONG, OWNER_RATE) == 20.1
    assert read_city_value(LONG, OWNER_RATE, "2011-05-09") == 20.7
    assert read_city_value(LONG, VACANCY_RATE) == 3.1


def test_read_city_value_stops_on_a_missing_or_double_row():
    with pytest.raises(ValueError, match="no rows with content WHG012"):
        read_city_value(LONG, RENT_SQM)
    with pytest.raises(ValueError, match="2 rows"):
        read_city_value(LONG + LONG.splitlines()[2] + "\n", OWNER_RATE)


@pytest.mark.parametrize("path, content, value", [("ZENSUS_4000W_0001", OWNER_RATE, 20.1),
                                                 ("ZENSUS_4000W_0004", RENT_SQM, 10.58),
                                                 ("ZENSUS_4000W_0001", VACANCY_RATE, 3.1)])
def test_real_tables_for_frankfurt(path, content, value):
    assert read_city_value(getattr(config, path).read_text(encoding="utf-8"), content) == value
