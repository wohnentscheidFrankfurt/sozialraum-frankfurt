import io
import zipfile

import pytest

from pipeline.shared.zensus.model import CLASSES, SIZES
from pipeline.shared.zensus.sources import (CODES_2011, COLUMNS_2011, COLUMNS_2011_BUILDINGS, GRID_FILES, count,
                                            extract_grid_2011, extract_grid_2022, extract_grid_km_2022, mean,
                                            rate, read_2011, read_2011_buildings, read_grid_csv, read_km_rates,
                                            targets)


@pytest.mark.parametrize("text, expected", [("3", 3), ("–", 0), ("", 0), ("1,803", 1803), (" 12 ", 12)])
def test_count(text, expected):
    assert count(text) == expected


@pytest.mark.parametrize("text, expected", [("6,26", 6.26), ("–", None), ("", None), ("57", 57.0)])
def test_mean(text, expected):
    """Means (rent): a rent of zero does not exist, so '–' has no value."""
    assert mean(text) == expected


@pytest.mark.parametrize("text, expected", [("6,26", 6.26), ("–", 0.0), ("-", 0.0), ("", None), ("57", 57.0)])
def test_rate(text, expected):
    """Rates: '–' means „Genau Null oder auf Null geändert“ (dataset description)."""
    assert rate(text) == expected


def _extract(path, head, rows):
    path.write_text("\n".join([head, *rows]), encoding="utf-8")


def test_read_grid_csv_converts_values(tmp_path):
    p = tmp_path / "t.csv"
    _extract(p, "GITTER_ID_100m;x_mp_100m;y_mp_100m;Eigentuemerquote;AnzahlWohnungen", [
        "CRS3035RES100mN3000600E4226700;4226750;3000650;12,5;1,203",
        "CRS3035RES100mN3000700E4226700;4226750;3000750;–;–"])
    values = read_grid_csv(p, {"Eigentuemerquote": ("eq", "mean"), "AnzahlWohnungen": ("n", "count")})
    assert values == {"CRS3035RES100mN3000600E4226700": {"eq": 12.5, "n": 1203},
                     "CRS3035RES100mN3000700E4226700": {"eq": None, "n": 0}}


def test_read_grid_csv_rate_with_dash_is_zero(tmp_path):
    p = tmp_path / "t.csv"
    _extract(p, "GITTER_ID_100m;x_mp_100m;y_mp_100m;Leerstandsquote;durchschnMieteQM", [
        "CRS3035RES100mN3000600E4226700;4226750;3000650;–;–",
        "CRS3035RES100mN3000700E4226700;4226750;3000750;3,5;9,1"])
    values = read_grid_csv(p, {"Leerstandsquote": ("vacancy", "rate"), "durchschnMieteQM": ("rent", "mean")})
    assert values == {"CRS3035RES100mN3000600E4226700": {"vacancy": 0.0, "rent": None},
                     "CRS3035RES100mN3000700E4226700": {"vacancy": 3.5, "rent": 9.1}}


def test_rates_read_a_dash_as_zero_means_do_not():
    kinds = {target: kind for columns in GRID_FILES.values() for entry in columns.values()
             for target, kind in targets(entry)}
    assert {t for t, k in kinds.items() if k == "rate"} == {"owner_rate", "vacancy_rate", "vacancy_rate_market"}
    assert kinds["rent_sqm"] == "mean"
    assert {t for t, k in kinds.items() if k == "dash"} == {"vacancy_rate_dash", "vacancy_rate_market_dash"}


def test_dash_flags_are_count_columns_so_the_cells_hold_integers():
    from pipeline.shared.zensus.sources import COUNT_COLUMNS, VALUE_COLUMNS
    assert {"vacancy_rate_dash", "vacancy_rate_market_dash"} <= set(COUNT_COLUMNS)
    assert "vacancy_rate" in VALUE_COLUMNS and "vacancy_rate_dash" not in VALUE_COLUMNS


