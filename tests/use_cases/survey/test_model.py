import math

import numpy as np
import pandas as pd
import pytest

from pipeline.shared.core.stats import weighted_median
from pipeline.use_cases.survey.model import (
    BREAKDOWN_IDS, CITY_ROW, _bootstrap_medians, area_weight_shares, breakdown_half_widths, burden_ratios,
    example_household, income_breakdown, round_half_up, survey_by_district, survey_city, survey_table,
    tenant_medians)


def test_survey_table_shows_the_printed_classes():
    figures = {"LIF_ATTACHMENT": {"city": 62, "classes": {(51, 61): ("West",), (64, 70): ("Süd",)}}}
    t = survey_table(figures, ["West", "Süd"]).set_index("survey_area")
    assert t.loc["Süd", "LIF_ATTACHMENT"] == 70 and t.loc["Süd", "LIF_ATTACHMENT_LOWER"] == 64
    assert t.loc["city", "LIF_ATTACHMENT"] == 62 and pd.isna(t.loc["city", "LIF_ATTACHMENT_LOWER"])


def test_survey_table_stops_on_a_missing_or_unknown_area():
    with pytest.raises(ValueError, match="Nord"):
        survey_table({"X": {"city": 1, "classes": {(1, 2): ("West",)}}}, ["West", "Nord"])
    with pytest.raises(ValueError, match="Westen"):
        survey_table({"X": {"city": 1, "classes": {(1, 2): ("West", "Westen")}}}, ["West"])


def test_survey_by_district_gives_each_district_the_class_of_its_area():
    survey = pd.DataFrame({"survey_area": ["Süd", "city"], "LIF_ATTACHMENT": [70, 62], "LIF_ATTACHMENT_LOWER": [64, None]})
    areas = pd.DataFrame({"id": ["10", "20"], "survey_area": ["Süd", "Süd"]})
    out = survey_by_district(survey, areas)
    assert out.to_dict("records") == [{"id": "10", "LIF_ATTACHMENT": 70, "LIF_ATTACHMENT_LOWER": 64.0},
                                      {"id": "20", "LIF_ATTACHMENT": 70, "LIF_ATTACHMENT_LOWER": 64.0}]


def test_survey_city_adds_the_breakdown_as_computed():
    """The printed city values are published; the income groups are the map's own count. city_rows would drop the
    ids ending in _LOW and _HIGH (ends of a range), so these rows must still stand."""
    survey = pd.DataFrame({"survey_area": ["Süd", "city"], "LIF_RENT_BURDEN_RATIO": [29, 29],
                           "LIF_ATTACHMENT": [70, 62], "LIF_RENT_BURDEN_INCOME_LOW": [60.0, 55.0],
                           "LIF_RENT_BURDEN_INCOME_MID": [40.0, 35.0], "LIF_RENT_BURDEN_INCOME_HIGH": [30.0, 25.0]})
    assert survey_city(survey) == [
        {"indicator": "LIF_RENT_BURDEN_RATIO", "value": 29, "kind": "published"},
        {"indicator": "LIF_ATTACHMENT", "value": 62, "kind": "published"},
        {"indicator": "LIF_RENT_BURDEN_INCOME_LOW", "value": 55.0, "kind": "computed"},
        {"indicator": "LIF_RENT_BURDEN_INCOME_MID", "value": 35.0, "kind": "computed"},
        {"indicator": "LIF_RENT_BURDEN_INCOME_HIGH", "value": 25.0, "kind": "computed"}]


def respondent(**changes):
    row = {"year": 2025, "survey_area": "Süd", "weight": 1.0, "tenant": True, "rent_low": 600.0, "rent_high": 700.0,
           "costs_low": 200.0, "costs_high": 250.0, "income_low": 1000.0, "income_high": 2000.0, "persons": 4.0,
           "children": 2.0, "household_form": "couple_children"}
    return row | changes


def frame(*rows):
    return pd.DataFrame(list(rows))


def test_burden_ratio_of_one_household():
    out = burden_ratios(frame(respondent())).iloc[0]
    assert out["household_income"] == pytest.approx(3150) and out["warm_rent"] == 875
    assert out["ratio"] == pytest.approx(27.78, abs=0.01)
    assert out["group"] == "LIF_RENT_BURDEN_INCOME_MID"


def test_open_classes_take_the_fixed_values():
    rows = [respondent(rent_low=1400.0, rent_high=math.nan, costs_low=400.0, costs_high=math.nan,
                       income_low=5000.0, income_high=math.nan, persons=1.0, children=0.0, household_form="single"),
            respondent(rent_low=0.0, rent_high=400.0, costs_low=0.0, costs_high=100.0,
                       income_low=0.0, income_high=1000.0, persons=1.0, children=0.0, household_form="single")]
    out = burden_ratios(frame(*rows))
    assert list(out["warm_rent"]) == [1700 + 450, 325 + 75]
    assert list(out["household_income"]) == [6000, 750]


