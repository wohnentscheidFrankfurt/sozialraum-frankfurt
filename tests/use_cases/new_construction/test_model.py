import re

import pytest

from pipeline.use_cases.new_construction.catalog import RENT_AXES, RENTS_TEXTS as RENTS_BY_LANGUAGE
from pipeline.use_cases.new_construction.catalog import T as PACKAGE_TEXTS
from pipeline.use_cases.new_construction.catalog import TEXTS as TEXTS_BY_LANGUAGE
from pipeline.use_cases.new_construction.model import (add_report_year, facts, rents_facts, rents_table, rents_view,
                                                       series, stock_facts, stock_series, up_to_last_year,
                                                       up_to_year, view, year_prices, year_wages)

TEXTS, RENTS_TEXTS, LANG = TEXTS_BY_LANGUAGE["de"], RENTS_BY_LANGUAGE["de"], PACKAGE_TEXTS["de"]

NEW_RES = {2011: 1905, 2012: 2144, 2013: 2768, 2014: 3556, 2015: 4076, 2016: 3472, 2017: 4047, 2018: 3244,
           2019: 3941, 2020: 3371, 2021: 3012, 2022: 2498, 2023: 2842, 2024: 3463, 2025: 3463}
NEW_NONRES = {2011: 20, 2012: 68, 2013: 17, 2014: 9, 2015: 1, 2016: 46, 2017: 269, 2018: 7, 2019: 15, 2020: 330,
              2021: 280, 2022: 188, 2023: 286, 2024: 17, 2025: 18}
ALL = {2011: 2138, 2012: 2682, 2013: 3156, 2014: 4418, 2015: 4325, 2016: 4273, 2017: 5122, 2018: 3761, 2019: 4641,
       2020: 4675, 2021: 3914, 2022: 2951, 2023: 3661, 2024: 4203, 2025: 3772}
SUBSIDISED = {2011: (83, 82), 2012: (90, 109), 2013: (56, 52), 2014: (307, 96), 2015: (431, 67), 2016: (226, 64),
              2017: (68, 52), 2018: (52, 318), 2019: (111, 298), 2020: (53, 120), 2021: (131, 210),
              2022: (160, 88), 2023: (182, 108), 2024: (131, 117), 2025: (343, 346)}


def table():
    return series(NEW_RES, NEW_NONRES, ALL, SUBSIDISED, 2011, 2025, 2023)


def test_series_splits_all_dwellings_into_new_construction_and_conversions():
    t = table().set_index("year")
    assert list(t.index) == list(range(2011, 2026))
    assert list(t.columns) == ["all", "new_res", "new_nonres", "new", "conversions", "fw1", "fw2", "subsidised",
                               "share", "provisional"]
    assert t["all"].sum() == 57692 and t["new"].sum() == 49373 and t["conversions"].sum() == 8319
    assert t["subsidised"].sum() == 4551
    assert t.loc[2025, "subsidised"] == 689 and round(t.loc[2025, "share"], 3) == 0.198
    assert t.loc[2017, "subsidised"] == 120 and t.loc[2017, "conversions"] == 806
    assert t.loc[2011, "new"] == 1925 and t.loc[2025, "new"] == 3481
    assert list(t[t["provisional"]].index) == [2023, 2024, 2025]


def test_series_keeps_a_negative_balance_for_the_check():
    t = series(NEW_RES, NEW_NONRES, {**ALL, 2016: 3400}, SUBSIDISED, 2011, 2025, 2023).set_index("year")
    assert t.loc[2016, "conversions"] == -118


@pytest.mark.parametrize("name", ["new residential", "new non-residential", "all dwellings", "subsidised"])
def test_series_stops_on_a_missing_year_and_names_year_and_input(name):
    inputs = {"new residential": NEW_RES, "new non-residential": NEW_NONRES, "all dwellings": ALL,
              "subsidised": SUBSIDISED}
    inputs[name] = {k: v for k, v in inputs[name].items() if k != 2016}
    with pytest.raises(ValueError, match=f"2016.*{name}|{name}.*2016"):
        series(inputs["new residential"], inputs["new non-residential"], inputs["all dwellings"],
               inputs["subsidised"], 2011, 2025, 2023)


def test_facts():
    f = facts(table(), 10)
    assert f["last_year"] == 2025 and round(f["share_last"], 3) == 0.198
    assert f["max_share_year"] == 2015 and round(f["max_share_before"], 4) == 0.1221
    assert (f["mean"], f["first_year"]) == (4097.3, 2016)


