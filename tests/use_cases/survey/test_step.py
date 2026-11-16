import pandas as pd

from pipeline import config
from pipeline.engine.datasets import (SURVEY_BY_DISTRICT, SURVEY_CALC_EXAMPLES, SURVEY_CHECKS, SURVEY_CITY,
                                      SURVEY_HALF_WIDTHS, SURVEY_RESPONDENTS)
from pipeline.use_cases.survey.catalog import CALC_EXAMPLE_HOUSEHOLD
from pipeline.use_cases.survey.model import BREAKDOWN_IDS, burden_ratios
from pipeline.use_cases.survey.sources import read_microdata
from pipeline.use_cases.survey.step import STEP


def test_survey_step_writes_the_class_per_district_and_the_city_values(tmp_path, run_step):
    store, _ = run_step(tmp_path, STEP, {}, DISTRICTS_GML=config.DISTRICTS_GML, MONITORING_CSV=config.MONITORING_CSV,
                        SURVEY_REPORT_PDF=config.SURVEY_REPORT_PDF, SURVEY_REPORT_2024_PDF=config.SURVEY_REPORT_2024_PDF,
                        SURVEY_MICRODATA=config.SURVEY_MICRODATA)
    by_district = store.read(SURVEY_BY_DISTRICT)
    assert len(by_district) == 114 and by_district["id"].is_unique and "survey_area" not in by_district.columns
    assert by_district.notna().all().all()
    # the income groups: rounded to 5 points, the same in every district of a survey area
    assert set(BREAKDOWN_IDS) <= set(by_district.columns)
    assert ((by_district[list(BREAKDOWN_IDS)] % 5) == 0).all().all()
    city = store.read(SURVEY_CITY)
    assert city[:2] == [{"indicator": "LIF_RENT_BURDEN_RATIO", "value": 29, "kind": "published"},
                        {"indicator": "LIF_ATTACHMENT", "value": 62, "kind": "published"}]
    assert [(r["indicator"], r["kind"]) for r in city[2:]] == [(k, "computed") for k in BREAKDOWN_IDS]
    assert [r["value"] for r in city[2:]] == [55, 35, 25]
    widths = store.read(SURVEY_HALF_WIDTHS)
    assert set(widths) == {"typical", "max_low", "max_upper"} and 0 < widths["typical"] <= widths["max_low"]
    assert (round(widths["typical"]), round(widths["max_low"]), round(widths["max_upper"])) == (5, 13, 4)
    example = store.read(SURVEY_CALC_EXAMPLES)["LIF_RENT_BURDEN_RATIO"]
    assert example["area"] == CALC_EXAMPLE_HOUSEHOLD
    assert [r["number"] for r in example["rows"]] == [550, 175, 725, 1500, 48]
    checks = store.read(SURVEY_CHECKS)
    assert len(checks) == 4 and [r["status"] for r in checks] == ["OK"] * 4


def test_step_writes_the_respondents_and_their_round_trip_keeps_the_ratios(tmp_path, run_step):
    store, _ = run_step(tmp_path, STEP, {}, DISTRICTS_GML=config.DISTRICTS_GML, MONITORING_CSV=config.MONITORING_CSV,
                        SURVEY_REPORT_PDF=config.SURVEY_REPORT_PDF, SURVEY_REPORT_2024_PDF=config.SURVEY_REPORT_2024_PDF,
                        SURVEY_MICRODATA=config.SURVEY_MICRODATA)
    direct = pd.concat([read_microdata(path, year) for year, path in config.SURVEY_MICRODATA.items()],
                       ignore_index=True)
    columns = ["ratio", "group", "weight"]
    pd.testing.assert_frame_equal(burden_ratios(store.read(SURVEY_RESPONDENTS))[columns],
                                  burden_ratios(direct)[columns], check_exact=True)