def test_singles_and_couples_have_no_children():
    out = burden_ratios(frame(respondent(persons=1.0, children=math.nan, household_form="single")))
    assert out.iloc[0]["household_income"] == 1500
    out = burden_ratios(frame(respondent(persons=math.nan, children=math.nan, household_form="couple")))
    assert out.iloc[0]["household_income"] == 2250


def test_household_without_form_and_children_counts_adults():
    out = burden_ratios(frame(respondent(persons=2.0, children=math.nan, household_form=None)))
    assert out.iloc[0]["household_income"] == 2250


def test_incomplete_and_owners_are_left_out():
    rows = [respondent(tenant=False), respondent(persons=math.nan, household_form=None),
            respondent(persons=3.0, children=math.nan, household_form=None), respondent(rent_low=math.nan, rent_high=math.nan),
            respondent(income_low=math.nan, income_high=math.nan), respondent(weight=math.nan), respondent()]
    assert len(burden_ratios(frame(*rows))) == 1


def test_group_limits():
    rows = [respondent(income_low=low, income_high=low, persons=1.0, children=0.0, household_form="single")
            for low in (1999.0, 2000.0, 3199.0, 3200.0)]
    # a closed class of width 0 puts the midpoint at the value
    assert list(burden_ratios(frame(*rows))["group"]) == [
        "LIF_RENT_BURDEN_INCOME_LOW", "LIF_RENT_BURDEN_INCOME_MID", "LIF_RENT_BURDEN_INCOME_MID",
        "LIF_RENT_BURDEN_INCOME_HIGH"]


def test_income_position_moves_only_closed_income_classes():
    single = dict(persons=1.0, children=0.0, household_form="single")
    rows = [respondent(**single),  # closed class 1,000-2,000
            respondent(income_low=0.0, income_high=1000.0, **single),  # open lowest class
            respondent(persons=4.0, children=2.0, household_form="couple_children")]
    out = burden_ratios(frame(*rows), income_position=0.7)
    scale = [1.0, 1.0, 2.1]
    assert list(out["household_income"]) == pytest.approx([1700 * scale[0], 750 * scale[1], 1700 * scale[2]])
    assert list(out["warm_rent"]) == [875, 875, 875]  # rent and costs stay at their midpoint


def test_scale_is_household_income_over_the_income_midpoint():
    """Other use cases take the scale from its column (rent_burden: the class bounds × scale)."""
    rows = [respondent(),  # couple with two children: 1 + 0.5 + 2 × 0.3
            respondent(persons=1.0, children=0.0, household_form="single"),
            respondent(persons=3.0, children=2.0, household_form="single_parent")]
    out = burden_ratios(frame(*rows))
    midpoint = (out["income_low"] + out["income_high"]) / 2
    assert list(out["scale"]) == pytest.approx([2.1, 1.0, 1.6])
    assert list(out["scale"]) == pytest.approx(list(out["household_income"] / midpoint))


def test_income_position_leaves_the_highest_open_class_alone():
    open_high = respondent(income_low=5000.0, income_high=math.nan, persons=1.0, children=0.0, household_form="single")
    assert burden_ratios(frame(open_high), income_position=0.9).iloc[0]["household_income"] == 6000


def test_open_low_income_replaces_the_fixed_value():
    open_low = respondent(income_low=0.0, income_high=1000.0, persons=4.0, children=2.0, household_form="couple_children")
    out = burden_ratios(frame(open_low), open_low_income=600)
    assert out.iloc[0]["household_income"] == pytest.approx(600 * 2.1)


def test_default_call_is_unchanged():
    rows = [respondent(), respondent(income_low=0.0, income_high=1000.0), respondent(rent_low=1400.0, rent_high=math.nan)]
    pd.testing.assert_frame_equal(burden_ratios(frame(*rows)),
                                  burden_ratios(frame(*rows), income_position=0.5, open_low_income=None),
                                  check_exact=True)


def test_round_half_up():
    assert [round_half_up(v) for v in (52.5, 52.4, 57.5)] == [55, 50, 60]


def cases(n, area="Süd", **changes):
    return [respondent(survey_area=area, **changes) for _ in range(n)]


