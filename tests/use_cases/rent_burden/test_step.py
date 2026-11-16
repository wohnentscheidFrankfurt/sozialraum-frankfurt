import pytest

from pipeline import config
from pipeline.engine.datasets import (NEW_CONSTRUCTION_RENTS, RENT_BURDEN_CHECKS, RENT_BURDEN_GROUPS,
                                      RENT_BURDEN_VIEW, RENT_BURDEN_WAGE, SURVEY_CALC_EXAMPLES, SURVEY_CITY,
                                      SURVEY_RESPONDENTS)
from pipeline.engine.steps import producers
from pipeline.engine.store import Store
from pipeline.use_cases.rent_burden.catalog import LOW_INCOME_TEXTS, WAGE_TEXTS
from pipeline.use_cases.rent_burden.step import STEP
from pipeline.use_cases.survey.model import BREAKDOWN_IDS

NAMES = ("BA_KDU_XLSX", "BA_WAGES_2017_XLSM", "BA_WAGES_SERIES_XLSX", "MIETSPIEGEL_2018_REPORT_PDF",
         "MIETSPIEGEL_2022_REPORT_PDF", "MIETSPIEGEL_2024_REPORT_PDF", "MIETSPIEGEL_2026_REPORT_PDF",
         "HSL_WAGE_DISTRIBUTION_PDF", "HOUSING_MARKET_REPORT_2019_2020_PDF", "BMF_WAGE_TAX_CSV")
CHECKS = {"net wage against BMF", "net wage tariff 2017", "rent wage heading",
          "rent wage sensitivity", "rent wage ceiling", "rent wage measured", "low income heading",
          "low income lead", "low income share"}


def _interim(dataset):
    """A dataset of the last build in interim/. A missing file stops the test and names the step that writes it."""
    from pipeline.build import STEPS
    return Store(config.INTERIM, producers(STEPS)).read(dataset)


@pytest.fixture(scope="module")
def built(tmp_path_factory, run_step):
    """The step on the real sources and the real interim data of the steps new_construction and survey, run once."""
    tables = {d: _interim(d) for d in (NEW_CONSTRUCTION_RENTS, SURVEY_RESPONDENTS, SURVEY_CITY, SURVEY_CALC_EXAMPLES)}
    return run_step(tmp_path_factory.mktemp("built"), STEP, tables, **{n: getattr(config, n) for n in NAMES})


def test_step_writes_both_figures_and_all_checks_pass(built):
    store, logs = built
    wage = store.read(RENT_BURDEN_WAGE)
    assert len(wage) == 4 * 3 * 2  # survey years × persons × contracts
    shares = wage.set_index(["year", "person", "contract"])["share"].round(1)
    # research/2026-11-01-warm-rent-and-income.md, S1: shares
    assert [shares[(y, "mindestlohn", "new")] for y in (2017, 2025)] == [65.6, 61.9]
    assert [shares[(y, "median", "new")] for y in (2017, 2025)] == [31.3, 31.4]
    assert [shares[(y, "high", "old")] for y in (2017, 2025)] == [18.3, 16.6]
    groups = store.read(RENT_BURDEN_GROUPS).set_index("group")
    assert list(groups.index) == list(BREAKDOWN_IDS)
    # the finding, S2: share of the tenants and median of the lowest group
    low = groups.loc[BREAKDOWN_IDS[0]]
    assert (round(low["share"], 1), round(low["median"], 1)) == (16.7, 53.3)
    view = store.read(RENT_BURDEN_VIEW)
    assert set(view) == {"wage", "low_income"}
    assert view["wage"]["title"] == WAGE_TEXTS["title"] and view["low_income"]["title"] == LOW_INCOME_TEXTS["title"]
    assert [c["id"] for c in view["wage"]["contracts"]] == ["new", "old"]
    assert [r["share_text"] for r in view["wage"]["contracts"][0]["rows"]] == ["~62 %", "~31 %", "~21 %"]
    assert len(view["wage"]["info"]["calc_examples"]) == 2
    assert view["low_income"]["info"]["calc_examples"] == [_interim(SURVEY_CALC_EXAMPLES)["LIF_RENT_BURDEN_RATIO"]]
    assert [b["id"] for b in view["low_income"]["bars"]] == list(BREAKDOWN_IDS)
    # the median of the lowest group in whole percent, not in steps of 5 (plan B, call 4)
    assert view["low_income"]["bars"][0]["label"] == LOW_INCOME_TEXTS["median_label"].format(median="~53 %")
    rows = store.read(RENT_BURDEN_CHECKS)
    assert {r["name"] for r in rows} == CHECKS
    assert [r["text"] for r in rows if r["status"] != "OK"] == []
    assert len(logs) == 2  # one line per figure
    assert "2025" in logs[0] and "16.7" in logs[1]


def test_step_stops_when_a_survey_year_lacks_its_kdu_file(tmp_path, run_step):
    cfg = {n: getattr(config, n) for n in NAMES}
    cfg["BA_KDU_XLSX"] = {y: p for y, p in config.BA_KDU_XLSX.items() if y != 2025}
    with pytest.raises(ValueError, match="2025"):
        run_step(tmp_path, STEP, {}, **cfg)