def test_read_grid_csv_sets_the_dash_flag_next_to_the_rate(tmp_path):
    p = tmp_path / "t.csv"
    _extract(p, "GITTER_ID_100m;x_mp_100m;y_mp_100m;Leerstandsquote", [
        "CRS3035RES100mN3000600E4226700;4226750;3000650;–",
        "CRS3035RES100mN3000700E4226700;4226750;3000750;3,5"])
    columns = {"Leerstandsquote": [("vacancy_rate", "rate"), ("vacancy_rate_dash", "dash")]}
    assert read_grid_csv(p, columns) == {
        "CRS3035RES100mN3000600E4226700": {"vacancy_rate": 0.0, "vacancy_rate_dash": 1},
        "CRS3035RES100mN3000700E4226700": {"vacancy_rate": 3.5, "vacancy_rate_dash": 0}}
    assert GRID_FILES["zensus_vacancy.zip"]["Leerstandsquote"] == columns["Leerstandsquote"]
    assert GRID_FILES["zensus_vacancy_market.zip"]["marktaktive_Leerstandsquote"] == [
        ("vacancy_rate_market", "rate"), ("vacancy_rate_market_dash", "dash")]


def test_read_km_rates_reads_a_dash_as_zero(tmp_path):
    p = tmp_path / "km.csv"
    p.write_text("GITTER_ID_1km;x_mp_1km;y_mp_1km;Leerstandsquote;werterlaeuternde_Zeichen\n"
                 "CRS3035RES1000mN3000000E4220000;4220500;3000500;–;\n"
                 "CRS3035RES1000mN3001000E4220000;4220500;3001500;3,4;\n", encoding="utf-8")
    assert read_km_rates(p, "Leerstandsquote") == {"CRS3035RES1000mN3000000E4220000": 0.0,
                                                   "CRS3035RES1000mN3001000E4220000": 3.4}
    with pytest.raises(ValueError, match=r"km\.csv.*marktaktive_Leerstandsquote"):
        read_km_rates(p, "marktaktive_Leerstandsquote")


HEAD = "Gitter_ID_100m,Gitter_ID_100m_neu,Merkmal,Auspraegung_Code,Auspraegung_Text,Anzahl,Anzahl_q"
A, B, C = ("CRS3035RES100mN3000600E4226700", "CRS3035RES100mN3000700E4226700", "CRS3035RES100mN2691700E4341100")
EMPTY = {c: 0 for c in COLUMNS_2011[1:]}


def _extract_2011(rows: list[str]) -> io.BytesIO:
    return io.BytesIO("\n".join([HEAD, *rows]).encode("latin-1"))


def test_codes_follow_the_classes():
    assert CODES_2011[4] == "dw_municipal_2011" and CODES_2011[7] == "dw_state_2011" and CODES_2011[1] == "dw_condo_2011"
    assert COLUMNS_2011 == ["cell_id", *(f"dw_{c}_2011" for c in CLASSES), "dw_total_2011", "dw_pre1919_2011",
                            "dw_1949_1978_2011"]
    assert COLUMNS_2011_BUILDINGS == ["cell_id", *(f"bld_{c}_2011" for c in CLASSES),
                                      *(f"bld_size_{s}_2011" for s in SIZES)]


def test_read_2011_keeps_every_ownership_class_in_frankfurt():
    rows = [
        f"100mN30006E42267,{A},INSGESAMT,0,Einheiten insgesamt,120,0",
        f"100mN30006E42267,{A},EIGENTUM,4,Kommune oder kommunales Wohnungsunternehmen,40,0",
        f"100mN30006E42267,{A},EIGENTUM,7,Bund oder Land,75,1",
        f"100mN30006E42267,{A},EIGENTUM,3,Wohnungsgenossenschaft,5,0",
        f"100mN30007E42267,{B},EIGENTUM,7,Bund oder Land,12,0",
        f"100mN30007E42267,{B},EIGENTUM,2,Privatperson/-en,9,0",
        f"100mN30007E42267,{B},HEIZTYP,4,Zentralheizung,12,0",
        f"100mN26917E43411,{C},EIGENTUM,4,Kommune oder kommunales Wohnungsunternehmen,99,0",
    ]
    df = read_2011(_extract_2011(rows), {A, B})
    assert list(df.columns) == COLUMNS_2011
    assert df.set_index("cell_id").to_dict("index") == {
        A: EMPTY | {"dw_municipal_2011": 40, "dw_state_2011": 75, "dw_coop_2011": 5, "dw_total_2011": 120},
        B: EMPTY | {"dw_state_2011": 12, "dw_person_2011": 9}}


