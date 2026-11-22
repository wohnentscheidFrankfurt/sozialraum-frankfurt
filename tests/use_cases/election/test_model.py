from pipeline import config
from pipeline.use_cases.election.catalog import T, election_indicators
from pipeline.use_cases.election.model import OTHER_COLOR, list_key, shares
from pipeline.use_cases.election.sources import lists, read_party_colors, result_row

COLORS = read_party_colors(config.PARTY_COLORS_CSV)
RESULT = {"Komponente": {"tabelle": {"zeilen": [
    {"label": {"labelKurz": "CDU - Summe Kandidaten-Stimmen"}, "color": "#312f30"},
    {"label": {"labelKurz": "GRÜNE - Summe Kandidaten-Stimmen"}, "color": "#56b460"},
    {"label": {"labelKurz": "Mini - Summe Kandidaten-Stimmen"}, "color": "#000000"}]}}}


def test_lists_and_keys():
    l = lists(RESULT, COLORS)
    assert l[1] == {"position": 2, "name": "GRÜNE", "color": "#52ae32"}  # Statistikportal instead of votemanager
    assert list_key("GRÜNE") == "ELEC_GRUENE" and list_key("Die Linke") == "ELEC_DIELINKE"


def test_lists_invalid_color_becomes_the_other_color():
    rows = [{"label": {"labelKurz": n}, "color": c} for n, c in
              [("A", 'red;" onmouseover="x'), ("B", "#12345"), ("C", "#ABCDEF"), ("D", None)]]
    colors = [l["color"] for l in lists({"Komponente": {"tabelle": {"zeilen": rows}}}, COLORS)]
    assert colors == [OTHER_COLOR, OTHER_COLOR, "#abcdef", OTHER_COLOR]


def test_list_color_from_csv_before_votemanager_before_grey():
    colors = {l["name"]: l["color"] for l in lists(RESULT, COLORS)}
    assert colors == {"CDU": "#1d1d1b", "GRÜNE": "#52ae32", "Mini": "#000000"}  # CSV, CSV, votemanager
    assert read_party_colors(config.PARTY_COLORS_CSV)["FDP"] == "#ffd600" and len(read_party_colors(config.PARTY_COLORS_CSV)) == 22


def test_invalid_csv_color_falls_back_to_votemanager():
    rows = [{"label": {"labelKurz": "X"}, "color": "#123456"}, {"label": {"labelKurz": "Y"}, "color": "kaputt"}]
    l = lists({"Komponente": {"tabelle": {"zeilen": rows}}}, {"X": "red", "Y": "#12345"})
    assert [x["color"] for x in l] == ["#123456", OTHER_COLOR]


def test_share_per_list_has_a_ramp_in_the_list_color():
    city = {"gebiet-name": "Frankfurt am Main", "A": "200", "B": "100", "D": "1000", "D1": "600", "D2": "390", "D3": "10"}
    quarter = [{"gebiet-name": "Altstadt", "A": "100", "B": "40", "D": "400", "D1": "100", "D2": "290", "D3": "10"}]
    k = {m.id: m for m in election_indicators(shares([result_row(r) for r in quarter], result_row(city), lists(RESULT, COLORS))[1], T["de"])}
    assert k["ELEC_CDU"].ramp == "color:#1d1d1b" and k["ELEC_GRUENE"].ramp == "color:#52ae32"
    assert k["ELEC_TURNOUT"].ramp == "teal"


def test_shares():
    city = {"gebiet-name": "Frankfurt am Main", "A": "200", "B": "100", "D": "1000", "D1": "600", "D2": "390", "D3": "10"}
    quarters = [{"gebiet-name": "Altstadt", "A": "100", "B": "40", "D": "400", "D1": "100", "D2": "290", "D3": "10"},
                 {"gebiet-name": "Nied", "A": "100", "B": "60", "D": "600", "D1": "500", "D2": "100", "D3": "0"}]
    df, shown = shares([result_row(r) for r in quarters], result_row(city), lists(RESULT, COLORS))
    assert [g["key"] for g in shown] == ["ELEC_CDU", "ELEC_GRUENE", "ELEC_OTHER"]
    a = df.set_index("quarter")
    assert a.loc["Altstadt", "ELEC_STRONGEST"] == "GRÜNE" and a.loc["Altstadt", "ELEC_GRUENE"] == 72.5
    assert a.loc["Altstadt", "ELEC_OTHER"] == 2.5 and a.loc["Nied", "ELEC_TURNOUT"] == 60.0


def test_shares_keep_eight_decimals():
    """The map rounds once when it shows a value; stored values keep eight decimals (no double rounding)."""
    city = {"gebiet-name": "Frankfurt am Main", "A": "300", "B": "100", "D": "300", "D1": "100", "D2": "100", "D3": "100"}
    quarters = [{"gebiet-name": "Nied", "A": "300", "B": "100", "D": "300", "D1": "100", "D2": "100", "D3": "100"}]
    df, shown = shares([result_row(r) for r in quarters], result_row(city), lists(RESULT, COLORS))
    assert df.loc[0, "ELEC_CDU"] == 33.33333333 and df.loc[0, "ELEC_TURNOUT"] == 33.33333333
    assert shown[0]["city_share"] == 33.33333333


def test_result_row_reads_votemanager_columns():
    raw = {"gebiet-name": " Nied ", "A": "100", "B": "60", "D": "600", "D1": "500", "D2": "100", "D3": "0"}
    assert result_row(raw) == {"name": "Nied", "eligible": 100, "voters": 60, "valid": 600,
                               "votes": {1: 500, 2: 100, 3: 0}}


def test_result_row_needs_the_area_name():
    import pytest
    with pytest.raises(KeyError, match="gebiet-name"):
        result_row({"A": "1", "B": "1", "D": "1"})
