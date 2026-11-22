import importlib.util
import re
from pathlib import Path

import pytest

from pipeline.shared.core.checks import FAIL, OK, WARN
from pipeline.use_cases.new_construction.catalog import PHRASES as PHRASES_BY_LANGUAGE
from pipeline.use_cases.new_construction.catalog import (RENT_AXES, RENTS_TEXTS as RENTS_BY_LANGUAGE, SURVEY_DATES, T,
                                                         TEXTS as TEXTS_BY_LANGUAGE)
from pipeline.use_cases.new_construction.checks import new_construction_checks, rents_checks, shown_month, stock_checks
from pipeline.use_cases.new_construction.model import (facts, rents_facts, rents_table, rents_view, series,
                                                       stock_facts, stock_series, year_prices, year_wages)

TEXTS, RENTS_TEXTS, PHRASES, LANG = (TEXTS_BY_LANGUAGE["de"], RENTS_BY_LANGUAGE["de"], PHRASES_BY_LANGUAGE["de"],
                                     T["de"])
OUTFLOW_CAVEAT = PHRASES["outflow_caveat"]

NEW_RES = {2011: 1905, 2012: 2144, 2013: 2768, 2014: 3556, 2015: 4076, 2016: 3472, 2017: 4047, 2018: 3244,
           2019: 3941, 2020: 3371, 2021: 3012, 2022: 2498, 2023: 2842, 2024: 3463, 2025: 3463}
NEW_NONRES = {2011: 20, 2012: 68, 2013: 17, 2014: 9, 2015: 1, 2016: 46, 2017: 269, 2018: 7, 2019: 15, 2020: 330,
              2021: 280, 2022: 188, 2023: 286, 2024: 17, 2025: 18}
ALL = {2011: 2138, 2012: 2682, 2013: 3156, 2014: 4418, 2015: 4325, 2016: 4273, 2017: 5122, 2018: 3761, 2019: 4641,
       2020: 4675, 2021: 3914, 2022: 2951, 2023: 3661, 2024: 4203, 2025: 3772}
SUBSIDISED = {2011: (83, 82), 2012: (90, 109), 2013: (56, 52), 2014: (307, 96), 2015: (431, 67), 2016: (226, 64),
              2017: (68, 52), 2018: (52, 318), 2019: (111, 298), 2020: (53, 120), 2021: (131, 210),
              2022: (160, 88), 2023: (182, 108), 2024: (131, 117), 2025: (343, 346)}

B483 = {2019: 3663, 2020: 4349, 2021: 3914, 2022: 2951, 2023: 3661, 2024: 4203}  # B 483/2025, Zu Frage 1


def run(new_res=NEW_RES, new_nonres=NEW_NONRES, all_=ALL, subsidised=SUBSIDISED, report=(2024, 262, 3463),
        confirm=343, report_all=(2024, 4203), report_nonres=(2024, 17), b483=B483, texts=TEXTS, detail=False):
    t = series(new_res, new_nonres, all_, subsidised, 2011, 2025, 2023)
    checks = new_construction_checks(t, facts(t, 10), report, confirm, report_all, report_nonres, b483, texts, PHRASES, LANG)
    return {c.name: c for c in checks} if detail else {c.name: c.status for c in checks}


def test_all_hold_on_the_real_numbers():
    result = run()
    assert set(result.values()) == {OK}
    assert "texts of the ⓘ" in result and "conversions not negative" in result
    assert "HSL report 2024 tables 15 and 19" in result


def test_fifth_fails_when_the_share_reaches_a_fifth():
    assert run(subsidised={**SUBSIDISED, 2025: (343, 400)})["heading fifth"] == FAIL


def test_eighth_fails_when_an_earlier_share_exceeds_an_eighth():
    assert run(subsidised={**SUBSIDISED, 2015: (431, 100)})["heading eighth"] == FAIL


def test_average_fails_when_it_rounds_to_another_hundred():
    assert run(all_={**ALL, 2017: 5700})["lead average"] == FAIL  # mean 4,155.1
    assert run(all_={**ALL, 2015: 9000})["lead average"] == OK  # outside the last ten years
    c = run(all_={**ALL, 2022: 2400}, detail=True)["lead average"]  # mean 4,042.2
    assert c.status == FAIL and "2016–2025" in c.text and "4.042" in c.text


