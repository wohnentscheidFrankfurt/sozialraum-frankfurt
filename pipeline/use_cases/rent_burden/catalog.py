"""Texts of the view „Miete“ (texts.<lang>.yaml, README) and the constants behind their statements. Figure S1: the
warm rent of one flat against the net wage of three model persons, new and older contracts, in the latest survey year
of the Mietspiegel (wage bars).
Figure S2: the warm rent against the household income of adult tenants per income group, split into burden classes.
checks.py checks every statement of title, lead and ⓘ."""
from __future__ import annotations

import datetime

from pipeline.shared.core import palette
from pipeline.shared.core.indicator import Source
from pipeline.shared.core.texts import Texts, package_texts, per_language
from pipeline.use_cases.new_construction.catalog import RENT_FROM, RENT_TO, SURVEY_DATES, shown_date
from pipeline.use_cases.survey.model import BREAKDOWN_IDS, INCOME_LIMITS

T: dict[str, Texts] = package_texts(__file__)

# the model persons: full time at the Mindestlohn, at the median wage of the residents, at the pension ceiling
PERSONS = ("mindestlohn", "median", "high")
CONTRACTS = ("new", "old")  # the two groups of the Mietspiegel: new contracts and older (raised) contracts
FLAT_M2 = 55  # the median class 50–60 m² of one-person tenant households, Leben in Frankfurt 2024 and 2025
CALC_PERSON, CALC_CONTRACT = "mindestlohn", "new"  # the written sums of the ⓘ of S1 (wage_view)
NEBENKOSTEN_MONTH = 6  # the Kosten der Unterkunft of the BA are those of June of each survey year (BA_KDU_XLSX)
# The statements of title and ⓘ; checks.py tests each against the data (docs/data-rules.md, Checks). Their words stand
# in texts.<lang>.yaml (PHRASES). The lead takes its euros from the table.
FACTOR_RANGE = (2.5, 3.5)  # title „etwa dreimal“: share Mindestlohn ÷ share high wage, both contracts of RENT_TO
SENSITIVITY_POINTS = (1, 4)  # Unsicherheit: with the Nebenkosten of the Mietspiegel the share lies this much lower
MEASURED = 29  # Unsicherheit: the published median burden of all tenants (Leben in Frankfurt 2024 and 2025), percent
CEILING_ABOVE = 11  # Regel „gut 11 %“: percent of full-time employees in Hessen above the pension ceiling (P88–P89)

# S2 title „etwa der Hälfte“: every median of the lowest group, whatever the income inside its class, lies this many
# points around 50 (checks.py)
ABOUT_HALF = 7.5
# S2 lead „knapp ein Viertel“: the median of the highest group, from this to under that, in percent (checks.py)
ALMOST_QUARTER = (20, 25)
# S2 lead „~17 %“: the share of the lowest group, rounded half up to whole percent, lies at most this many percent
# from the main case under every sensitivity of the income (checks.py)
ABOUT_SHARE = 1

SURVEY_YEARS = (2024, 2025)  # the surveys of the microdata (config.SURVEY_MICRODATA), pooled
# the burden classes: percent of the household income, from the lower bound to under the upper (None: open)
CLASSES = ((0, 30), (30, 40), (40, 50), (50, None))
# the red family of the rents, darker = heavier burden (call 2 of the plan); the key and the tooltips name the classes
CLASS_COLOURS = (palette.STATE, palette.NONPROFIT, palette.PUBLIC, palette.COOP)


def _values(t: Texts) -> dict[str, object]:
    """Everything the texts take from Python (the model fills the rest)."""
    years = sorted(SURVEY_DATES)
    lower, upper = (t.number(limit, 0, "€") for limit in INCOME_LIMITS)
    return {"rent_from": RENT_FROM, "rent_to": RENT_TO, "last_survey": shown_date(RENT_TO, t),
            "stock_day": t.date(datetime.date(RENT_TO, 12, 31)),
            "costs_month": t.month(NEBENKOSTEN_MONTH), "mietspiegel_year": RENT_TO + 1, "flat_m2": FLAT_M2,
            "ceiling_above": CEILING_ABOVE, "sensitivity_low": SENSITIVITY_POINTS[0],
            "sensitivity_high": SENSITIVITY_POINTS[1], "measured": MEASURED, "lower": lower, "upper": upper,
            "first": SURVEY_YEARS[0], "second": SURVEY_YEARS[1], "earlier": ", ".join(map(str, years[:-1])),
            "last": years[-1]}


def _fill(node: dict, t: Texts, prefix: str, values: dict[str, object]) -> dict:
    """The tree under `prefix` with the values filled; the other placeholders stay for the model."""
    return {key: _fill(child, t, f"{prefix}.{key}", values) if isinstance(child, dict)
            else t.fill(f"{prefix}.{key}", **values) for key, child in node.items()}


def _class_name(low: float, high: float | None, unit: str, t: Texts) -> str:
    """„unter 30 %“, „30 bis unter 40 %“, „50 % und mehr“: a class from its bounds (0: open at the bottom). The unit
    stands behind the number that comes last in the name."""
    if low == 0:
        return t.fill("class_name.below", high=t.number(high, 0, unit))
    if high is None:
        return t.fill("class_name.from", low=t.number(low, 0, unit))
    return t.fill("class_name.between", low=t.number(low, 0), high=t.number(high, 0, unit))


def _phrases(t: Texts) -> dict[str, str]:
    """The statements that checks.py tests."""
    return _fill(t.tree("phrases"), t, "phrases", _values(t))


def _wage_texts(t: Texts) -> dict:
    return _fill(t.tree("wage"), t, "wage", _values(t))


def _low_income_texts(t: Texts) -> dict:
    texts = _fill(t.tree("low_income"), t, "low_income", _values(t))
    bounds = tuple(zip((0, *INCOME_LIMITS), (*INCOME_LIMITS, None)))
    return {"link": texts.pop("link"), "title": texts.pop("title"), "lead": texts.pop("lead"),
            "info": texts.pop("info"), "source": texts.pop("source"),
            "groups": {group: _class_name(low, high, "€", t) for group, (low, high) in zip(BREAKDOWN_IDS, bounds)},
            "classes": [_class_name(low, high, "%", t) for low, high in CLASSES], **texts}


def _sources(t: Texts) -> list[Source]:
    return [Source(**_fill(t.tree(f"sources.{name}"), t, f"sources.{name}", _values(t)))
            for name in ("ba_costs", "ba_wages", "hsl_wages", "micro_census")]


PHRASES: dict[str, dict[str, str]] = per_language(_phrases, T)
# „link“ names the question of the figure in the fragment of a direct link (docs/design.md, Direct links); once
# published it never changes
WAGE_TEXTS: dict[str, dict] = per_language(_wage_texts, T)
LOW_INCOME_TEXTS: dict[str, dict] = per_language(_low_income_texts, T)
SOURCES: dict[str, list[Source]] = per_language(_sources, T)
