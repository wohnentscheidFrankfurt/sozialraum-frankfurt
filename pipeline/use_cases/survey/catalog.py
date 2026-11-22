"""Titles and ⓘ of the survey indicators and the worked example of the rent burden (texts.<lang>.yaml). Pure module."""
from __future__ import annotations

from pipeline.shared.core.calc_example import CalcExample, Row
from pipeline.shared.core.indicator import Indicator, Source, year_of
from pipeline.shared.core.texts import Texts, package_texts, per_language
from pipeline.use_cases.survey.model import BREAKDOWN_IDS, INCOME_LIMITS, MIN_CASES, STEP, round_half_up

T: dict[str, Texts] = package_texts(__file__)

SURVEY_LEVELS = ("district",)  # every district lies in one survey area (README)
_LOW_ID, _MID_ID, _HIGH_ID = BREAKDOWN_IDS
# Placeholders of the half widths (model.breakdown_half_widths), apart from the range_/high_ names of catalog_numbers:
# typical and largest of the lowest group, largest of the two upper groups. texts.<lang>.yaml writes them in
# `income_uncertainty`.
HALF_WIDTH_NAMES = {"typical": f"typical_{_LOW_ID}", "max_low": f"max_{_LOW_ID}",
                    "max_upper": "max_LIF_RENT_BURDEN_INCOME_UPPER"}


def _limits(t: Texts) -> dict[str, str]:
    """The income limits as the map prints them (model.INCOME_LIMITS)."""
    lower, upper = (t.number(limit, 0) for limit in INCOME_LIMITS)
    return {"lower": lower, "upper": upper}


def _income_titles(t: Texts) -> dict[str, str]:
    """The income groups of the tooltip, as lines under the lead."""
    return {kid: t.fill(f"income_titles.{kid}", **_limits(t)) for kid in BREAKDOWN_IDS}


def _values(t: Texts) -> dict[str, object]:
    """Everything the texts of the income groups take from Python (the build fills the rest)."""
    titles = _income_titles(t)
    return {**_limits(t), "title_low": titles[_LOW_ID], "title_mid": titles[_MID_ID], "title_high": titles[_HIGH_ID],
            "step": STEP, "min_cases": MIN_CASES}


def _sources(t: Texts) -> list[Source]:
    return [Source(**t.tree("sources.report")), Source(**t.tree("sources.microdata"))]


INCOME_TITLES: dict[str, dict[str, str]] = per_language(_income_titles, T)
INCOME_LEAD: dict[str, str] = per_language(lambda t: t["income_lead"], T)
INCOME_CALC: dict[str, str] = per_language(lambda t: t.fill("income_calc", **_values(t)), T)
INCOME_RULE: dict[str, str] = per_language(lambda t: t.fill("income_rule", **_values(t)), T)
INCOME_UNCERTAINTY: dict[str, str] = per_language(lambda t: t.fill("income_uncertainty", **_values(t)), T)
SOURCES: dict[str, list[Source]] = per_language(_sources, T)


def half_width_numbers(widths: dict[str, float], t: Texts) -> dict[str, str]:
    """The half widths of the build as whole points, rounded half up, for the Unsicherheit of the rent burden.
    t: any texts of a language; they format the numbers."""
    return {name: t.number(round_half_up(widths[key], 1), 0) for key, name in HALF_WIDTH_NAMES.items()}


def _indicators(t: Texts) -> list[Indicator]:
    year = year_of(t["as_of"])
    rent, situation = t["core.groups.rent"], t["core.groups.situation"]
    values = _values(t)
    return [
        Indicator("LIF_RENT_BURDEN_RATIO", t["LIF_RENT_BURDEN_RATIO.title"], rent, "%", SURVEY_LEVELS,
                  t["LIF_RENT_BURDEN_RATIO.source"], t["LIF_RENT_BURDEN_RATIO.as_of"],
                  t.fill("LIF_RENT_BURDEN_RATIO.calc", **values), "orange", 0,
                  type="classes",
                  rule=t.fill("LIF_RENT_BURDEN_RATIO.rule", **values, label="26–28", low=25, high=28),
                  uncertainty=t.fill("LIF_RENT_BURDEN_RATIO.uncertainty", **values),
                  legend_note=t.fill("LIF_RENT_BURDEN_RATIO.legend_note", year=year),
                  breakdown_lead=t["income_lead"], section="rent", survey_area=True),
        # tooltip lines of the rent burden, no layer; the ⓘ of the rent burden explains them
        *(Indicator(kid, title, rent, "%", SURVEY_LEVELS, t["income_group.source"], t["income_group.as_of"],
                    t["income_group.calc"], "orange", 0, layer=False, criterion=False, estimate=True,
                    breakdown_of="LIF_RENT_BURDEN_RATIO", section="rent", survey_area=True)
          for kid, title in _income_titles(t).items()),
        Indicator("LIF_ATTACHMENT", t["LIF_ATTACHMENT.title"], situation, "%", SURVEY_LEVELS,
                  t["LIF_ATTACHMENT.source"], t["LIF_ATTACHMENT.as_of"], t["LIF_ATTACHMENT.calc"], "teal", 0,
                  type="classes", rule=t.fill("rule", label="64–70", low=63, high=70),
                  uncertainty=t["uncertainty"], legend_note=t.fill("LIF_ATTACHMENT.legend_note", year=year),
                  section="situation", survey_area=True),
    ]


INDICATORS: dict[str, list[Indicator]] = per_language(_indicators, T)


def _class_text(e: dict, kind: str, t: Texts) -> str:
    return t.fill("calc_example.bracket", low=t.number(e[f"{kind}_low"], 0), high=t.number(e[f"{kind}_high"], 0))


def survey_calc_example(e: dict, t: Texts) -> CalcExample:
    """Written sum of one household (docs/texts.md, Written sums): rent and costs, warm rent, income, its ratio. The
    ratio is one household, not the map value: whole percent, rounded half up, without „~“. e: example_household.
    t: the texts of this package (T[lang]); the area is the household."""
    return CalcExample(t["calc_example.household"], (
        Row("", round(e["rent"]), 0, t.fill("calc_example.rent", bracket=_class_text(e, "rent", t)), unit="€"),
        Row("+", round(e["costs"]), 0, t.fill("calc_example.costs", bracket=_class_text(e, "costs", t)), unit="€"),
        Row("", round(e["rent"] + e["costs"]), 0, t["calc_example.warm_rent"], total=True, unit="€"),
        Row("÷", round(e["income"]), 0, t.fill("calc_example.income", bracket=_class_text(e, "income", t)), unit="€"),
        Row("", int(round_half_up(e["ratio"], 1)), 0, t["calc_example.ratio"], total=True, unit="%")))