def test_conversions_fail_when_a_year_is_negative_and_the_text_names_it():
    c = run(all_={**ALL, 2016: 3400}, detail=True)["conversions not negative"]
    assert c.status == FAIL and "2016" in c.text


def test_report_2024_and_confirmation():
    assert run(report=(2024, 262, 3500))["HSL report 2024"] == WARN
    assert run(report=(2023, 262, 3463))["HSL report 2024"] == WARN
    assert run(confirm=300)["FW 1 of the last year"] == WARN


def test_report_2024_tables_15_and_19_warn_when_they_differ_from_the_regionaldatenbank():
    name = "HSL report 2024 tables 15 and 19"
    assert run(report_all=(2024, 4200))[name] == WARN
    assert run(report_nonres=(2024, 20))[name] == WARN
    assert run(report_all=(2023, 4203))[name] == WARN
    assert run(report_nonres=(2023, 17))[name] == WARN


def test_texts_of_the_info_fail_when_a_phrase_is_gone():
    info = TEXTS["info"]
    assert run(texts={**TEXTS, "info": {**info, "rule": info["rule"].replace("2023 bis 2025", "ab 2023")}}
               )["texts of the ⓘ"] == FAIL
    assert run(texts={**TEXTS, "info": {**info, "uncertainty": info["uncertainty"].replace("2023 bis 2025", "ab 2023")}}
               )["texts of the ⓘ"] == FAIL


def test_gap_of_2019_and_2020_fails_when_the_totals_are_no_longer_above_the_magistrat():
    name = "gap of 2019 and 2020"
    assert run()[name] == OK
    assert run(all_={**ALL, 2019: 3663})[name] == FAIL
    assert run(all_={**ALL, 2020: 4300})[name] == FAIL
    assert run(b483={**B483, 2019: 4700})[name] == FAIL
    assert run(b483={2021: 3914})[name] == FAIL  # a missing year is no proof



# The fixtures of test_model.py (stocks, bridge, surveys, VPI, wages, households). With --import-mode=importlib a test
# module cannot import another one, so this file loads it like tests/test_compare_build.py loads its script.
_spec = importlib.util.spec_from_file_location("test_model_fixtures", Path(__file__).with_name("test_model.py"))
tm = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(tm)
STOCK, POPULATION, BRIDGE = tm.STOCK, tm.POPULATION, tm.BRIDGE
SURVEYS, VPI, WAGES, HOUSEHOLDS = tm.SURVEYS, tm.VPI, tm.WAGES, tm.HOUSEHOLDS
REPORT_2025 = (2025, 760656)  # HSL, A I 2 mit A II, A III, A V, 2. Halbjahr 2025, PDF pages 28 and 35
MONTHS = {y: s["month"][1] for y, s in SURVEYS.items()}  # the survey month of each survey year
GROWTHS = {2021: {"new": 13.2, "old": 5.2}, 2025: {"new": 6.9, "old": 7.2}}  # percent, as the reports print them
# axes wide enough for the tests that push a line far away (the real axes make rents_view stop)
WIDE = {cid: {**axis, "min": 50, "max": 200} for cid, axis in RENT_AXES.items()}


def run_stock(stock=STOCK, population=POPULATION, all_=ALL, texts=RENTS_TEXTS, bridge=BRIDGE, report=REPORT_2025,
              detail=False):
    t = stock_series(stock, population, all_, 2011, 2025, (2022,))
    checks = stock_checks(t, stock_facts(t, 2017, (2022,), bridge), report, texts, PHRASES)
    return {c.name: c for c in checks} if detail else {c.name: c.status for c in checks}


def test_stock_checks_hold_on_the_real_numbers():
    assert run_stock() == {"stock outflow": OK, "stock outflow of the last year": OK,
                           "population report of the last year": OK}


def test_population_report_warns_when_it_differs_from_the_regionaldatenbank_or_is_of_another_year():
    name = "population report of the last year"
    c = run_stock(detail=True)[name]
    assert c.status == OK and "760656" in c.text
    c = run_stock(report=(2025, 760600), detail=True)[name]
    assert c.status == WARN and "760600" in c.text and "760656" in c.text
    c = run_stock(report=(2024, 760656), detail=True)[name]
    assert c.status == WARN and "2024" in c.text


