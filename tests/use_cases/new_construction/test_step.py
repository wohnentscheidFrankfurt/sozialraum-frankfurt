import pytest

from pipeline import config
from pipeline.engine.datasets import (NEW_CONSTRUCTION, NEW_CONSTRUCTION_CHECKS, NEW_CONSTRUCTION_RENTS,
                                      NEW_CONSTRUCTION_STOCK, NEW_CONSTRUCTION_VIEW)
from pipeline.use_cases.new_construction.catalog import RENTS_TEXTS as RENTS_BY_LANGUAGE
from pipeline.use_cases.new_construction.step import STEP

RENTS_TEXTS = RENTS_BY_LANGUAGE["de"]

NAMES = ("REGIONAL_COMPLETIONS_CSV", "REGIONAL_ALL_DWELLINGS_CSV", "REGIONAL_NEW_NONRES_CSV",
         "HSL_COMPLETIONS_2025_PDF", "HSL_COMPLETIONS_2024_PDF", "SUBSIDISED_B12_PDF", "ANSWER_F_3150_2025_PDF",
         "ANSWER_F_79_2026_PDF", "ANSWER_F_9_2026_PDF", "ANSWER_F_158_2026_PDF", "ANSWER_B_483_2025_PDF",
         "REGIONAL_STOCK_CSV", "HSL_STOCK_2025_PDF", "HSL_STOCK_2022_OLD_BASE_PDF", "REGIONAL_POPULATION_CSV",
         "HSL_POPULATION_2022_OLD_BASE_PDF", "HSL_POPULATION_2025_PDF", "MIETSPIEGEL_2018_REPORT_PDF",
         "MIETSPIEGEL_2022_REPORT_PDF", "MIETSPIEGEL_2022_PDF", "MIETSPIEGEL_2024_REPORT_PDF", "MIETSPIEGEL_2024_PDF",
         "MIETSPIEGEL_2026_REPORT_PDF", "MIETSPIEGEL_2026_PDF", "HSL_PRICES_PDF", "HSL_WAGES_XLSX", "HOUSEHOLDS_CSV")
RENT_CHECKS = ["rents heading", "rents households", "rents lead older contracts",
               "rents growth rates of the reports", "rents survey dates", "rents uncertainty"]


@pytest.fixture(scope="module")
def built(tmp_path_factory, run_step):
    """The step on the real sources, run once: the tests on unchanged sources read its store and its log."""
    return run_step(tmp_path_factory.mktemp("built"), STEP, {}, **{n: getattr(config, n) for n in NAMES})


def test_step_reads_all_sources_and_writes_the_view(built):
    store, _ = built
    t = store.read(NEW_CONSTRUCTION).astype({"year": int}).set_index("year")  # the store reads keys as text
    # year: (all, new, conversions, subsidised), checked against the sources by hand
    expected = {2011: (2138, 1925, 213, 165), 2017: (5122, 4316, 806, 120), 2020: (4675, 3701, 974, 173),
                2025: (3772, 3481, 291, 689)}
    assert {y: tuple(int(t.loc[y, c]) for c in ("all", "new", "conversions", "subsidised")) for y in expected} == expected
    assert t["all"].sum() == 57692 and t["new"].sum() == 49373 and t["conversions"].sum() == 8319
    assert t["subsidised"].sum() == 4551
    v = store.read(NEW_CONSTRUCTION_VIEW)
    assert len(v["years"]) == 15 and v["years"][-1]["share_text"] == "19,8 %" and v["max"] == 5122
    assert [r["text"] for r in store.read(NEW_CONSTRUCTION_CHECKS) if r["status"] != "OK"] == []
    names = {r["name"] for r in store.read(NEW_CONSTRUCTION_CHECKS)}
    assert names >= {"stock outflow", "stock outflow of the last year", "population report of the last year"}
    assert not names & {"population heading faster", "population lead", "population uncertainty",
                        "population axes proportional"}  # dropped with the chart of the stock


def test_step_writes_the_stock_and_the_population(built):
    store, _ = built
    t = store.read(NEW_CONSTRUCTION_STOCK).astype({"year": int}).set_index("year")
    # checked against the sources by hand on 25.10.2026
    expected = {2011: (366541, 676533), 2015: (380510, 732688), 2021: (406003, 759224), 2022: (404227, 747389),
                2024: (411592, 756021), 2025: (415359, 760656)}
    assert {y: (int(t.loc[y, "stock"]), int(t.loc[y, "population"])) for y in expected} == expected
    assert t["outflow"].isna().sum() == 2 and t["outflow"].sum() == 2009