def test_view_formats_every_number_in_german():
    v = view(table(), {"title": "T", "lead": "L", "key": {}, "info": {}, "source": "S", "color": "#d40000",
                       "link": "l", "provisional_note": "<provisional>", "tip": TEXTS["tip"],
                       "calc_column": TEXTS["calc_column"], "calc_share": TEXTS["calc_share"]}, LANG)
    y = {r["year"]: r for r in v["years"]}
    assert set(y[2025]) == {"year", "all", "new", "conversions", "subsidised", "provisional", "all_text",
                            "share_text", "tip"}
    assert (y[2025]["all"], y[2025]["new"], y[2025]["conversions"]) == (3772, 3481, 291)
    assert y[2025]["all_text"] == "3.772" and y[2025]["share_text"] == "19,8 %"
    # the tooltip: year, all, new, conversions, subsidised and the share, in any order; a provisional year adds the note
    numbers = lambda tip: sorted(re.findall(r"\d+(?:[.,]\d+)*(?: %)?", tip))
    assert numbers(y[2025]["tip"]) == sorted(["2025", "3.772", "3.481", "291", "689", "19,8 %"])
    assert numbers(y[2011]["tip"]) == sorted(["2011", "2.138", "1.925", "213", "165", "8,6 %"])
    assert y[2025]["tip"].endswith(". <provisional>") and "<provisional>" not in y[2011]["tip"]
    assert v["highlight"] == 2025 and v["max"] == 5122
    assert set(v) == {"title", "lead", "key", "info", "source", "color", "link", "highlight", "max", "years"}
    assert v["link"] == "l"


def rows_of(example):
    return [(r["op"], r["number"], r["decimals"], r["unit"], r["total"], r["estimate"]) for r in example["rows"]]


def test_view_info_has_the_sums_of_the_column_and_the_share_of_the_last_year():
    """docs/texts.md, Written sums: the column and the share of the year of the heading; counts, no estimate."""
    v = view(table(), TEXTS, LANG)
    assert {k: v["info"][k] for k in TEXTS["info"]} == TEXTS["info"]
    column, share = v["info"]["calc_examples"]
    assert column["label"] == TEXTS["calc_column"]["label"].format(year=2025)
    assert share["label"] == TEXTS["calc_share"]["label"].format(year=2025)
    assert rows_of(column) == [("", 3463, 0, "", False, False), ("+", 18, 0, "", False, False),
                               ("", 3481, 0, "", True, False), ("+", 291, 0, "", False, False),
                               ("", 3772, 0, "", True, False)]
    assert rows_of(share) == [("", 343, 0, "", False, False), ("+", 346, 0, "", False, False),
                              ("", 689, 0, "", True, False), ("÷", 3481, 0, "", False, False),
                              ("", 19.8, 1, "%", True, False)]
    texts = TEXTS["calc_column"], TEXTS["calc_share"]
    assert [r["text"] for r in column["rows"]] == [texts[0][k] for k in ("new_res", "new_nonres", "new", "conversions",
                                                                         "all")]
    # 2025 is provisional: the row of the subsidised dwellings says so
    assert [r["text"] for r in share["rows"]] == [texts[1][k] for k in ("fw1", "fw2", "subsidised_provisional", "new",
                                                                        "share")]


def test_view_sum_of_a_final_year_names_no_provisional():
    v = view(table()[table()["year"] <= 2022], TEXTS, LANG)
    assert v["info"]["calc_examples"][1]["rows"][2]["text"] == TEXTS["calc_share"]["subsidised"]


def test_report_year_is_added_for_the_last_year_only():
    assert add_report_year({2024: 3463}, 2025, 3500, 2025) == {2024: 3463, 2025: 3500}
    with pytest.raises(ValueError, match="2025"):
        add_report_year({2024: 3463}, 2024, 3463, 2025)  # the report is of the year before
    with pytest.raises(ValueError, match="2025"):
        add_report_year({2024: 3463, 2025: 3400}, 2025, 3500, 2025)  # the Regionaldatenbank has 2025 already


STOCK = {2011: 366541, 2012: 368933, 2013: 372039, 2014: 376431, 2015: 380510, 2016: 384609, 2017: 389524,
         2018: 393186, 2019: 397709, 2020: 402210, 2021: 406003, 2022: 404227, 2023: 407457, 2024: 411592,
         2025: 415359}  # HSL, Fortschreibung, 31.12.
POPULATION = {2011: 676533, 2012: 687775, 2013: 701350, 2014: 717624, 2015: 732688, 2016: 736414, 2017: 746878,
              2018: 753056, 2019: 763380, 2020: 764104, 2021: 759224, 2022: 747389, 2023: 749596, 2024: 756021,
              2025: 760656}  # HSL, Fortschreibung, 31.12., Hauptwohnsitz


def stock_table(stock=STOCK, population=POPULATION):
    return stock_series(stock, population, ALL, 2011, 2025, (2022,))


def test_stock_series_derives_the_outflow_without_the_first_year_and_the_break():
    t = stock_table().set_index("year")
    assert list(t.index) == list(range(2011, 2026))
    assert list(t.columns) == ["stock", "population", "completed", "change", "outflow"]
    assert t["change"].isna().tolist() == [y in (2011, 2022) for y in range(2011, 2026)]
    assert t["outflow"].isna().tolist() == [y in (2011, 2022) for y in range(2011, 2026)]
    assert (t.loc[2012, "change"], t.loc[2012, "outflow"]) == (2392, 290)
    assert (t.loc[2023, "change"], t.loc[2023, "outflow"]) == (3230, 431)
    assert (t["outflow"].min(), t["outflow"].max(), t["outflow"].sum()) == (5, 431, 2009)
    assert (t.loc[2015, "population"], t.loc[2025, "population"]) == (732688, 760656)