def test_read_2011_keeps_two_construction_year_classes():
    """pipeline/use_cases/construction_year/README.md: only codes 01 (Vor 1919) and 03 (1949–1978) of BAUJAHR_MZ."""
    rows = [
        f"x,{A},INSGESAMT,0,Einheiten insgesamt,91,0",
        f"x,{A},BAUJAHR_MZ,01,Vor 1919,30,0",
        f"x,{A},BAUJAHR_MZ,02,1919 - 1948,7,0",
        f"x,{A},BAUJAHR_MZ,03,1949 - 1978,50,0",
        f"x,{A},BAUJAHR_MZ,10,2009 und später,4,0",
        f"x,{C},BAUJAHR_MZ,01,Vor 1919,99,0",
    ]
    df = read_2011(_extract_2011(rows), {A, B})
    assert df.set_index("cell_id").to_dict("index") == {
        A: EMPTY | {"dw_total_2011": 91, "dw_pre1919_2011": 30, "dw_1949_1978_2011": 50}}


def test_read_2011_without_hits_is_empty():
    df = read_2011(_extract_2011([f"x,{C},EIGENTUM,4,Kommune,9,0"]), {A})
    assert df.empty and list(df.columns) == COLUMNS_2011


def test_read_2011_stops_on_duplicate_rows():
    rows = [f"x,{A},EIGENTUM,7,Bund oder Land,10,0", f"y,{A},EIGENTUM,7,Bund oder Land,12,0"]
    with pytest.raises(ValueError, match="duplicate.*" + A):
        read_2011(_extract_2011(rows), {A})


def test_read_2011_stops_on_values_that_are_not_numbers():
    rows = [f"x,{A},EIGENTUM,7,Bund oder Land,10,0", f"x,{A},EIGENTUM,1,WEG,k.A.,0", f"x,{B},EIGENTUM,4,Kommune,,0"]
    with pytest.raises(ValueError, match="2 values"):
        read_2011(_extract_2011(rows), {A, B})


def test_read_2011_buildings_keeps_owners_and_sizes():
    rows = [
        f"x,{A},INSGESAMT,0,Einheiten insgesamt,12,0",
        f"x,{A},EIGENTUM,4,Kommune,9,0",
        f"x,{A},EIGENTUM,2,Privatperson/-en,3,0",
        f"x,{A},ZAHLWOHNGN_HHG,5,13 und mehr Wohnungen,9,0",
        f"x,{A},ZAHLWOHNGN_HHG,1,1 Wohnung,3,0",
        f"x,{A},GEBTYPGROESSE,9,Mehrfamilienhaus,9,0",
        f"x,{C},EIGENTUM,4,Kommune,7,0",
    ]
    df = read_2011_buildings(_extract_2011(rows), {A, B})
    empty = {c: 0 for c in COLUMNS_2011_BUILDINGS[1:]}
    assert list(df.columns) == COLUMNS_2011_BUILDINGS
    assert df.set_index("cell_id").to_dict("index") == {A: empty | {
        "bld_municipal_2011": 9, "bld_person_2011": 3, "bld_size_13_plus_2011": 9, "bld_size_1_2011": 3}}


def test_read_2011_buildings_stops_on_duplicate_rows():
    rows = [f"x,{A},ZAHLWOHNGN_HHG,3,3 - 6 Wohnungen,4,0", f"y,{A},ZAHLWOHNGN_HHG,3,3 - 6 Wohnungen,5,0"]
    with pytest.raises(ValueError, match="duplicate"):
        read_2011_buildings(_extract_2011(rows), {A})


def test_grid_files_read_buildings_by_number_of_dwellings():
    columns = GRID_FILES["zensus_buildings_by_size.zip"]
    assert columns == {"1_Wohnung": ("bld_size_1", "count"), "2_Wohnungen": ("bld_size_2", "count"),
                       "3bis6_Wohnungen": ("bld_size_3_6", "count"), "7bis12_Wohnungen": ("bld_size_7_12", "count"),
                       "13undmehr_Wohnungen": ("bld_size_13_plus", "count")}


INSIDE = "CRS3035RES100mN3000000E4220000"   # in BBOX_3035
OUTSIDE = "CRS3035RES100mN2689100E4337000"