def test_stock_outflow_warns_when_a_year_is_negative_and_names_it():
    c = run_stock(stock={**STOCK, 2016: 385000}, detail=True)["stock outflow"]  # change 4,490, completed 4,273
    assert c.status == WARN and "2016" in c.text


def without_caveat():
    info = RENTS_TEXTS["info"]
    return {**RENTS_TEXTS, "info": {**info, "uncertainty": info["uncertainty"].replace(" " + OUTFLOW_CAVEAT, "")}}


def test_stock_outflow_of_the_last_year_needs_the_caveat_of_the_info_and_names_both_numbers():
    name = "stock outflow of the last year"
    assert OUTFLOW_CAVEAT in RENTS_TEXTS["info"]["uncertainty"]
    c = run_stock(texts=without_caveat(), detail=True)[name]  # outflow 2025: 5, mean of the other years 167.0
    assert c.status == FAIL and "5" in c.text and "167.0" in c.text
    c = run_stock(detail=True)[name]
    assert c.status == OK and "5" in c.text and "167.0" in c.text


def test_stock_outflow_of_the_last_year_needs_no_caveat_from_a_third_of_the_mean():
    # stock 2025 415,200: change 3,608, outflow 164, mean of the other years 167.0
    assert run_stock(stock={**STOCK, 2025: 415200}, texts=without_caveat())["stock outflow of the last year"] == OK


NAMES = ["rents heading", "rents households", "rents lead older contracts", "rents growth rates of the reports",
         "rents survey dates", "rents uncertainty"]


def run_rents(surveys=SURVEYS, vpi=VPI, months=None, wages=WAGES, stock=STOCK, population=POPULATION, bridge=BRIDGE,
              households=HOUSEHOLDS, axes=RENT_AXES, growths=GROWTHS, texts=RENTS_TEXTS, read_surveys=None,
              read_vpi=None, detail=False):
    """The checks of the block on a table built the way the step builds it (`surveys`, `vpi` and `months` feed the
    table). `read_surveys` and `read_vpi` are what the checks get as read from the sources; by default the same."""
    stocks = tm.stock_table(stock, population)
    prices = year_prices(vpi, MONTHS if months is None else months, 2017, 2025, 7)
    t = rents_table(stocks, surveys, prices, year_wages(wages, (2, 3), 2017, 2025), 2017, 2025)
    f = rents_facts(t, stock_facts(stocks, 2017, (2022,), bridge), households, 2017, 2025)
    view = rents_view(t, f, RENTS_TEXTS, bridge, (2022,), axes, LANG)
    checks = rents_checks(t, f, view, growths, surveys if read_surveys is None else read_surveys,
                          vpi if read_vpi is None else read_vpi, texts, PHRASES, LANG)
    return {c.name: c for c in checks} if detail else {c.name: c.status for c in checks}


def test_rents_checks_hold_on_the_real_numbers():
    result = run_rents()
    assert list(result) == NAMES
    assert set(result.values()) == {OK}


def test_heading_fails_when_the_dwellings_grow_slower_than_the_population():
    # dwellings 2025 395,000: 1.41 % published against 1.84 %, chained 2.50 % against 5.34 %
    c = run_rents(stock={**STOCK, 2025: 395000}, detail=True)["rents heading"]
    assert c.status == FAIL and "1.41" in c.text and "1.84" in c.text and "2.50" in c.text and "5.34" in c.text


def test_heading_fails_when_the_dwellings_are_faster_with_one_calculation_only():
    # population on the old base 800,000: chained 9.01 % against the dwellings' 7.79 %, published 1.84 % against 6.63 %
    c = run_rents(bridge={**BRIDGE, "population": {2022: 800000}}, detail=True)["rents heading"]
    assert c.status == FAIL and "9.01" in c.text and "7.79" in c.text and "6.63" in c.text


