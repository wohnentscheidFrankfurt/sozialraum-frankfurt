"""Texts of the view „Neubau“ (texts.<lang>.yaml, README) and the constants behind their statements. checks.py checks
every statement of title, lead and ⓘ of both charts."""
from __future__ import annotations

import re

from pipeline.shared.core import palette
from pipeline.shared.core.indicator import Source
from pipeline.shared.core.texts import Texts, package_texts, per_language

T: dict[str, Texts] = package_texts(__file__)

FIRST_YEAR, LAST_YEAR = 2011, 2025
PROVISIONAL_FROM = 2023  # from here the subsidised numbers rest on the latest answer of the Magistrat
YEARS, AVERAGE = 10, 4100  # the lead: the mean of all dwellings of the last YEARS years, rounded to hundreds
# the phrases „fifth“ (18 % ≤ share of the last year < 20 %) and „eighth“ (every share before the last year ≤ 12.5 %)
# stand in texts.<lang>.yaml (PHRASES); checks.py tests them
STOCK_BREAKS = (2022,)  # from here stock and population rest on the Zensus 2022; the lines do not connect the year before
BASE_EFFECTS = (25679, 4378)  # the ⓘ: the Zensus 2022 lowered the population and the dwellings by these numbers
OLD_BASE, NEW_BASE = 2011, 2022  # Zensus of the stock and the population before and from STOCK_BREAKS
RENT_FROM = 2017  # the base of the second block (rents, prices, wages): all lines start here at 100; heading starts "Seit"
# the rents of new contracts must outgrow the dwellings in Euro by more than this (4 index points): above the sampling
# error of the Mietspiegel in Euro, about ±3.2 points by an own estimate (docs/data-rules.md, Uncertainty)
RENT_MARGIN = 0.04
# from the survey of this year the Mietspiegel counts the contracts of six years before the survey, before of four
# (§ 558 BGB since 2020); the sentence stands in the Unsicherheit of the rents (PHRASES)
SIX_YEARS_FROM = 2021
PRICE_MONTH = 7  # the VPI of this month stands for a year without Mietspiegel survey (survey months: July, 2017 June)
WAGE_QUARTERS = (2, 3)  # the wage of a year is the mean of these quarters (the survey days lie on their border)
# the value axes of the two charts of the second block (index, 2017 = 100): lowest and highest value and the ticks
# (docs/design.md, View Neubau); rents_view stops if a value lies outside
RENT_AXES = {"nominal": {"min": 95, "max": 140, "ticks": (100, 110, 120, 130, 140)},
             "real": {"min": 86, "max": 112, "ticks": (90, 95, 100, 105, 110)}}
OUTFLOW_THIRD = 1 / 3  # below this part of the mean outflow of the other years, the ⓘ names the outflow caveat
# the lowest and the highest persons per household of RENT_FROM to RENT_TO (the rule of the ⓘ); the check „rents
# households“ guards them
HOUSEHOLD_RANGE = (1.84, 1.87)
# the growth since RENT_FROM in percent, on the same base (Zensus 2022) and as published (the lines): dwellings,
# population; the check „rents uncertainty“ guards them (docs/data-rules.md, Uncertainty)
SAME_BASE_GROWTH, PUBLISHED_GROWTH = (7.8, 5.3), (6.6, 1.8)

# The survey days the tooltips show; the check compares year and month with the dates read from the brochures. The day
# is pinned in the date patterns of RENT_SOURCES.
SURVEY_DATES = {2017: "Juni 2017", 2021: "1.7.2021", 2023: "1.7.2023", 2025: "1.7.2025"}
RENT_TO = max(SURVEY_DATES)  # the rents block ends at the last survey year; the columns and the stock run to LAST_YEAR
# The German month names, to read the month of a date of SURVEY_DATES (shown_month). sources.py keeps the same list for
# the brochures: it may not import this module (tests/test_architecture.py), a test compares both.
GERMAN_MONTHS = {name: number for number, name in enumerate(
    ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November",
     "Dezember"], 1)}


def shown_month(shown: str) -> tuple[int, int] | None:
    """(year, month) of a survey date as the tooltips show it („1.7.2021“ or „Juni 2017“); None for any other form."""
    numeric, named = re.fullmatch(r"\d{1,2}\.(\d{1,2})\.(\d{4})", shown), re.fullmatch(r"(\w+) (\d{4})", shown)
    if numeric:
        month, year = int(numeric[1]), int(numeric[2])
    elif named:
        month, year = GERMAN_MONTHS.get(named[1]), int(named[2])
    else:
        return None
    return (year, month) if month is not None and 1 <= month <= 12 else None