def test_stock_series_stops_on_a_missing_year_and_names_it():
    with pytest.raises(ValueError, match="^stock: no value for 2016$"):
        stock_table({k: v for k, v in STOCK.items() if k != 2016})
    with pytest.raises(ValueError, match="^population: no value for 2016$"):
        stock_table(population={k: v for k, v in POPULATION.items() if k != 2016})
    with pytest.raises(ValueError, match="^all dwellings: no value for 2016$"):
        stock_series(STOCK, POPULATION, {k: v for k, v in ALL.items() if k != 2016}, 2011, 2025, (2022,))


def test_up_to_last_year_needs_the_last_year_and_nothing_after_it():
    assert up_to_last_year({2024: 1, 2025: 2}, 2025, "population") == {2024: 1, 2025: 2}
    with pytest.raises(ValueError, match="population.*2025"):
        up_to_last_year({2024: 1}, 2025, "population")
    with pytest.raises(ValueError, match="population.*2026"):
        up_to_last_year({2025: 2, 2026: 3}, 2025, "population")


# 31.12.2022 on the Zensus 2011: HSL, F I 1 j/22, table 4, and A I 2 of the 2nd half of 2022
BRIDGE = {"stock": {2022: 408605}, "population": {2022: 773068}}


def test_stock_facts_give_both_growths_of_both_series():
    f = stock_facts(stock_table(), 2015, (2022,), BRIDGE)
    assert (f["last_year"], f["from_year"], f["break_year"]) == (2025, 2015, 2022)
    # chained: 408,605 ÷ 380,510 × 415,359 ÷ 404,227 − 1 and 773,068 ÷ 732,688 × 760,656 ÷ 747,389 − 1
    assert round(100 * f["stock_growth"], 2) == 9.16 and round(100 * f["stock_growth_chained"], 2) == 10.34
    assert round(100 * f["population_growth"], 2) == 3.82 and round(100 * f["population_growth_chained"], 2) == 7.38
    assert (f["stock_bridge"], f["stock_base_effect"]) == (408605, -4378)
    assert (f["population_bridge"], f["population_base_effect"]) == (773068, -25679)
    assert round(f["mean_outflow"], 2) == 154.54  # 2,009 over 13 years


def test_stock_facts_give_the_outflow_of_the_last_year_and_the_mean_of_the_others():
    f = stock_facts(stock_table(), 2015, (2022,), BRIDGE)
    assert f["outflow_last"] == 5 and f["mean_outflow_other"] == 167.0  # (2,009 − 5) ÷ 12


def test_stock_facts_stop_without_a_value_of_a_break_year_on_the_old_base():
    with pytest.raises(ValueError, match="stock.*old base.*2022"):
        stock_facts(stock_table(), 2015, (2022,), {**BRIDGE, "stock": {2021: 408605}})
    with pytest.raises(ValueError, match="population.*old base.*2022"):
        stock_facts(stock_table(), 2015, (2022,), {**BRIDGE, "population": {}})


# The rents of the Mietspiegel, the VPI Hessen (HSL, M I 2 j/25, table 3; only the months the chart uses and July 2017
# to tell the survey month from the default month) and the Nominallohnindex Hessen (HSL, quarters 2 and 3)
SURVEYS = {2017: {"new": 10.21, "old": 8.69, "month": (2017, 6)}, 2021: {"new": 11.56, "old": 9.14, "month": (2021, 7)},
           2023: {"new": 13.05, "old": 9.43, "month": (2023, 7)},
           2025: {"new": 13.95, "old": 10.11, "month": (2025, 7)}}
VPI = {(2017, 6): 97.2, (2017, 7): 97.6, (2018, 7): 99.2, (2019, 7): 100.6, (2020, 7): 99.6, (2021, 7): 103.1,
       (2022, 7): 109.9, (2023, 7): 116.6, (2024, 7): 118.7, (2025, 7): 121.5}
WAGES = {(2017, 2): 93.6, (2017, 3): 84.0, (2018, 2): 96.7, (2018, 3): 87.2, (2019, 2): 98.7, (2019, 3): 90.1,
         (2020, 2): 95.1, (2020, 3): 88.9, (2021, 2): 98.4, (2021, 3): 92.5, (2022, 2): 101.5, (2022, 3): 94.6,
         (2023, 2): 108.2, (2023, 3): 100.1, (2024, 2): 114.5, (2024, 3): 106.5, (2025, 2): 120.1, (2025, 3): 110.9}
# Melderegister, persons ÷ households, row insgesamt
HOUSEHOLDS = {2017: 768537 / 416615, 2018: 773824 / 413365, 2019: 765315 / 408355, 2020: 768589 / 412046,
              2021: 761958 / 409444, 2022: 775684 / 417632, 2023: 778178 / 419582, 2024: 782441 / 422398,
              2025: 786325 / 426293}


def year_price_table():
    return year_prices(VPI, {y: s["month"][1] for y, s in SURVEYS.items()}, 2017, 2025, 7)