def test_heading_holds_when_the_new_rents_lag_the_dwellings_without_inflation_only():
    # dwellings 2025 428,500: 10.01 % published, 11.20 % chained; new rents 36.63 % in Euro, 9.30 % without inflation.
    # The heading speaks of Euro; without inflation the gap lies within the sampling error (docs/data-rules.md)
    c = run_rents(stock={**STOCK, 2025: 428500}, detail=True)["rents heading"]
    assert c.status == OK and "36.63" in c.text and "9.30" in c.text and "not checked" in c.text


def test_heading_fails_when_the_new_rents_in_euro_lag_the_dwellings():
    # new rent 2025 10.80 €/m²: +5.78 % in Euro, below the dwellings' 6.63 % published and 7.79 % chained
    c = run_rents(surveys={**SURVEYS, 2025: {**SURVEYS[2025], "new": 10.80}}, axes=WIDE, detail=True)["rents heading"]
    assert c.status == FAIL and "5.78" in c.text and "6.63" in c.text
    # new rent 2025 10.92 €/m²: +6.95 % in Euro, above the published 6.63 % but below the chained 7.79 %
    c = run_rents(surveys={**SURVEYS, 2025: {**SURVEYS[2025], "new": 10.92}}, axes=WIDE, detail=True)["rents heading"]
    assert c.status == FAIL and "6.95" in c.text and "7.79" in c.text


def test_heading_fails_when_the_new_rents_in_euro_lead_the_dwellings_by_less_than_the_margin():
    # new rent 2025 11.40 €/m²: +11.66 % in Euro, 3.87 points above the chained 7.79 %, below the margin of 4
    c = run_rents(surveys={**SURVEYS, 2025: {**SURVEYS[2025], "new": 11.40}}, detail=True)["rents heading"]
    assert c.status == FAIL and "11.66" in c.text and "4 points" in c.text
    # 11.45 €/m²: +12.14 %, 4.35 points above the chained growth
    assert run_rents(surveys={**SURVEYS, 2025: {**SURVEYS[2025], "new": 11.45}})["rents heading"] == OK


def test_heading_compares_the_new_rents_with_both_calculations_of_the_dwellings():
    # stock on the old base 400,000: chained 5.52 %, below the published 6.63 %. New rent 2025 11.23 €/m²: +9.99 %,
    # 4.47 points above the chained growth, but only 3.36 above the published one
    surveys = {**SURVEYS, 2025: {**SURVEYS[2025], "new": 11.23}}
    c = run_rents(bridge={**BRIDGE, "stock": {2022: 400000}}, surveys=surveys, detail=True)["rents heading"]
    assert c.status == FAIL and "5.52" in c.text and "6.63" in c.text and "9.99" in c.text


def test_heading_fails_unless_the_title_starts_with_seit_2017():
    for title in (RENTS_TEXTS["title"].removeprefix("Seit 2017 "), RENTS_TEXTS["title"].replace("2017", "2015")):
        c = run_rents(texts={**RENTS_TEXTS, "title": title}, detail=True)["rents heading"]
        assert c.status == FAIL and "„Seit 2017“" in c.text
    c = run_rents(detail=True)["rents heading"]
    assert c.status == OK and "„Seit 2017“" in c.text and "36.63" in c.text and "9.30" in c.text


def test_households_hold_when_the_info_names_the_lowest_and_the_highest_size():
    c = run_rents(detail=True)["rents households"]
    assert c.status == OK and "1.8446" in c.text and "1.8741" in c.text
    assert "1,84" in c.text and "1,87" in c.text  # the range the rule of the ⓘ names, as the map shows it


def test_households_fail_when_a_year_lies_outside_the_named_range():
    # 2020 with 1.90 persons per household: the highest size reads 1,90, the ⓘ says 1,87
    c = run_rents(households={**HOUSEHOLDS, 2020: 1.90}, detail=True)["rents households"]
    assert c.status == FAIL and "1,90" in c.text
    # 2023 with 1.80: the lowest size reads 1,80, the ⓘ says 1,84
    c = run_rents(households={**HOUSEHOLDS, 2023: 1.80}, detail=True)["rents households"]
    assert c.status == FAIL and "1,80" in c.text


def test_households_fail_when_the_info_drops_the_range():
    info = RENTS_TEXTS["info"]
    # the rule without the sentence of the range
    rule = " ".join(s for s in re.split(r"(?<=\.) ", info["rule"]) if "1,84" not in s)
    assert rule != info["rule"] and "1,87" not in rule
    texts = {**RENTS_TEXTS, "info": {**info, "rule": rule}}
    assert run_rents(texts=texts)["rents households"] == FAIL