def _values(t: Texts) -> dict[str, object]:
    """Everything the texts take from Python (the model fills the rest)."""
    return {"last_year": LAST_YEAR, "prev_year": LAST_YEAR - 1, "years": YEARS, "average": t.number(AVERAGE, 0),
            "provisional_from": PROVISIONAL_FROM, "rent_from": RENT_FROM, "rent_to": RENT_TO,
            "break_year": STOCK_BREAKS[0], "old_census": OLD_BASE, "new_census": NEW_BASE,
            "six_years_from": SIX_YEARS_FROM, "price_month": t.month(PRICE_MONTH),
            "rent_month": t.month(shown_month(SURVEY_DATES[RENT_TO])[1]), "wage_quarter": WAGE_QUARTERS[-1],
            "survey": SURVEY_DATES[RENT_TO], "population_effect": t.number(BASE_EFFECTS[0], 0),
            "stock_effect": t.number(BASE_EFFECTS[1], 0), "same_stock": t.number(SAME_BASE_GROWTH[0], 1, "%"),
            "same_population": t.number(SAME_BASE_GROWTH[1], 1, "%"),
            "published_stock": t.number(PUBLISHED_GROWTH[0], 1, "%"),
            "published_population": t.number(PUBLISHED_GROWTH[1], 1, "%")}


def _fill(node: dict, t: Texts, prefix: str, values: dict[str, object]) -> dict:
    """The tree under `prefix` with the values filled; the other placeholders stay for the model."""
    return {key: _fill(child, t, f"{prefix}.{key}", values) if isinstance(child, dict)
            else t.fill(f"{prefix}.{key}", **values) for key, child in node.items()}


def _phrases(t: Texts) -> dict[str, str]:
    """The statements that checks.py tests; {low} and {high} of the household range stay for the check."""
    return _fill(t.tree("phrases"), t, "phrases", _values(t))


def _view_texts(t: Texts) -> dict:
    texts = _fill(t.tree("view"), t, "view", _values(t))
    return {"link": texts.pop("link"), "title": texts.pop("title"), "lead": texts.pop("lead"),
            "key": texts.pop("key"), "info": texts.pop("info"), "source": texts.pop("source"),
            "color": palette.SUBSIDISED, **texts}


def _rents_texts(t: Texts) -> dict:
    values = {**_values(t), "low": t.number(HOUSEHOLD_RANGE[0], 2), "high": t.number(HOUSEHOLD_RANGE[1], 2)}
    return _fill(t.tree("rents"), t, "rents", values)


def _sources(t: Texts) -> list[Source]:
    return [Source(**_fill(t.tree(f"sources.{name}"), t, f"sources.{name}", _values(t)))
            for name in ("completions", "stock", "population", "prices", "wages", "rents", "households", "subsidised")]


PHRASES: dict[str, dict[str, str]] = per_language(_phrases, T)
# „link“ of TEXTS and RENTS_TEXTS names the question of the figure in the fragment of a direct link (docs/design.md,
# Direct links); once published it never changes
TEXTS: dict[str, dict] = per_language(_view_texts, T)
RENTS_TEXTS: dict[str, dict] = per_language(_rents_texts, T)
SOURCES: dict[str, list[Source]] = per_language(_sources, T)