def test_step_writes_the_rents_the_prices_the_wages_and_their_two_charts(built):
    store, _ = built
    t = store.read(NEW_CONSTRUCTION_RENTS).astype({"year": int}).set_index("year")
    assert list(t.index) == list(range(2017, 2026))
    # index 2025 (2017 = 100), checked against the sources by hand on 31.10.2026
    assert [round(t.loc[2025, c], 1) for c in ("new_index", "wages_index", "prices_index", "old_index", "stock_index",
                                              "population_index")] == [136.6, 130.1, 125.0, 116.3, 106.6, 101.8]
    assert [round(t.loc[2025, c], 1) for c in ("new_real", "wages_real", "old_real")] == [109.3, 104.1, 93.1]
    assert (t.loc[2017, "new"], t.loc[2025, "new"], t.loc[2017, "old"], t.loc[2025, "old"]) == (10.21, 13.95, 8.69, 10.11)
    assert list(t["new"].dropna().index) == [2017, 2021, 2023, 2025]
    view = store.read(NEW_CONSTRUCTION_VIEW)
    assert "stock" not in view  # the chart of the stock against the population is gone
    rents = view["rents"]
    assert [c["id"] for c in rents["charts"]] == ["nominal", "real"]
    assert rents["title"] == RENTS_TEXTS["title"]
    ends = {c["id"]: {s["id"]: s["end_value_text"] for s in c["series"]} for c in rents["charts"]}
    assert ends == {"nominal": {"prices": "125,0", "wages": "130,1", "dwellings": "106,6", "population": "101,8",
                                "new": "136,6", "old": "116,3"},
                    "real": {"prices": "100,0", "wages": "104,1", "new": "109,3", "old": "93,1"}}
    assert len(view["years"]) == 15 and view["max"] == 5122  # the column chart stays


def test_step_checks_the_rents_and_all_pass(built):
    store, _ = built
    rows = store.read(NEW_CONSTRUCTION_CHECKS)
    assert {r["name"]: r["status"] for r in rows if r["name"].startswith("rents ")} == {n: "OK" for n in RENT_CHECKS}
    assert [r["text"] for r in rows if r["status"] != "OK"] == []


def test_step_logs_the_index_of_the_last_year_in_one_line(built):
    _, logs = built
    lines = [line for line in logs if line.startswith("rents index")]
    assert lines == ["rents index 2025 (2017 = 100): new 136.6, old 116.3, prices 125.0, wages 130.1, dwellings 106.6, "
                     "population 101.8; without inflation: new 109.3, old 93.1, wages 104.1"]
    assert not [line for line in logs if "2015" in line]  # the growth of the stocks runs from 2017


def test_step_stops_when_a_survey_brochure_has_another_survey_day(tmp_path, run_step):
    cfg = {n: getattr(config, n) for n in NAMES}
    cfg["MIETSPIEGEL_2026_PDF"] = config.MIETSPIEGEL_2024_PDF  # its survey day is of the Mietspiegel 2024
    with pytest.raises(ValueError, match="Mietspiegel 2025"):
        run_step(tmp_path, STEP, {}, **cfg)


def test_step_stops_when_the_price_report_is_no_report_of_prices(tmp_path, run_step):
    cfg = {n: getattr(config, n) for n in NAMES}
    cfg["HSL_PRICES_PDF"] = config.HSL_STOCK_2025_PDF
    with pytest.raises(ValueError, match="M I 2 j/25"):
        run_step(tmp_path, STEP, {}, **cfg)


def test_step_stops_when_the_household_csv_lacks_the_row_of_the_city(tmp_path, run_step):
    text = config.HOUSEHOLDS_CSV.read_text(encoding="utf-8")
    csv = tmp_path / "households.csv"
    csv.write_text("\n".join(r for r in text.splitlines() if "insgesamt;insgesamt;" not in r) + "\n",
                   encoding="utf-8")
    with pytest.raises(ValueError, match="households"):
        run_step(tmp_path, STEP, {}, **{**{n: getattr(config, n) for n in NAMES}, "HOUSEHOLDS_CSV": csv})


def test_step_stops_when_the_population_report_is_of_another_base_or_day(tmp_path, run_step):
    cfg = {n: getattr(config, n) for n in NAMES}
    cfg["HSL_POPULATION_2022_OLD_BASE_PDF"] = config.HSL_STOCK_2022_OLD_BASE_PDF  # a report of the dwellings
    with pytest.raises(ValueError, match="A I 2"):
        run_step(tmp_path, STEP, {}, **cfg)


def test_step_stops_when_the_population_reports_are_swapped(tmp_path, run_step):
    cfg = {n: getattr(config, n) for n in NAMES}
    cfg["HSL_POPULATION_2025_PDF"] = config.HSL_POPULATION_2022_OLD_BASE_PDF  # on the Zensus 2011
    with pytest.raises(ValueError, match="A I 2.*Basis Zensus.*2022"):
        run_step(tmp_path, STEP, {}, **cfg)
    cfg = {n: getattr(config, n) for n in NAMES}
    cfg["HSL_POPULATION_2022_OLD_BASE_PDF"] = config.HSL_POPULATION_2025_PDF  # on the Zensus 2022
    with pytest.raises(ValueError, match="A I 2.*Basis Zensus.*2011"):
        run_step(tmp_path, STEP, {}, **cfg)


