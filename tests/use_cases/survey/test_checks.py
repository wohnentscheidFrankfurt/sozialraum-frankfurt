from pipeline.shared.core.checks import FAIL, OK, WARN
from pipeline.use_cases.survey.checks import (check_area_codes, check_own_against_printed, check_printed_city_sentence,
                                              check_printed_extremes)

FIGURES = {"X": {"city": 5, "classes": {(1, 3): ("A", "B"), (4, 9): ("C",)}}}
PAGES = ["", "Abb. Min.: 1 A Max.: 9 C"]


def test_printed_extremes_match_the_classes():
    assert check_printed_extremes(PAGES, FIGURES, {"X": (1, "A", "C")}).status == OK


def test_another_extreme_in_the_report_fails():
    found = check_printed_extremes(PAGES, FIGURES, {"X": (1, "B", "C")})
    assert found.status == FAIL and "X" in found.text
    assert check_printed_extremes(["", "Min.: 2 A Max.: 9 C"], FIGURES, {"X": (1, "A", "C")}).status == FAIL


PRINTED = {2025: (30, 29), 2024: (25, 29)}
CLASSES = {(30, 30): ("Ost 2", "Nord"), (26, 29): ("West",)}
OWN = {2025: {"city": 29.4, "Ost 2": 32.2, "Nord": 30.0, "West": 27.0}, 2024: {"city": 29.3}}
SHARES = {2024: {"Ost 2": 6.3, "West": 10.0}, 2025: {"Ost 2": 6.4, "West": 10.0}}


def _pages(text_2025: str, text_2024: str = "mindestens 29 Prozent") -> dict[int, list[str]]:
    return {2025: ["x"] * 30 + [text_2025], 2024: ["x"] * 25 + [text_2024]}


def test_printed_city_sentence_found_after_joining_lines_and_hyphen_breaks():
    pages = _pages("Mieter zahlen min-\ndestens  29\nProzent des Einkommens")
    assert check_printed_city_sentence(pages, PRINTED).status == OK


def test_printed_city_sentence_with_another_value_fails():
    assert check_printed_city_sentence(_pages("mindestens 30 Prozent"), PRINTED).status == FAIL


def test_own_medians_match_the_report():
    found = check_own_against_printed(OWN, CLASSES, PRINTED)
    assert found.status == OK and "29" in found.text and "Ost 2" in found.text


def test_city_median_more_than_one_point_off_warns():
    own = {**OWN, 2025: {**OWN[2025], "city": 30.6}}
    assert check_own_against_printed(own, CLASSES, PRINTED).status == WARN


def test_area_median_more_than_two_points_outside_its_class_warns():
    own = {**OWN, 2025: {**OWN[2025], "Ost 2": 33.0}}
    assert check_own_against_printed(own, CLASSES, PRINTED).status == WARN


def test_survey_area_shares_stable_between_the_years():
    assert check_area_codes(SHARES).status == OK


def test_share_gap_above_the_tolerance_fails():
    shares = {**SHARES, 2025: {"Ost 2": 6.9, "West": 10.0}}
    assert check_area_codes(shares).status == FAIL
