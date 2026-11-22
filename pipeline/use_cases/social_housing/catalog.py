"""Titles and ⓘ of the social housing indicators (texts.<lang>.yaml); the step checks SH_AS_OF against the report.
Pure module."""
from __future__ import annotations

import datetime

from pipeline.shared.core.calc_example import CalcExample, Row
from pipeline.shared.core.indicator import QUARTERS_ONLY, Indicator, Source
from pipeline.shared.core.texts import Texts, package_texts, per_language

T: dict[str, Texts] = package_texts(__file__)

SH_DATE = datetime.date(2025, 12, 31)  # the as-of date of the report
SH_AS_OF = "31.12.2025"  # German form of SH_DATE; the step social_housing checks the year against the report
SH_REPORT_NO = "(B 223/2026)"
# numbers in the rules below; the checks compare them with the report (check_social_housing_protocol)
SH_OUTSIDE_STOCK, SH_HIGHER_INCOME, SH_CONTRACT_ONLY = 362, 4867, 2294


def _fill(t: Texts, key: str) -> str:
    return t.fill(key, year=SH_DATE.year, report_no=SH_REPORT_NO, higher_income=t.number(SH_HIGHER_INCOME, 0),
                  outside_stock=t.number(SH_OUTSIDE_STOCK, 0), contract_only=t.number(SH_CONTRACT_ONLY, 0))


def _sources(t: Texts) -> list[Source]:
    return [Source(title=_fill(t, "sources.report.title"), as_of=t.date(SH_DATE), license=t["sources.report.license"]),
            Source(**t.tree("sources.stock_file"), as_of=t.date(SH_DATE))]


def _indicators(t: Texts) -> list[Indicator]:
    group, end_of = t["core.groups.stock"], _fill(t, "end_of")
    return [
        Indicator("SH_SHARE", t["SH_SHARE.title"], group, "%", QUARTERS_ONLY, _fill(t, "SH_SHARE.source"), end_of, "",
                  "blue", rule=_fill(t, "SH_SHARE.rule"), legend_note=_fill(t, "SH_SHARE.legend_note"),
                  section="stock"),
        Indicator("SH_COUNT", t["SH_COUNT.title"], group, t["units.dwellings"], QUARTERS_ONLY,
                  _fill(t, "SH_COUNT.source"), end_of, t["SH_COUNT.calc"], "blue", 0, layer=False, criterion=False,
                  count_of="SH_SHARE", section="stock"),
    ]


SOURCES: dict[str, list[Source]] = per_language(_sources, T)
INDICATORS: dict[str, list[Indicator]] = per_language(_indicators, T)


# The Stadtteil of the worked example, fixed. The numbers come from the build.
CALC_EXAMPLE_QUARTERS = {"SH_SHARE": "Bonames"}


def social_housing_calc_example(area: str, count: int, dwellings: float, share: float, t: Texts) -> CalcExample:
    """The written sum of the share: the social dwellings divided by all dwellings of the Stadtteil.
    t: the texts of this package (T[lang])."""
    return CalcExample(area, (Row("", count, 0, t["calc_example.count"]),
                              Row("÷", round(dwellings), 0, t["calc_example.dwellings"]),
                              Row("", round(share, 1), 1, t["core.calc_rows.map_value"], total=True, unit="%")))