def test_older_contracts_fail_when_their_index_is_above_the_wages():
    # wages 2025 mean 97.5: index 109.80, below the older contracts' 116.34 (the prices stay at 125.00)
    c = run_rents(wages={**WAGES, (2025, 2): 100.0, (2025, 3): 95.0}, detail=True)["rents lead older contracts"]
    assert c.status == FAIL and "116.34" in c.text and "109.80" in c.text


def test_older_contracts_fail_when_their_index_is_above_the_prices_and_without_inflation_above_100():
    # prices 2025 index 113.17 (VPI 110.0): older 116.34 and, without inflation, 102.80
    c = run_rents(vpi={**VPI, (2025, 7): 110.0}, axes=WIDE, detail=True)["rents lead older contracts"]
    assert c.status == FAIL and "113.17" in c.text and "102.80" in c.text
    # older rent 2025 11.50: index 132.34, above prices and wages
    surveys = {**SURVEYS, 2025: {**SURVEYS[2025], "old": 11.5}}
    assert run_rents(surveys=surveys)["rents lead older contracts"] == FAIL


def test_older_contracts_hold_on_the_real_numbers_and_name_both_charts():
    c = run_rents(detail=True)["rents lead older contracts"]
    assert c.status == OK and "116.34" in c.text and "125.00" in c.text and "130.07" in c.text and "93.07" in c.text
    # a lead without the claim
    assert run_rents(texts={**RENTS_TEXTS, "lead": "L"})["rents lead older contracts"] == FAIL


def test_report_growths_fail_when_the_older_and_the_new_rents_of_2017_are_swapped():
    old, new = SURVEYS[2017]["old"], SURVEYS[2017]["new"]
    swapped = {**SURVEYS, 2017: {**SURVEYS[2017], "new": old, "old": new}}
    # the table and the facts are built from the swapped rents; the printed 13.2 % and 5.2 % no longer fit
    c = run_rents(surveys=swapped, axes=WIDE, detail=True)["rents growth rates of the reports"]
    assert c.status == FAIL and "33.03" in c.text and "-10.48" in c.text and "13.2" in c.text
    c = run_rents(detail=True)["rents growth rates of the reports"]
    assert c.status == OK and "13.22" in c.text and "5.18" in c.text and "6.90" in c.text and "7.21" in c.text


def test_report_growths_fail_when_a_printed_rate_differs_after_one_decimal_or_a_report_is_missing():
    name = "rents growth rates of the reports"
    c = run_rents(growths={**GROWTHS, 2025: {"new": 7.0, "old": 7.2}}, detail=True)[name]  # read 6.90 %
    assert c.status == FAIL and "7.0" in c.text and "6.90" in c.text
    assert run_rents(growths={2021: GROWTHS[2021]})[name] == FAIL  # a missing report is no proof


def test_survey_dates_hold_and_the_text_names_each_year_with_the_date_read_and_the_date_shown():
    c = run_rents(detail=True)["rents survey dates"]
    assert c.status == OK
    for year, shown in SURVEY_DATES.items():
        assert str(year) in c.text and f"„{shown}“" in c.text
    assert "2017-06" in c.text and "2021-07" in c.text and "125.00" in c.text


@pytest.mark.parametrize("year, month", [(2017, (2017, 7)), (2021, (2021, 6)), (2023, (2022, 7)), (2025, (2025, 8))])
def test_survey_dates_fail_when_a_date_read_differs_from_the_tooltips(year, month):
    # the VPI of the month read is the one of the table, so only the date differs from SURVEY_DATES
    read = {**SURVEYS, year: {**SURVEYS[year], "month": month}}
    seen = {**VPI, month: VPI[(year, MONTHS[year])]}
    c = run_rents(read_surveys=read, read_vpi=seen, detail=True)["rents survey dates"]
    assert c.status == FAIL and f"„{SURVEY_DATES[year]}“" in c.text and f"{month[0]}-{month[1]:02d}" in c.text


