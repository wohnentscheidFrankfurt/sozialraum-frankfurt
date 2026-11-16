"""Checks of the survey step: the classes typed into FIGURES match the minimum and maximum printed in the report.
Pure module."""
from __future__ import annotations

from pipeline.shared.core.checks import FAIL, OK, WARN, Check
from pipeline.use_cases.survey.model import CITY_ROW, round_half_up

CITY_TOLERANCE = 1  # points between the rounded own city median and the printed value
AREA_TOLERANCE = 2  # points between the rounded own area median and its printed class


def check_printed_extremes(pages: list[str], figures: dict[str, dict],
                           extremes: dict[str, tuple[int, str, str]]) -> Check:
    """extremes: indicator -> (index of the page in the PDF, area with the minimum, area with the maximum)."""
    name = "Survey: classes against the minimum and maximum in the report"
    wrong = []
    for indicator, (page, low, high) in extremes.items():
        text = " ".join(pages[page].split())
        classes = figures[indicator]["classes"]
        first, last = min(classes), max(classes)
        if not (low in classes[first] and f"Min.: {first[0]:g} {low}" in text
                and high in classes[last] and f"Max.: {last[1]:g} {high}" in text):
            wrong.append(indicator)
    if wrong:
        return Check(name, FAIL, "not as printed: " + ", ".join(wrong))
    return Check(name, OK, ", ".join(f"{i}: minimum {low}, maximum {high}" for i, (_, low, high) in extremes.items()))


def check_printed_city_sentence(pages: dict[int, list[str]], printed: dict[int, tuple[int, int]]) -> Check:
    """pages: year -> page texts of the report. printed: year -> (index of the page, printed city value)."""
    name = "Survey: city value of the rent burden in the sentence of the report"
    wrong = []
    for year, (page, value) in printed.items():
        text = " ".join(pages[year][page].split()).replace("- ", "")
        if f"mindestens {value} Prozent" not in text:
            wrong.append(f"{year}: „mindestens {value} Prozent“ not on page index {page}")
    if wrong:
        return Check(name, FAIL, "; ".join(wrong))
    return Check(name, OK, ", ".join(f"{year}: {value} %" for year, (_, value) in printed.items()))


def _gap_to_class(value: float, low: float, high: float) -> float:
    return max(low - value, value - high, 0.0)


def check_own_against_printed(own: dict[int, dict[str, float]], classes: dict[tuple, tuple[str, ...]],
                              printed: dict[int, tuple[int, int]]) -> Check:
    """own: year -> survey area (and CITY_ROW) -> unrounded median. Rounded half up to the shown whole percent.
    The area values of 2025 are compared to the printed classes, those of 2024 only in the city."""
    name = "Survey: own medians of the tenants against the report"
    city = {year: round_half_up(own[year][CITY_ROW], 1) for year in printed}
    problems = [f"city {year}: own {city[year]:g} against printed {value}"
                for year, (_, value) in printed.items() if abs(city[year] - value) > CITY_TOLERANCE]
    gaps = {area: _gap_to_class(round_half_up(own[2025][area], 1), low, high)
            for (low, high), areas in classes.items() for area in areas}
    problems += [f"{area}: {gap:g} points outside its class" for area, gap in gaps.items() if gap > AREA_TOLERANCE]
    if problems:
        return Check(name, WARN, "; ".join(problems))
    worst = max(gaps, key=gaps.get)
    cities = ", ".join(f"{year}: {own[year][CITY_ROW]:.1f} (shown {city[year]:g}) against {value}" for year, (_, value) in printed.items())
    return Check(name, OK, f"city {cities}; largest gap to a class: {worst} ({gaps[worst]:g} points)")


def check_area_codes(shares: dict[int, dict[str, float]], tolerance: float = 0.5) -> Check:
    """shares: year -> survey area -> share of the weights in percent. Same codes, same areas in both years."""
    name = "Survey: area codes of the two survey years stay the same"
    first, second = sorted(shares)
    gaps = {area: abs(shares[first][area] - shares[second][area]) for area in shares[first].keys() & shares[second].keys()}
    off = sorted(area for area, gap in gaps.items() if gap > tolerance)
    if off:
        return Check(name, FAIL, f"weight share differs by more than {tolerance:g} points ({first} to {second}): "
                                 + ", ".join(off))
    return Check(name, OK, f"largest gap of a weight share {max(gaps.values()):.3f} points ({first} to {second})")
