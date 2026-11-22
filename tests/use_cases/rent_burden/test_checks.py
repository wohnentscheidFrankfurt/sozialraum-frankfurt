import copy
from dataclasses import replace

import pytest

from pipeline import config
from pipeline.shared.core.checks import FAIL, OK
from pipeline.use_cases.new_construction.catalog import RENT_TO
from pipeline.use_cases.rent_burden.catalog import MEASURED, PHRASES as PHRASES_BY_LANGUAGE, T
from pipeline.use_cases.rent_burden.checks import low_income_checks, net_wage_checks, wage_checks
from pipeline.use_cases.rent_burden.sources import (HESSEN_QUANTILES, WAGE_RULES, read_bmf_reference,
                                                    read_est_reference)
from pipeline.use_cases.survey.model import BREAKDOWN_IDS

PHRASES, LANG = PHRASES_BY_LANGUAGE["de"], T["de"]


def _by_name(checks):
    return {c.name: c for c in checks}


def _real():
    return read_bmf_reference(config.BMF_WAGE_TAX_CSV), read_est_reference(config.BMF_WAGE_TAX_CSV)


@pytest.fixture(name="grosses", scope="module")
def grosses_fixture(table):
    """The gross wage the model uses per (year, person): the column gross of the real wage table."""
    return {(int(r.year), r.person): float(r.gross) for r in table.itertuples()}


def test_bmf_check_passes_on_the_real_reference(grosses):
    reference, est = _real()
    checks = _by_name(net_wage_checks(WAGE_RULES, reference, est, grosses))
    assert checks["net wage against BMF"].status == OK
    assert checks["net wage tariff 2017"].status == OK


def test_bmf_check_fails_for_a_year_of_the_rules_without_rows(grosses):
    """Every year of the rules but the Einkommensteuer year needs a row of the Lohnsteuerrechner for each person."""
    reference, est = _real()
    rules = {**WAGE_RULES, 2027: WAGE_RULES[2025]}
    check = _by_name(net_wage_checks(rules, reference, est, grosses))["net wage against BMF"]
    assert check.status == FAIL
    assert "2027" in check.text
    one_less = {k: v for k, v in reference.items() if k != (2023, "median")}
    check = _by_name(net_wage_checks(WAGE_RULES, one_less, est, grosses))["net wage against BMF"]
    assert check.status == FAIL
    assert "2023" in check.text and "median" in check.text


def test_bmf_check_fails_when_a_base_is_not_the_gross_of_the_model(grosses):
    reference, est = _real()
    shifted = {**grosses, (2025, "median"): grosses[(2025, "median")] + 0.02}
    check = _by_name(net_wage_checks(WAGE_RULES, reference, est, shifted))["net wage against BMF"]
    assert check.status == FAIL
    assert "2025" in check.text and "median" in check.text


def test_bmf_check_fails_when_a_tariff_constant_is_off(grosses):
    reference, est = _real()
    rules = dict(WAGE_RULES)
    rules[2021] = replace(rules[2021], tariff=replace(rules[2021].tariff, c3=rules[2021].tariff.c3 + 1))
    check = _by_name(net_wage_checks(rules, reference, est, grosses))["net wage against BMF"]
    assert check.status == FAIL
    assert "2021" in check.text


def test_tariff_check_fails_when_the_2017_tariff_is_off(grosses):
    reference, est = _real()
    rules = dict(WAGE_RULES)
    rules[2017] = replace(rules[2017], tariff=replace(rules[2017].tariff, c3=rules[2017].tariff.c3 + 5))
    checks = _by_name(net_wage_checks(rules, reference, est, grosses))
    assert checks["net wage tariff 2017"].status == FAIL


# --- the statements of S1 and S2 (catalog: FACTOR_RANGE, SENSITIVITY_POINTS, ... ABOUT_HALF) ---

WAGE_CHECKS = ("rent wage heading", "rent wage sensitivity", "rent wage ceiling", "rent wage measured")
LOW_CHECKS = ("low income heading", "low income lead", "low income share")


def _wage(facts, **changes):
    args = {"quantiles": HESSEN_QUANTILES, "ceiling": WAGE_RULES[RENT_TO].ceiling_rv, "measured": float(MEASURED),
            "phrases": PHRASES, "t": LANG}
    return _by_name(wage_checks(facts, **{**args, **changes}))


def _mutated(facts, key, value):
    mutated = copy.deepcopy(facts)
    mutated[key] = value
    return mutated


def _low(low_facts, **parts):
    return _by_name(low_income_checks({**low_facts, **parts}, PHRASES))


def test_wage_checks_pass_on_the_real_facts(facts):
    checks = _wage(facts)
    assert tuple(checks) == WAGE_CHECKS
    assert all(c.status == OK for c in checks.values()), [c for c in checks.values() if c.status != OK]