def _grid_zip(path, name, text, encoding="utf-8"):
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr(name, text.encode(encoding))
    return path


def test_extract_2022_keeps_header_and_rows_in_the_box(tmp_path):
    z = _grid_zip(tmp_path / "g.zip", "x/Zensus2022_X_100m-Gitter.csv",
             f"GITTER_ID_100m;x_mp_100m;y_mp_100m;Einwohner\r\n{INSIDE};1;2;–\r\n{OUTSIDE};1;2;4\r\n")
    assert extract_grid_2022(z, tmp_path / "out.csv", ["Einwohner"]) == 1
    assert (tmp_path / "out.csv").read_bytes() == \
        f"GITTER_ID_100m;x_mp_100m;y_mp_100m;Einwohner\r\n{INSIDE};1;2;–\r\n".encode("utf-8")


def test_extract_2022_stops_on_another_header_or_two_csv(tmp_path):
    with pytest.raises(ValueError, match="g.zip"):
        extract_grid_2022(_grid_zip(tmp_path / "g.zip", "a_100m.csv", "ID;x\n"), tmp_path / "o.csv", ["x"])
    z = tmp_path / "h.zip"
    with zipfile.ZipFile(z, "w") as zf:
        zf.writestr("a_100m.csv", "GITTER_ID_100m;x\n")
        zf.writestr("b_100m.csv", "GITTER_ID_100m;x\n")
    with pytest.raises(ValueError, match="h.zip"):
        extract_grid_2022(z, tmp_path / "o.csv", ["x"])
    assert not (tmp_path / "o.csv").exists()


def test_extract_2022_stops_without_a_row_in_the_box(tmp_path):
    z = _grid_zip(tmp_path / "g.zip", "a_100m.csv", f"GITTER_ID_100m;x\n{OUTSIDE};1\n")
    with pytest.raises(ValueError, match="no cell"):
        extract_grid_2022(z, tmp_path / "o.csv", ["x"])


def test_extract_2022_stops_on_a_renamed_column_and_keeps_the_old_extract(tmp_path):
    z = _grid_zip(tmp_path / "pop.zip", "a_100m.csv",
                  f"GITTER_ID_100m;x_mp_100m;y_mp_100m;Einwohnerzahl\n{INSIDE};1;2;5\n")
    target = tmp_path / "o.csv"
    target.write_text("good extract")
    with pytest.raises(ValueError, match=r"pop\.zip.*Einwohner\b"):
        extract_grid_2022(z, target, ["Einwohner"])
    assert target.read_text() == "good extract"


def test_extract_2011_stops_on_a_missing_column_and_keeps_the_old_extract(tmp_path):
    head = "Gitter_ID_100m,Gitter_ID_100m_neu,Merkmal,Auspraegung_Text,Anzahl,Anzahl_q\n"
    z = _grid_zip(tmp_path / "w.zip", "Wohnungen100m.csv", head + f"a,{INSIDE},EIGENTUM,x,5,0\n", encoding="latin-1")
    target = tmp_path / "o.csv"
    target.write_text("good extract")
    with pytest.raises(ValueError, match=r"w\.zip.*Auspraegung_Code"):
        extract_grid_2011(z, target, {"EIGENTUM"})
    assert target.read_text() == "good extract"


def test_read_grid_csv_names_the_file_when_a_column_is_missing(tmp_path):
    p = tmp_path / "pop.csv"
    p.write_text(f"GITTER_ID_100m;x_mp_100m;y_mp_100m;Einwohnerzahl\n{INSIDE};1;2;5\n", encoding="utf-8")
    with pytest.raises(ValueError, match=r"pop\.csv.*Einwohner\b"):
        read_grid_csv(p, {"Einwohner": ("pop", "count")})


