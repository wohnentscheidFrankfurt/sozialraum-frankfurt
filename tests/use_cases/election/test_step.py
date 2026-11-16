import json
from types import SimpleNamespace


from pipeline.engine.datasets import ELECTION_BY_QUARTER, ELECTION_CHECKS, ELECTION_CITY, ELECTION_LISTS
from pipeline.use_cases.election import step

HEADER = "gebiet-name;A;B;D;D1;D2;D3\n"
RESULT = {"Komponente": {"tabelle": {"zeilen": [
    {"label": {"labelKurz": "CDU - Summe Kandidaten-Stimmen"}, "color": "#312f30"},
    {"label": {"labelKurz": "GRÜNE - Summe Kandidaten-Stimmen"}, "color": "#56b460"},
    {"label": {"labelKurz": "Mini - Summe Kandidaten-Stimmen"}, "color": "#000000"}]}}}


def _cache(tmp_path, quarters):
    (tmp_path / "election_result.json").write_text(json.dumps(RESULT), encoding="utf-8")
    (tmp_path / "election_city.csv").write_text(HEADER + "Frankfurt am Main;200;100;1000;600;390;10\n", encoding="utf-8")
    (tmp_path / "election_quarters.csv").write_text(HEADER + quarters, encoding="utf-8")
    (tmp_path / "colors.csv").write_text("name,color,source\nCDU,#1d1d1b,x\nGRÜNE,#52ae32,x\n", encoding="utf-8")
    return SimpleNamespace(ELECTION_RESULT_JSON=tmp_path / "election_result.json",
                           ELECTION_CITY_CSV=tmp_path / "election_city.csv",
                           ELECTION_QUARTERS_CSV=tmp_path / "election_quarters.csv",
                           PARTY_COLORS_CSV=tmp_path / "colors.csv", GAZETTE_PDF=tmp_path / "gazette.pdf")


def test_step_on_a_fake_store(tmp_path, monkeypatch, run_step):
    config_ = _cache(tmp_path, "001;100;40;400;100;290;10\n002;100;60;600;500;100;0\n")
    monkeypatch.setattr(step, "read_gazette_text", lambda path: "Wahlberechtigte 200 Wähler 100 gültige 1.000 600 390")
    store, _ = run_step(tmp_path, step.STEP, {}, **vars(config_))
    q = store.read(ELECTION_BY_QUARTER).set_index("id")
    assert list(q.index) == ["001", "002"] and "quarter" not in q.columns
    assert q.loc["001", "ELEC_STRONGEST"] == "GRÜNE" and q.loc["001", "ELEC_GRUENE"] == 72.5
    lists = store.read(ELECTION_LISTS)
    assert [l["key"] for l in lists["lists"]] == ["ELEC_CDU", "ELEC_GRUENE", "ELEC_OTHER"]
    assert lists["city"] == {"ELEC_CDU": 60.0, "ELEC_GRUENE": 39.0, "ELEC_OTHER": 1.0, "ELEC_TURNOUT": 50.0}
    assert store.read(ELECTION_CITY) == [{"indicator": k, "value": v, "kind": "published"}
                                         for k, v in lists["city"].items()]
    assert [r["status"] for r in store.read(ELECTION_CHECKS)] == ["OK", "OK"]


def test_step_writes_a_failing_check_instead_of_stopping(tmp_path, monkeypatch, run_step):
    config_ = _cache(tmp_path, "001;100;40;400;100;290;10\n")  # one quarter only: the sum differs
    monkeypatch.setattr(step, "read_gazette_text", lambda path: None)
    store, _ = run_step(tmp_path, step.STEP, {}, **vars(config_))
    assert [r["status"] for r in store.read(ELECTION_CHECKS)] == ["FAIL", "FAIL"]