def rents(surveys=SURVEYS):
    return rents_table(stock_table(), surveys, year_price_table(), year_wages(WAGES, (2, 3), 2017, 2025), 2017, 2025)


def rents_chart(table=None, axes=RENT_AXES):
    t = rents() if table is None else table
    sf = stock_facts(stock_table(), 2017, (2022,), BRIDGE)
    return rents_view(t, rents_facts(t, sf, HOUSEHOLDS, 2017, 2025), RENTS_TEXTS, BRIDGE, (2022,), axes, LANG)


def test_year_prices_take_the_survey_month():
    prices = year_price_table()
    assert list(prices) == list(range(2017, 2026))
    assert (prices[2017], prices[2018], prices[2025]) == (97.2, 99.2, 121.5)  # June 2017, not July (97.6)


def test_year_prices_stop_and_name_the_missing_month():
    with pytest.raises(ValueError, match="prices.*2019.*month 7"):
        year_prices({k: v for k, v in VPI.items() if k != (2019, 7)}, {2017: 6}, 2017, 2025, 7)


def test_year_wages_mean_of_quarters_2_and_3():
    wages = year_wages(WAGES, (2, 3), 2017, 2025)
    assert list(wages) == list(range(2017, 2026))
    assert (round(wages[2017], 2), round(wages[2018], 2), round(wages[2025], 2)) == (88.8, 91.95, 115.5)


def test_year_wages_stop_and_name_the_missing_quarter():
    with pytest.raises(ValueError, match="wages.*2025.*quarter 3"):
        year_wages({k: v for k, v in WAGES.items() if k != (2025, 3)}, (2, 3), 2017, 2025)


def test_rents_table_index_2025():
    t = rents().set_index("year")
    assert list(t.index) == list(range(2017, 2026))
    assert list(t.columns) == ["stock", "population", "stock_index", "population_index", "prices_index", "wages_index",
                               "wages_real", "new", "old", "new_index", "old_index", "new_real", "old_real"]
    got = {c: round(t.loc[2025, c], 1) for c in ("new_index", "wages_index", "prices_index", "old_index", "stock_index",
                                                 "population_index", "new_real", "wages_real", "old_real")}
    assert got == {"new_index": 136.6, "wages_index": 130.1, "prices_index": 125.0, "old_index": 116.3,
                   "stock_index": 106.6, "population_index": 101.8, "new_real": 109.3, "wages_real": 104.1,
                   "old_real": 93.1}
    assert (t.loc[2025, "stock"], t.loc[2025, "population"], t.loc[2025, "new"]) == (415359, 760656, 13.95)
    # chart 2 per survey year: new 100; 106,7; 106,5; 109,3. Older 100; 99,2; 90,5; 93,1. New 2023 is
    # 100 × (13,05 ÷ 116,6) ÷ (10,21 ÷ 97,2) = 106.5498, so 106,5 (the approved mockup shows 106,5 too).
    assert [round(t.loc[y, "new_real"], 1) for y in (2017, 2021, 2023, 2025)] == [100.0, 106.7, 106.5, 109.3]
    assert [round(t.loc[y, "old_real"], 1) for y in (2017, 2021, 2023, 2025)] == [100.0, 99.2, 90.5, 93.1]
    assert {c: t.loc[2017, c] for c in ("stock_index", "population_index", "prices_index", "wages_index")} == {
        "stock_index": 100, "population_index": 100, "prices_index": 100, "wages_index": 100}


def test_rents_table_has_rents_only_in_survey_years():
    t = rents().set_index("year")
    rent_columns = ["new", "old", "new_index", "old_index", "new_real", "old_real"]
    assert [y for y in t.index if t.loc[y, rent_columns].notna().all()] == [2017, 2021, 2023, 2025]
    assert t.loc[2018, rent_columns].isna().all()


def test_rents_table_stops_without_a_survey_in_the_first_or_last_year():
    with pytest.raises(ValueError, match="rents.*no survey.*2017"):
        rents({k: v for k, v in SURVEYS.items() if k != 2017})
    with pytest.raises(ValueError, match="rents.*no survey.*2025"):
        rents({k: v for k, v in SURVEYS.items() if k != 2025})


def test_rents_table_stops_on_a_missing_year_and_names_the_input():
    prices, wages = year_price_table(), year_wages(WAGES, (2, 3), 2017, 2025)
    with pytest.raises(ValueError, match="^prices: no value for 2019$"):
        rents_table(stock_table(), SURVEYS, {k: v for k, v in prices.items() if k != 2019}, wages, 2017, 2025)
    with pytest.raises(ValueError, match="^wages: no value for 2019$"):
        rents_table(stock_table(), SURVEYS, prices, {k: v for k, v in wages.items() if k != 2019}, 2017, 2025)
    with pytest.raises(ValueError, match="^stock: no value for 2019$"):
        rents_table(stock_table().query("year != 2019"), SURVEYS, prices, wages, 2017, 2025)