def test_income_breakdown_leaves_out_small_groups():
    small = burden_ratios(frame(*cases(29), *cases(30, area="West")))
    out = income_breakdown(small, ["Süd", "West"]).set_index("survey_area")
    mid = "LIF_RENT_BURDEN_INCOME_MID"
    assert math.isnan(out.loc["Süd", mid]) and out.loc["West", mid] == 30
    assert out.loc[CITY_ROW, mid] == 30
    assert math.isnan(out.loc["Süd", "LIF_RENT_BURDEN_INCOME_LOW"])
    assert list(out.columns) == list(BREAKDOWN_IDS)
    split = burden_ratios(frame(*cases(29), *cases(29, area="West")))
    out = income_breakdown(split, ["Süd", "West"]).set_index("survey_area")
    assert out[mid].isna().tolist() == [True, True, False]


def varied(n, area, **changes):
    return [respondent(survey_area=area, weight=1.0 + i % 3, rent_low=400.0 + 100 * (i % 5),
                       rent_high=500.0 + 100 * (i % 5), **changes) for i in range(n)]


SINGLE = dict(persons=1.0, children=0.0, household_form="single")  # household income 1,500: group LOW


def test_breakdown_half_widths_is_reproducible():
    ratios = burden_ratios(frame(*varied(40, "Süd"), *varied(35, "West"), *varied(30, "Süd", **SINGLE),
                                 *varied(31, "West", **SINGLE), *varied(50, "Nord", **SINGLE)))
    first = breakdown_half_widths(ratios, ["Süd", "West", "Nord"], draws=50)
    assert first == breakdown_half_widths(ratios, ["Süd", "West", "Nord"], draws=50)
    assert set(first) == {"typical", "max_low", "max_upper"}
    assert 0 <= first["typical"] <= first["max_low"] and first["max_upper"] >= 0


def test_breakdown_half_widths_split_the_lowest_group_from_the_others(monkeypatch):
    """typical: median over the areas of the lowest group; max_low: its largest; max_upper: the largest of the other
    groups. Cells under MIN_CASES count nowhere."""
    from pipeline.use_cases.survey import model
    cells = [("Süd", SINGLE, 2.0), ("West", SINGLE, 9.0), ("Nord", SINGLE, 4.0), ("Süd", {}, 3.0), ("West", {}, 1.0)]
    rows = []
    for area, household, width in cells:
        rows += [respondent(survey_area=area, rent_low=width * 100, rent_high=width * 100, **household)] * 30
    rows += [respondent(survey_area="Nord", rent_low=5000.0, rent_high=5000.0)] * 29  # under MIN_CASES
    # each cell's half width stands in as its rent / 100, so the test sees which cells count where
    monkeypatch.setattr(model, "_half_width", lambda cell, draws, rng: cell["rent_low"].iloc[0] / 100)
    out = breakdown_half_widths(burden_ratios(frame(*rows)), ["Süd", "West", "Nord"])
    assert out == {"typical": 4.0, "max_low": 9.0, "max_upper": 3.0}


def test_bootstrap_matches_weighted_median():
    ratio, weight = np.array([5.0, 1.0, 9.0, 3.0, 7.0]), np.array([1.0, 2.0, 1.0, 3.0, 1.0])
    fast = _bootstrap_medians(ratio, weight, 20, np.random.default_rng(3))
    picks = np.random.default_rng(3).integers(0, 5, (20, 5))
    assert list(fast) == [weighted_median(ratio[p], weight[p]) for p in picks]


def test_area_weight_shares_sum_to_100():
    shares = area_weight_shares(frame(respondent(weight=1.0), respondent(weight=3.0, survey_area="West")))
    assert shares == {"Süd": 25.0, "West": 75.0}


def test_tenant_medians_give_each_area_and_the_city():
    out = tenant_medians(burden_ratios(frame(respondent(), respondent(survey_area="West"))))
    assert set(out) == {"Süd", "West", CITY_ROW}
    assert out[CITY_ROW] == pytest.approx(27.78, abs=0.01)


def test_example_household_takes_the_medians_of_singles():
    single = dict(persons=1.0, children=0.0, household_form="single", costs_low=150.0, costs_high=200.0)
    rows = [respondent(rent_low=low, rent_high=low + 100, **single) for low in (400.0, 500.0, 600.0)]
    rows.append(respondent(persons=2.0, children=0.0, household_form="couple", rent_low=1000.0, rent_high=1100.0,
                           costs_low=150.0, costs_high=200.0))
    out = example_household(burden_ratios(frame(*rows)))
    assert (out["rent"], out["rent_low"], out["rent_high"]) == (550, 500, 600)
    assert (out["costs"], out["costs_low"], out["costs_high"]) == (175, 150, 200)
    assert out["income"] == 1500 and out["ratio"] == pytest.approx(48.33, abs=0.01)