# Rents of the Mietspiegel: per survey year the mean net rent per m² of the new and of the older (raised) contracts
# and the survey day. `config` names the file in pipeline/config.py. `pattern` is the pinned phrase as
# re.sub(r"\s+", " ", " ".join(page_texts(path))) renders it (PDF hyphenation stays: "ei- nen", "veränder- ten").
# The date pattern has the named groups month (digits or a German month name) and year. A survey day is the literal 01
# in the pattern, not a group: a brochure with another day finds no hit and the reader stops (SURVEY_DATES shows 1.7.).
# 2017: the labels of figure 21 of the Gutachten 2022 (all, older and new contracts in 2013, 2017 and 2021, in this
# order); REPORT_GROWTHS guards the order.
RENT_SOURCES = [
    {"year": 2017,
     "values": {"config": "MIETSPIEGEL_2022_REPORT_PDF",
                "pattern": r"€8,66 €9,36 €10,29 €(\d+,\d+) €(\d+,\d+) (\d+,\d+) €(\d+,\d+) €(\d+,\d+) (\d+,\d+)",
                "new_group": 5, "old_group": 2},
     "date": {"config": "MIETSPIEGEL_2018_REPORT_PDF",
              "pattern": r"Stichmonat für die zu ermittelnde Vergleichsmiete war der (?P<month>[A-Za-zäöü]+) "
                         r"(?P<year>\d{4})"}},
    {"year": 2021,
     "values": {"config": "MIETSPIEGEL_2022_REPORT_PDF",
                "pattern": r"Teilmenge der erhöhten Altverträge weist ei- nen Mittelwert von (\d+,\d+) €/m² auf, was "
                           r"einer relativen Wachstumsrate von \d+,\d+ % entspricht\. Der Mittelwert der neu "
                           r"abgeschlossenen Verträge beträgt (\d+,\d+) €/m²",
                "new_group": 2, "old_group": 1},
     "date": {"config": "MIETSPIEGEL_2022_PDF",
              "pattern": r"Erhebungsstichtag des Mietspiegels 2022 war der 01\.(?P<month>\d{2})\."
                         r"(?P<year>\d{4})"}},
    {"year": 2023,
     "values": {"config": "MIETSPIEGEL_2024_REPORT_PDF",
                "pattern": r"Untergruppe der Neuverträge beträgt (\d+,\d+) €/m2, für die Untergruppe der veränder- "
                           r"ten Altverträge (\d+,\d+) €/m2",
                "new_group": 1, "old_group": 2},
     "date": {"config": "MIETSPIEGEL_2024_PDF",
              "pattern": r"Erhebungsstichtag für die Anpassungsstichprobe des Mietspiegels 2024 war der "
                         r"01\.(?P<month>\d{2})\.(?P<year>\d{4})"}},
    {"year": 2025,
     "values": {"config": "MIETSPIEGEL_2026_REPORT_PDF",
                "pattern": r"Teilmenge der erhöhten Altverträge weist einen Mittelwert von (\d+,\d+) €/m² auf, was "
                           r"einer Wachstumsrate von \d+,\d+ % entspricht\. Der Mittelwert der neu abgeschlossenen "
                           r"Verträge beträgt (\d+,\d+) €/m²",
                "new_group": 2, "old_group": 1},
     "date": {"config": "MIETSPIEGEL_2026_PDF",
              "pattern": r"Erhebungsstichtag für den Mietspiegel 2026 war der 01\.(?P<month>\d{2})\."
                         r"(?P<year>\d{4})"}},
]
# The growth rates (percent) the reports print for the two groups against the survey before. The check compares them
# with the growth of the values read; this guards the labels of 2017, which no sentence prints.
REPORT_GROWTHS = [
    {"year": 2021, "base": 2017, "config": "MIETSPIEGEL_2022_REPORT_PDF",
     "pattern": r"Altverträge weist ei- nen Mittelwert von \d+,\d+ €/m² auf, was einer relativen Wachstumsrate von "
                r"(\d+,\d+) % entspricht\. Der Mittelwert der neu abgeschlossenen Verträge beträgt \d+,\d+ €/m², "
                r"entsprechend einer relativen Wachstumsrate von (\d+,\d+) %",
     "new_group": 2, "old_group": 1},
    {"year": 2025, "base": 2023, "config": "MIETSPIEGEL_2026_REPORT_PDF",
     "pattern": r"Altverträge weist einen Mittelwert von \d+,\d+ €/m² auf, was einer Wachstumsrate von (\d+,\d+) % "
                r"entspricht\. Der Mittelwert der neu abgeschlossenen Verträge beträgt \d+,\d+ €/m², die "
                r"entsprechende Wachs- tumsrate liegt bei (\d+,\d+) %",
     "new_group": 2, "old_group": 1},
]

# Subsidised dwellings from 2023: per year and programme the latest answer of the Magistrat. `config` names
# the file in pipeline/config.py; `pattern` is the pinned phrase, `group` the number in it. 2011–2022: B 12/2024.
SUBSIDISED_SOURCES = [
    {"year": 2023, "programme": "fw1", "config": "ANSWER_F_158_2026_PDF",
     "pattern": r"2023 (\d+) (\d+) (\d+) 2024 (\d+) (\d+) (\d+) 2025 (\d+) (\d+) (\d+)", "group": 3},
    {"year": 2023, "programme": "fw2", "config": "ANSWER_F_3150_2025_PDF",
     "pattern": r"2023: Förderweg 1: (\d+) WE, Förderweg 2: (\d+) WE", "group": 2},
    {"year": 2024, "programme": "fw1", "config": "ANSWER_F_79_2026_PDF",
     "pattern": r"(\d+) Wohneinheiten fielen auf den Förderweg 1", "group": 1},
    {"year": 2024, "programme": "fw2", "config": "ANSWER_F_79_2026_PDF",
     "pattern": r"Im Förderweg 2, FW 2, wurden (\d+) Wohneinheiten fertiggestellt", "group": 1},
    {"year": 2025, "programme": "fw1", "config": "ANSWER_F_9_2026_PDF",
     "pattern": r"wurden 2025 (\d+) Wohneinheiten im Förderweg 1", "group": 1},
    {"year": 2025, "programme": "fw2", "config": "ANSWER_F_9_2026_PDF",
     "pattern": r"Im Förderweg 2 wurden (\d+) Wohneinheiten fertiggestellt", "group": 1},
]
# F 158/2026 confirms FW 1 2025 (checks.py)
CONFIRM_FW1_LAST = {"config": "ANSWER_F_158_2026_PDF", "pattern": SUBSIDISED_SOURCES[0]["pattern"], "group": 9}