def test_rents_facts_growths():
    t = rents()
    f = rents_facts(t, stock_facts(stock_table(), 2017, (2022,), BRIDGE), HOUSEHOLDS, 2017, 2025)
    pct = {k: round(100 * v, 2) for k, v in f.items() if k.endswith("growth") or "growth_" in k}
    assert pct["stock_growth_chained"] == 7.79 and pct["population_growth_chained"] == 5.34
    assert pct["stock_growth"] == 6.63 and pct["population_growth"] == 1.84  # published: 415,359 ÷ 389,524 − 1
    assert pct["new_growth"] == 36.63 and pct["old_growth"] == 16.34  # 13.95 ÷ 10.21 − 1 and 10.11 ÷ 8.69 − 1
    assert pct["new_growth_real"] == 9.30 and pct["old_growth_real"] == -6.93  # 1.3663 ÷ 1.25 − 1 and 1.1634 ÷ 1.25 − 1
    assert pct["prices_growth"] == 25.0 and pct["wages_growth"] == 30.07 and pct["wages_growth_real"] == 4.05
    # the lowest and the highest size of all years 2017 to 2025: 1.8446 (2025) and 1.8741 (2019)
    assert (f["household_low"], f["household_high"]) == (HOUSEHOLDS[2025], HOUSEHOLDS[2019])
    assert (round(f["household_low"], 4), round(f["household_high"], 4)) == (1.8446, 1.8741)
    assert not {"household_first", "household_last", "household_change"} & set(f)


def test_rents_facts_stop_without_the_households_of_a_year():
    sf = stock_facts(stock_table(), 2017, (2022,), BRIDGE)
    for year in (2017, 2019, 2025):
        with pytest.raises(ValueError, match=f"^households: no value for {year}$"):
            rents_facts(rents(), sf, {k: v for k, v in HOUSEHOLDS.items() if k != year}, 2017, 2025)


def test_rents_facts_give_the_base_effects_of_the_break_year_for_the_info():
    f = rents_facts(rents(), stock_facts(stock_table(), 2017, (2022,), BRIDGE), HOUSEHOLDS, 2017, 2025)
    assert f["break_year"] == 2022
    assert (f["stock_bridge"], f["stock_base_effect"]) == (408605, -4378)  # 404,227 − 408,605
    assert (f["population_bridge"], f["population_base_effect"]) == (773068, -25679)  # 747,389 − 773,068


def test_rents_facts_stop_when_the_stock_facts_start_in_another_year():
    with pytest.raises(ValueError, match="2015.*2017"):
        rents_facts(rents(), stock_facts(stock_table(), 2015, (2022,), BRIDGE), HOUSEHOLDS, 2017, 2025)
    with pytest.raises(ValueError, match="^households: no value for 2018$"):  # the first year without a value
        rents_facts(rents(), stock_facts(stock_table(), 2017, (2022,), BRIDGE), {2017: 1.84}, 2017, 2025)


def test_the_rents_block_ends_at_its_end_year_when_the_stock_runs_one_year_longer():
    # LAST_YEAR 2026 without a Mietspiegel survey (RENT_TO stays 2025): the stock table has 2026, the block ends at 2025
    longer = stock_series({**STOCK, 2026: 419000}, {**POPULATION, 2026: 764000}, {**ALL, 2026: 3900}, 2011, 2026, (2022,))
    assert int(longer["year"].max()) == 2026
    stocks = up_to_year(longer, 2025)  # the step gives the rents block the stock up to RENT_TO
    assert list(stocks["year"]) == list(range(2011, 2026))
    t = rents_table(stocks, SURVEYS, year_price_table(), year_wages(WAGES, (2, 3), 2017, 2025), 2017, 2025)
    sf = stock_facts(stocks, 2017, (2022,), BRIDGE)
    f = rents_facts(t, sf, HOUSEHOLDS, 2017, 2025)
    assert (int(t["year"].min()), int(t["year"].max())) == (2017, 2025) and sf["last_year"] == 2025
    assert f == rents_facts(rents(), stock_facts(stock_table(), 2017, (2022,), BRIDGE), HOUSEHOLDS, 2017, 2025)
    assert [c["years"][-1] for c in rents_view(t, f, RENTS_TEXTS, BRIDGE, (2022,), RENT_AXES, LANG)["charts"]] == [2025, 2025]
    # the stock facts of the full table keep the last year of the stock (stock_checks), the block refuses them
    full = stock_facts(longer, 2017, (2022,), BRIDGE)
    assert (full["last_year"], full["outflow_last"]) == (2026, 259)  # 3,900 completed − 3,641 change
    with pytest.raises(ValueError, match="2017 to 2026.*2017 to 2025"):
        rents_facts(t, full, HOUSEHOLDS, 2017, 2025)


def test_up_to_year_keeps_the_rows_up_to_the_year_and_the_table_unchanged():
    t = stock_table()
    assert list(up_to_year(t, 2020)["year"]) == list(range(2011, 2021))
    assert list(up_to_year(t, 2025)["year"]) == list(range(2011, 2026)) and len(t) == 15


def tip_of(chart, year):
    return next(t for t in chart["tips"] if t["year"] == year)


T = RENTS_TEXTS  # the tooltips take their labels and notes from the catalog