@pytest.mark.parametrize("year, message", [(2025, "population: no value for 2025"), (2026, "population.*2026")])
def test_step_stops_when_the_population_csv_lacks_the_last_year_or_has_a_later_one(year, message, tmp_path, run_step):
    text = config.REGIONAL_POPULATION_CSV.read_text(encoding="utf-8")
    if year == 2025:
        text = "\n".join(r for r in text.splitlines() if ";2025-12-31;" not in r) + "\n"
    else:
        row = next(r for r in text.splitlines() if ";%TOTAL%;" in r and ";2025-12-31;" in r)
        text += row.replace("2025", "2026") + "\n"
    csv = tmp_path / "population.csv"
    csv.write_text(text, encoding="utf-8")
    with pytest.raises(ValueError, match=message):
        run_step(tmp_path, STEP, {}, **{**{n: getattr(config, n) for n in NAMES}, "REGIONAL_POPULATION_CSV": csv})


def test_step_stops_when_the_stock_report_has_no_table_4(tmp_path, run_step):
    cfg = {n: getattr(config, n) for n in NAMES}
    cfg["HSL_STOCK_2025_PDF"] = config.HSL_COMPLETIONS_2025_PDF  # holds no table 4
    with pytest.raises(ValueError, match="F I 1"):
        run_step(tmp_path, STEP, {}, **cfg)


def test_step_stops_when_the_stock_reports_are_swapped(tmp_path, run_step):
    cfg = {n: getattr(config, n) for n in NAMES}
    cfg["HSL_STOCK_2022_OLD_BASE_PDF"] = config.HSL_STOCK_2025_PDF  # on the Gebäude- und Wohnungszählung 2022
    with pytest.raises(ValueError, match="Wohnungszählung 2011"):
        run_step(tmp_path, STEP, {}, **cfg)
    cfg = {n: getattr(config, n) for n in NAMES}
    cfg["HSL_STOCK_2025_PDF"] = config.HSL_STOCK_2022_OLD_BASE_PDF  # on the Gebäude- und Wohnungszählung 2011
    with pytest.raises(ValueError, match="Wohnungszählung 2022"):
        run_step(tmp_path, STEP, {}, **cfg)


def test_step_stops_when_the_stock_csv_already_has_the_last_year(tmp_path, run_step):
    text = config.REGIONAL_STOCK_CSV.read_text(encoding="utf-8")
    row = next(r for r in text.splitlines() if "WOHNY1$QMU" in r and ";%TOTAL%;" in r and ";2024-12-31;" in r)
    csv = tmp_path / "stock.csv"
    csv.write_text(text + row.replace("2024", "2025") + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="2025"):
        run_step(tmp_path, STEP, {}, **{**{n: getattr(config, n) for n in NAMES}, "REGIONAL_STOCK_CSV": csv})


def test_step_stops_when_the_report_is_not_of_the_last_year(tmp_path, run_step):
    cfg = {n: getattr(config, n) for n in NAMES}
    cfg["HSL_COMPLETIONS_2025_PDF"] = config.HSL_COMPLETIONS_2024_PDF  # reports 2024, not 2025
    with pytest.raises(ValueError, match="2025"):
        run_step(tmp_path, STEP, {}, **cfg)


def test_step_stops_when_the_csv_already_has_the_last_year(tmp_path, run_step):
    text = config.REGIONAL_COMPLETIONS_CSV.read_text(encoding="utf-8")
    row = next(r for r in text.splitlines() if "WOHN01$QMU" in r and "%TOTAL%" in r and ";2024;" in r)
    csv = tmp_path / "regional.csv"
    csv.write_text(text + row.replace("2024", "2025") + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="2025"):
        run_step(tmp_path, STEP, {}, **{**{n: getattr(config, n) for n in NAMES}, "REGIONAL_COMPLETIONS_CSV": csv})


@pytest.mark.parametrize("name", ["REGIONAL_ALL_DWELLINGS_CSV", "REGIONAL_NEW_NONRES_CSV"])
def test_step_stops_when_a_csv_already_has_the_last_year(name, tmp_path, run_step):
    content, column, key = {"REGIONAL_ALL_DWELLINGS_CSV": ("WOHN02$QMU", "WHGGR2", "%TOTAL%"),
                            "REGIONAL_NEW_NONRES_CSV": ("WOHN01$QMU", "BAUF04", "WOHNNG")}[name]
    text = getattr(config, name).read_text(encoding="utf-8")
    row = next(r for r in text.splitlines() if content in r and f";{key};" in r and ";2024;" in r)
    csv = tmp_path / "regional.csv"
    csv.write_text(text + row.replace("2024", "2025") + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="2025"):
        run_step(tmp_path, STEP, {}, **{**{n: getattr(config, n) for n in NAMES}, name: csv})