def test_extract_2011_keeps_the_features_in_the_box_byte_for_byte(tmp_path):
    head = "Gitter_ID_100m,Gitter_ID_100m_neu,Merkmal,Auspraegung_Code,Auspraegung_Text,Anzahl,Anzahl_q\n"
    rows = [f"a,{INSIDE},EIGENTUM,1,Gemeinschaft von Wohnungseigentümern,5,0\n",
            f"a,{INSIDE},HEIZTYP,4,Zentralheizung,3,0\n",
            f"b,{OUTSIDE},EIGENTUM,1,x,3,0\n"]
    z = _grid_zip(tmp_path / "w.zip", "Wohnungen100m.csv", head + "".join(rows), encoding="latin-1")
    assert extract_grid_2011(z, tmp_path / "o.csv", {"EIGENTUM"}) == 1
    assert (tmp_path / "o.csv").read_bytes() == (head + rows[0]).encode("latin-1")


def test_read_grid_csv_reads_an_extract(tmp_path):
    p = tmp_path / "pop.csv"
    p.write_text(f"GITTER_ID_100m;x_mp_100m;y_mp_100m;Einwohner\n{INSIDE};1;2;1,803\n", encoding="utf-8")
    assert read_grid_csv(p, {"Einwohner": ("pop", "count")}) == {INSIDE: {"pop": 1803}}


def test_read_2011_reads_an_extract_for_the_given_cells(tmp_path):
    p = tmp_path / "w.csv"
    p.write_bytes(("Gitter_ID_100m,Gitter_ID_100m_neu,Merkmal,Auspraegung_Code,Auspraegung_Text,Anzahl,Anzahl_q\n"
                   f"a,{INSIDE},EIGENTUM,3,Wohnungsgenossenschaft,7,0\n"
                   f"a,{INSIDE},INSGESAMT,0,Einheiten insgesamt,9,0\n").encode("latin-1"))
    df = read_2011(p, {INSIDE})
    assert df.loc[0, "dw_coop_2011"] == 7 and df.loc[0, "dw_total_2011"] == 9


KM_HEAD = "GITTER_ID_1km;x_mp_1km;y_mp_1km;Leerstandsquote;werterlaeuternde_Zeichen"
KM_INSIDE = "CRS3035RES1000mN3000000E4220000"
KM_BELOW = "CRS3035RES1000mN2988000E4211000"  # y 2988000 to 2989000, the box starts at y 2989900
KM_LEFT = "CRS3035RES1000mN2989000E4210000"   # x 4210000 to 4211000, the box starts at x 4211500
KM_MEETS = "CRS3035RES1000mN2989000E4211000"  # x 4211000 to 4212000, y 2989000 to 2990000: reaches into the box
KM_OUTSIDE = "CRS3035RES1000mN2689000E4341000"


def test_extract_km_2022_keeps_the_squares_that_meet_the_box(tmp_path):
    rows = [f"{KM_INSIDE};4220500;3000500;3,4;", f"{KM_MEETS};4211500;2989500;–;", f"{KM_LEFT};4210500;2989500;2;",
            f"{KM_BELOW};4211500;2988500;1;", f"{KM_OUTSIDE};4341500;2689500;–;"]
    z = tmp_path / "v.zip"
    with zipfile.ZipFile(z, "w") as zf:
        zf.writestr("x/Zensus2022_Leerstandsquote_10km-Gitter.csv", "GITTER_ID_10km;x\n")
        zf.writestr("x/Zensus2022_Leerstandsquote_100m-Gitter.csv", "GITTER_ID_100m;x\n")
        zf.writestr("x/Zensus2022_Leerstandsquote_1km-Gitter.csv", "\r\n".join([KM_HEAD, *rows, ""]).encode("utf-8"))
    assert extract_grid_km_2022(z, tmp_path / "out.csv", "Leerstandsquote") == 2
    assert (tmp_path / "out.csv").read_bytes() == "\r\n".join([KM_HEAD, rows[0], rows[1], ""]).encode("utf-8")


def test_extract_km_2022_stops_on_a_renamed_column_or_without_a_square_in_the_box(tmp_path):
    z = _grid_zip(tmp_path / "v.zip", "a_1km-Gitter.csv", f"{KM_HEAD}\n{KM_OUTSIDE};1;2;3;\n")
    with pytest.raises(ValueError, match="no cell"):
        extract_grid_km_2022(z, tmp_path / "o.csv", "Leerstandsquote")
    with pytest.raises(ValueError, match=r"v\.zip.*Quote"):
        extract_grid_km_2022(z, tmp_path / "o.csv", "Quote")
    assert not (tmp_path / "o.csv").exists()