def test_rents_view_tip_of_2023():
    nominal, real = rents_chart()["charts"]
    tip = tip_of(nominal, 2023)
    assert tip["head"] == T["tip_head"].format(year=2023, base=2017)
    assert tip["rows"] == [["104,6", f"{T['tip_dwellings']} (407.457)", "dwellings"],
                           ["100,4", f"{T['tip_population']} (749.596)", "population"],
                           ["127,8", f"{T['tip_new']} (13,05 €, 1.7.2023)", "new"],
                           ["108,5", f"{T['tip_old']} (9,43 €)", "old"], ["120,0", T["tip_prices"], "prices"],
                           ["117,3", T["tip_wages"], "wages"]]
    assert tip["note"] == T["tip_survey"]
    tip = tip_of(real, 2023)  # the same without the stocks; the wage row is the one without inflation
    assert tip["rows"] == [["106,5", f"{T['tip_new']} (13,05 €, 1.7.2023)", "new"],
                           ["90,5", f"{T['tip_old']} (9,43 €)", "old"], ["100,0", T["tip_prices"], "prices"],
                           ["97,8", T["tip_wages_real"], "wages"]]
    assert tip["note"] == T["tip_survey"]
    assert tip["text"] == (f"{T['tip_head'].format(year=2023, base=2017)}: 106,5 {T['tip_new']} (13,05 €, 1.7.2023); "
                           f"90,5 {T['tip_old']} (9,43 €); 100,0 {T['tip_prices']}; 97,8 {T['tip_wages_real']}. "
                           f"{T['tip_survey']}")


def test_rents_view_tips_of_the_first_year_a_year_without_survey_and_the_break_year():
    nominal, real = rents_chart()["charts"]
    assert [t["year"] for t in nominal["tips"]] == list(range(2017, 2026)) == nominal["years"]
    assert tip_of(nominal, 2017)["rows"][2:4] == [["100,0", f"{T['tip_new']} (10,21 €, Juni 2017)", "new"],
                                                  ["100,0", f"{T['tip_old']} (8,69 €)", "old"]]
    tip = tip_of(nominal, 2018)  # no rent rows, a note for the missing survey
    assert tip["rows"] == [["100,9", f"{T['tip_dwellings']} (393.186)", "dwellings"],
                           ["100,8", f"{T['tip_population']} (753.056)", "population"],
                           ["102,1", T["tip_prices"], "prices"], ["103,5", T["tip_wages"], "wages"]]
    assert tip["note"] == T["tip_no_survey"]
    # 2022: the values on the old base come first, then the note of the year
    assert tip_of(nominal, 2022)["note"] == (T["tip_old_base"].format(dwellings="104,9", population="103,5") + " "
                                             + T["tip_no_survey"])
    assert tip_of(real, 2022)["note"] == T["tip_no_survey"]


def test_rents_view_break_only_in_chart_1():
    nominal, real = rents_chart()["charts"]
    assert nominal["break"] == {"year": 2022, "note": T["break_note"]}
    assert nominal["old_base"] == {
        "year": 2022,
        "dwellings": {"value": 408605 / 389524 * 100,
                      "tip": f"31.12.2022 {T['old_base']}: 104,9 {T['tip_dwellings']} (408.605)."},
        "population": {"value": 773068 / 746878 * 100,
                       "tip": f"31.12.2022 {T['old_base']}: 103,5 {T['tip_population']} (773.068)."}}
    assert "break" not in real and "old_base" not in real


def test_rents_view_end_labels_one_decimal():
    nominal, real = rents_chart()["charts"]
    ends = lambda chart: {s["id"]: s["end_value_text"] for s in chart["series"]}
    assert ends(nominal) == {"prices": "125,0", "wages": "130,1", "dwellings": "106,6", "population": "101,8",
                             "new": "136,6", "old": "116,3"}
    assert ends(real) == {"prices": "100,0", "wages": "104,1", "new": "109,3", "old": "93,1"}
    assert all(s["end_name"] == T["names"][s["id"]] for chart in (nominal, real) for s in chart["series"])
    # the browser places the labels in the order of height, highest first
    assert nominal["end_order"] == ["new", "wages", "prices", "old", "dwellings", "population"]
    assert real["end_order"] == ["new", "wages", "prices", "old"]


def test_rents_view_info_has_the_sum_of_the_new_contracts_of_the_last_year():
    """The index and the value without inflation of the new contracts: the end values of their two lines."""
    t = rents().set_index("year")
    (example,) = rents_chart()["info"]["calc_examples"]
    texts = RENTS_TEXTS["calc_rent"]
    assert example["label"] == texts["label"].format(year=2025)
    assert rows_of(example) == [("", t.loc[2025, "new"], 2, "€", False, False), ("÷", t.loc[2017, "new"], 2, "€", False, False),
                                ("×", 100, 0, "", False, False), ("", 136.6, 1, "", True, False),
                                ("÷", round(t.loc[2025, "prices_index"], 1), 1, "", False, False),
                                ("×", 100, 0, "", False, False), ("", 109.3, 1, "", True, False)]
    assert [r["text"] for r in example["rows"]] == [
        texts["rent"].format(year=2025), texts["base"].format(first=2017), "", texts["nominal"].format(first=2017),
        texts["prices"].format(year=2025, first=2017), "", texts["real"]]