def test_wage_checks_are_all_fail_checks_with_values_in_the_text(facts):
    """A failing check is FAIL, and its text names the value it found."""
    broken = _mutated(_mutated(facts, "factor", (2.85, 3.6)), "sensitivity", (0.95, 5.6))
    checks = _wage(broken, quantiles={88: 7000, 89: 7500}, measured=30.0)
    assert {c.status for c in checks.values() if c.status != OK} == {FAIL}
    assert "3.6" in checks["rent wage heading"].text and "5.6" in checks["rent wage sensitivity"].text
    assert "30" in checks["rent wage measured"].text and "7000" in checks["rent wage ceiling"].text


def test_wage_heading_fails_for_a_factor_outside_the_range(facts):
    assert _wage(_mutated(facts, "factor", (2.85, 3.6)))["rent wage heading"].status == FAIL
    assert _wage(_mutated(facts, "factor", (2.4, 3.3)))["rent wage heading"].status == FAIL


def test_wage_sensitivity_fails_outside_one_to_four_points(facts):
    assert _wage(_mutated(facts, "sensitivity", (1.39, 4.6)))["rent wage sensitivity"].status == FAIL  # rounds to 5
    assert _wage(_mutated(facts, "sensitivity", (0.4, 4.09)))["rent wage sensitivity"].status == FAIL


def test_wage_sensitivity_fails_if_another_person_has_the_largest_gap(facts):
    persons = copy.deepcopy(facts["sensitivity_persons"])
    persons["median"] = (persons["median"][0], 6.0)
    assert _wage(_mutated(facts, "sensitivity_persons", persons))["rent wage sensitivity"].status == FAIL


def test_wage_ceiling_needs_the_ceiling_between_p88_and_p89(facts):
    ceiling = WAGE_RULES[RENT_TO].ceiling_rv
    assert _wage(facts, ceiling=HESSEN_QUANTILES[89] + 1)["rent wage ceiling"].status == FAIL  # above P89
    assert _wage(facts, ceiling=HESSEN_QUANTILES[88] - 1)["rent wage ceiling"].status == FAIL  # below P88
    assert _wage(facts, ceiling=ceiling)["rent wage ceiling"].status == OK


def test_wage_ceiling_fails_if_the_constant_no_longer_matches_the_quantiles(facts, monkeypatch):
    """„gut 11 %“ means 11 to under 12 percent earn more: P88 and P89 must enclose it, not only the ceiling."""
    monkeypatch.setattr("pipeline.use_cases.rent_burden.checks.CEILING_ABOVE", 12)
    assert _wage(facts)["rent wage ceiling"].status == FAIL
    monkeypatch.setattr("pipeline.use_cases.rent_burden.checks.CEILING_ABOVE", 10)
    assert _wage(facts)["rent wage ceiling"].status == FAIL


def test_wage_measured_must_equal_the_published_value(facts):
    assert _wage(facts, measured=30.0)["rent wage measured"].status == FAIL
    assert _wage(facts, measured=29.0)["rent wage measured"].status == OK


def test_low_income_checks_pass_on_the_real_facts(low_facts):
    checks = _low(low_facts)
    assert tuple(checks) == LOW_CHECKS
    assert all(c.status == OK for c in checks.values()), [c for c in checks.values() if c.status != OK]


def test_low_income_heading_fails_for_a_median_away_from_half(low_facts):
    for kind, key in (("position", 0.4), ("open_low", 600)):
        medians = copy.deepcopy(low_facts["medians"])
        medians[kind][key] = 42.0
        assert _low(low_facts, medians=medians)["low income heading"].status == FAIL


def test_low_income_lead_fails_if_the_highest_group_is_not_nearly_a_quarter(low_facts):
    high = BREAKDOWN_IDS[-1]
    for value in (25.0, 19.9):
        main = low_facts["main"].copy()
        main.loc[high, "median"] = value
        assert _low(low_facts, main=main)["low income lead"].status == FAIL


def test_low_income_share_must_lie_between_the_bounds(low_facts):
    low = BREAKDOWN_IDS[0]
    for value in (low_facts["bounds"][0] - 1, low_facts["bounds"][1] + 1):
        main = low_facts["main"].copy()
        main.loc[low, "share"] = value
        assert _low(low_facts, main=main)["low income share"].status == FAIL


def test_low_income_share_fails_if_a_sensitivity_moves_the_rounded_share_too_far(low_facts):
    """„~17 %“: under every sensitivity the share rounds to at most ABOUT_SHARE whole percent from the main case."""
    for kind, key, value, status in (("position", 0.7, 18.6, FAIL), ("open_low", 600, 15.4, FAIL),
                                     ("position", 0.7, 18.4, OK), ("open_low", 600, 15.5, OK)):
        shares = copy.deepcopy(low_facts["shares"])
        shares[kind][key] = value
        check = _low(low_facts, shares=shares)["low income share"]
        assert check.status == status, (kind, key, value)
        assert str(value) in check.text