def test_survey_dates_fail_when_a_survey_year_is_missing_or_unknown():
    name = "rents survey dates"
    assert run_rents(read_surveys={k: v for k, v in SURVEYS.items() if k != 2021})[name] == FAIL
    assert run_rents(read_surveys={**SURVEYS, 2019: {**SURVEYS[2021], "month": (2019, 7)}})[name] == FAIL


def test_survey_dates_fail_when_the_table_takes_the_prices_of_other_months_than_the_survey_months():
    # the step fed the July of 2017 (97.6) instead of June (97.2): the 2025 index is 124.49, not 125.00
    c = run_rents(months={}, detail=True)["rents survey dates"]
    assert c.status == FAIL and "124.49" in c.text and "125.00" in c.text
    # the VPI of July 2021 read differs from the one the table used: index 107.10 against 106.07
    c = run_rents(read_vpi={**VPI, (2021, 7): 104.1}, detail=True)["rents survey dates"]
    assert c.status == FAIL and "107.10" in c.text and "106.07" in c.text
    # a survey month without a VPI value is no proof
    assert run_rents(read_vpi={k: v for k, v in VPI.items() if k != (2023, 7)})["rents survey dates"] == FAIL


def test_shown_month_reads_both_forms_of_the_tooltips():
    assert shown_month("1.7.2021") == (2021, 7) and shown_month("Juni 2017") == (2017, 6)
    assert [shown_month(s) for s in SURVEY_DATES.values()] == [(2017, 6), (2021, 7), (2023, 7), (2025, 7)]
    for text in ("Junius 2017", "1.13.2021", "Mitte 2017", "2021", "1.7.21"):
        assert shown_month(text) is None, text


def test_uncertainty_fails_when_the_info_misses_a_base_effect_or_it_differs_from_the_data():
    name = "rents uncertainty"
    info = RENTS_TEXTS["info"]
    for old, new in (("25.679", ""), ("4.378", ""), ("25.679", "25.680"), ("4.378", "4.380")):
        texts = {**RENTS_TEXTS, "info": {**info, "uncertainty": info["uncertainty"].replace(old, new)}}
        assert run_rents(texts=texts)[name] == FAIL, (old, new)
    c = run_rents(bridge={**BRIDGE, "population": {2022: 773000}}, detail=True)[name]  # base effect −25,611
    assert c.status == FAIL and "25.611" in c.text
    c = run_rents(bridge={**BRIDGE, "stock": {2022: 408600}}, detail=True)[name]  # base effect −4,373
    assert c.status == FAIL and "4.373" in c.text
    c = run_rents(detail=True)[name]
    assert c.status == OK and "25.679" in c.text and "4.378" in c.text and "773.068" in c.text


def test_uncertainty_fails_when_a_growth_in_the_info_is_wrong_or_missing():
    # docs/data-rules.md, Uncertainty: the ⓘ names both calculations; chained 7,8 % and 5,3 %, published 6,6 % and 1,8 %
    name = "rents uncertainty"
    info = RENTS_TEXTS["info"]
    for old, new in (("7,8 %", "7,9 %"), ("5,3 %", "5,4 %"), ("6,6 %", "6,7 %"), ("1,8 %", "1,9 %"),
                     ("7,8 %", "17,8 %"), ("5,3 %", "")):
        texts = {**RENTS_TEXTS, "info": {**info, "uncertainty": info["uncertainty"].replace(old, new)}}
        assert run_rents(texts=texts)[name] == FAIL, (old, new)
    swapped = info["uncertainty"].replace("7,8 %", "x").replace("5,3 %", "7,8 %").replace("x", "5,3 %")
    assert run_rents(texts={**RENTS_TEXTS, "info": {**info, "uncertainty": swapped}})[name] == FAIL


def test_uncertainty_fails_when_the_growths_of_the_data_differ_from_the_info():
    name = "rents uncertainty"
    c = run_rents(stock={**STOCK, 2025: 416000}, detail=True)[name]  # dwellings published 6.80 %, chained 7.96 %
    assert c.status == FAIL and "6,8 %" in c.text and "8,0 %" in c.text
    c = run_rents(detail=True)[name]
    assert c.status == OK
    for named in ("7,8 %", "5,3 %", "6,6 %", "1,8 %"):
        assert named in c.text