def test_rents_view_gives_texts_axes_keys_and_series_in_drawing_order():
    v = rents_chart()
    assert list(v) == ["title", "lead", "info", "source", "link", "charts"]
    assert (v["title"], v["lead"], v["source"], v["link"]) == tuple(
        RENTS_TEXTS[k] for k in ("title", "lead", "source", "link"))
    assert {k: v["info"][k] for k in RENTS_TEXTS["info"]} == RENTS_TEXTS["info"]
    nominal, real = v["charts"]
    assert (nominal["id"], real["id"]) == ("nominal", "real")
    assert (nominal["title"], nominal["explain"]) == (RENTS_TEXTS["charts"]["nominal"]["title"],
                                                      RENTS_TEXTS["charts"]["nominal"]["explain"])
    assert nominal["axis"] == {"min": 95, "max": 140, "ticks": [100, 110, 120, 130, 140],
                               "tick_texts": ["100", "110", "120", "130", "140"]}
    assert real["axis"] == {"min": 86, "max": 112, "ticks": [90, 95, 100, 105, 110],
                            "tick_texts": ["90", "95", "100", "105", "110"]}
    assert nominal["years"] == real["years"] == list(range(2017, 2026))
    # the two references first, under everything, then the data lines
    assert [s["id"] for s in nominal["series"]] == ["prices", "wages", "dwellings", "population", "new", "old"]
    assert [s["id"] for s in real["series"]] == ["prices", "wages", "new", "old"]
    # the key follows the line ends from top to bottom (end_order), the old base comes last
    assert [(k["id"], k["kind"], k["colour"], k["width"], k["dash"]) for k in nominal["key"]] == [
        ("new", "data", "#8c0000", 3, None),
        ("wages", "reference", "#6b6b6b", 1.5, "5 3"),
        ("prices", "reference", "#8c8c8c", 1.5, None),
        ("old", "data", "#f07067", 2.5, None),
        ("dwellings", "data", "#d40000", 2.5, None),
        ("population", "data", "#1a1a1a", 2, None),
        ("old_base", "old_base", "#6b6b6b", 2, "1 4")]
    assert [k["id"] for k in nominal["key"]] == nominal["end_order"] + ["old_base"]
    assert [k["id"] for k in real["key"]] == ["new", "wages", "prices", "old"] == real["end_order"]
    # each chart names its entries with its own key of the catalog: without inflation the wages say so
    for chart in (nominal, real):
        assert all(k["name"] == RENTS_TEXTS["charts"][chart["id"]]["key"][k["id"]] for k in chart["key"])
    # a reference entry names the side of its edge and the band; no key entry carries an ink of its own
    for chart in (nominal, real):
        references = {k["id"]: k for k in chart["key"] if k["kind"] == "reference"}
        assert {sid: (k["edge"], k["band"]) for sid, k in references.items()} == {
            "wages": ("top", "#e6e6e6"), "prices": ("bottom", "#e6e6e6")}
        assert all("edge" not in k and "band" not in k for k in chart["key"] if k["kind"] != "reference")
        assert all("ink" not in k for k in chart["key"])


def test_rents_view_key_entries_say_whether_their_swatch_has_a_dot():
    nominal, real = rents_chart()["charts"]
    for chart in (nominal, real):
        series = {s["id"]: s for s in chart["series"]}
        data = [k for k in chart["key"] if k["kind"] == "data"]
        assert all(isinstance(k["dot"], bool) for k in data)
        assert all(k["dot"] == bool(series[k["id"]]["dots"]) for k in data)  # the key follows the chart
        assert all("dot" not in k for k in chart["key"] if k["kind"] != "data")
    assert {k["id"]: k["dot"] for k in nominal["key"] if k["kind"] == "data"} == {
        "new": True, "old": True, "dwellings": False, "population": False}
    assert {k["id"]: k["dot"] for k in real["key"] if k["kind"] == "data"} == {"new": True, "old": True}


def test_rents_view_gives_the_band_and_the_survey_years_and_the_note_of_the_old_base():
    nominal, real = rents_chart()["charts"]
    for chart in (nominal, real):
        assert chart["band"] == {"between": ["wages", "prices"], "colour": "#e6e6e6"}
        assert chart["survey_years"] == [2017, 2021, 2023, 2025]
    assert nominal["old_base_note"] == RENTS_TEXTS["old_base_note"] and "old_base_note" not in real


def test_rents_view_survey_years_come_from_the_table():
    surveys = {y: s for y, s in SURVEYS.items() if y != 2023}
    for chart in rents_chart(rents(surveys))["charts"]:
        assert chart["survey_years"] == [2017, 2021, 2025]


def test_rents_view_key_order_and_edges_hold_on_a_tie():
    t = rents()
    t.loc[t["year"] == 2025, "wages_index"] = t.loc[t["year"] == 2025, "prices_index"].iloc[0]  # prices = wages
    nominal = rents_chart(t)["charts"][0]
    # the drawing order (prices first) breaks the tie
    assert nominal["end_order"] == ["new", "prices", "wages", "old", "dwellings", "population"]
    assert [k["id"] for k in nominal["key"]] == nominal["end_order"] + ["old_base"]
    edges = {k["id"]: k["edge"] for k in nominal["key"] if k["kind"] == "reference"}
    assert edges == {"prices": "top", "wages": "bottom"}
    assert list(edges.values()).count("top") == 1


def test_rents_view_stops_when_a_band_series_lacks_a_year():
    t = rents()
    t.loc[t["year"] == 2020, "wages_index"] = float("nan")
    with pytest.raises(ValueError, match="nominal: wages 2020"):
        rents_chart(t)


def test_rents_view_series_carry_style_values_and_dots():
    nominal, real = rents_chart()["charts"]
    s = {x["id"]: x for x in nominal["series"]}
    style = lambda x: (x["kind"], x["colour"], x["ink"], x["width"], x["dash"])
    assert style(s["prices"]) == ("reference", "#8c8c8c", "#6b6b6b", 1.5, None)
    assert style(s["wages"]) == ("reference", "#6b6b6b", "#6b6b6b", 1.5, "5 3")
    assert style(s["new"]) == ("data", "#8c0000", "#1a1a1a", 3, None)
    assert style(s["old"]) == ("data", "#f07067", "#1a1a1a", 2.5, None)
    assert style(s["dwellings"]) == ("data", "#d40000", "#1a1a1a", 2.5, None)
    assert style(s["population"]) == ("data", "#1a1a1a", "#1a1a1a", 2, None)
    assert s["new"]["name"] == RENTS_TEXTS["charts"]["nominal"]["key"]["new"]
    assert s["prices"]["dots"] == s["wages"]["dots"] == []
    # a stock has no dot: its end (31.12.2025) is no survey day of the Mietspiegel, which the dots stand for
    assert s["dwellings"]["dots"] == s["population"]["dots"] == []
    assert s["new"]["dots"] == s["old"]["dots"] == [2017, 2021, 2023, 2025]
    assert [None if v is None else round(v, 1) for v in s["new"]["values"]] == [
        100.0, None, None, None, 113.2, None, 127.8, None, 136.6]
    assert [round(v, 1) for v in s["dwellings"]["values"]] == [100.0, 100.9, 102.1, 103.3, 104.2, 103.8, 104.6, 105.7,
                                                                106.6]
    r = {x["id"]: x for x in real["series"]}
    assert r["prices"]["values"] == [100.0] * 9  # prices are the scale of the second chart
    assert [round(v, 1) for v in r["wages"]["values"]] == [100.0, 101.5, 102.7, 101.1, 101.3, 97.7, 97.8, 101.9, 104.1]


def test_rents_view_tip_rows_name_their_series_and_the_swatch_colour_is_that_of_the_series():
    # the rows follow the tooltip order, not the drawing order, and a year without survey has no rent rows: the browser
    # finds the colour of a row by its series id
    for chart in rents_chart()["charts"]:
        colours = {s["id"]: s["colour"] for s in chart["series"]}
        for tip in chart["tips"]:
            assert all(len(row) == 3 and row[2] in colours for row in tip["rows"])
            assert len({row[2] for row in tip["rows"]}) == len(tip["rows"])
        assert [row[2] for row in tip_of(chart, 2018)["rows"]] == [
            sid for sid in ("dwellings", "population", "prices", "wages") if sid in colours]
        assert {row[2]: colours[row[2]] for row in tip_of(chart, 2025)["rows"]}["new"] == "#8c0000"


def test_rents_view_aria_label_names_the_chart_and_holds_every_tip():
    nominal, real = rents_chart()["charts"]
    assert nominal["aria_label"].startswith(RENTS_TEXTS["charts"]["nominal"]["title"] + ". ")
    assert real["aria_label"].startswith(RENTS_TEXTS["charts"]["real"]["title"] + ". ")
    for chart in (nominal, real):
        assert all(t["text"] in chart["aria_label"] for t in chart["tips"])
    assert all(o["tip"] in nominal["aria_label"] for o in (nominal["old_base"]["dwellings"],
                                                         nominal["old_base"]["population"]))


def test_rents_view_stops_when_a_value_leaves_its_axis_and_names_series_and_year():
    axes = {**RENT_AXES, "nominal": {**RENT_AXES["nominal"], "max": 130}}
    with pytest.raises(ValueError, match="nominal.*wages.*2025"):
        rents_chart(axes=axes)
    axes = {**RENT_AXES, "real": {**RENT_AXES["real"], "min": 92}}
    with pytest.raises(ValueError, match="real.*old.*2023"):
        rents_chart(axes=axes)


def test_rents_view_stops_when_the_facts_do_not_match_the_table():
    t = rents()
    sf = stock_facts(stock_table(), 2017, (2022,), BRIDGE)
    facts_ = {**rents_facts(t, sf, HOUSEHOLDS, 2017, 2025), "stock_growth": 0.10}
    with pytest.raises(ValueError, match="stock.*growth"):
        rents_view(t, facts_, RENTS_TEXTS, BRIDGE, (2022,), RENT_AXES, LANG)
