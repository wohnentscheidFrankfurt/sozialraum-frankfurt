"""Titles and ⓘ of ABG and Nassauische Heimstätte (texts.<lang>.yaml). Pure module."""
from __future__ import annotations

from pipeline.shared.core import palette
from pipeline.shared.core.calc_example import CalcExample, Row
from pipeline.shared.core.indicator import QUARTERS_ONLY, Indicator, Source, estimate_range
from pipeline.shared.core.texts import Texts, package_texts, per_language
from pipeline.use_cases.ownership_cells.catalog import OWN_LEGEND_NOTE

T: dict[str, Texts] = package_texts(__file__)

ABG_NEW_BUILDINGS: dict[str, Source] = per_language(lambda t: Source(**t.tree("sources.abg_new_buildings")), T)
SOURCES: dict[str, list[Source]] = per_language(lambda t: [ABG_NEW_BUILDINGS[t.lang]], T)


def _indicators(t: Texts) -> list[Indicator]:
    return [
        Indicator("OWN_PUBLIC", t["OWN_PUBLIC.title"], t["core.groups.ownership"], "%", QUARTERS_ONLY,
                  t["OWN_PUBLIC.source"], t["OWN_PUBLIC.as_of"], "", f"color:{palette.PUBLIC}",
                  rule=t["OWN_PUBLIC.rule"],
                  uncertainty=t.fill("OWN_PUBLIC.uncertainty", estimate=estimate_range(t, "OWN_PUBLIC")),
                  estimate=True, color=palette.PUBLIC, legend_note=OWN_LEGEND_NOTE[t.lang], section="ownership"),
    ]


INDICATORS: dict[str, list[Indicator]] = per_language(_indicators, T)


def public_calc_example(area: str, row: dict, total: float, share: float, t: Texts) -> CalcExample:
    """The written sum of ABG und NH: the count of 2011 the factor scales × the factor of the change, + the dwellings of
    2011 without owner in 2022, + the new sites, ÷ all dwellings. t: the texts of this package (T[lang]).

    The row of 2011 without owner is the value of the build minus the other rows, so it also holds the secrecy gap of
    2011 and the rounding."""
    scaled, value = round(row["abg_scaled"] + row["nh_scaled"]), round(row["public_value"])
    new = round(row["new"] + row["research_new"])
    return CalcExample(area, (
        Row("", round(row["scaled_2011"]), 0, t["calc_example.scaled_2011"], estimate=True),
        Row("×", round(row["factor"], 2), 2, t["calc_example.factor"]),
        Row("", scaled, 0, "", total=True, estimate=True),
        Row("+", value - scaled - new, 0, t["calc_example.no_owner_2022"], estimate=True),
        Row("+", new, 0, t["calc_example.new"], estimate=True),
        Row("", value, 0, t["calc_example.value"], total=True, estimate=True),
        Row("÷", round(total), 0, t["core.calc_rows.all_dwellings"]),
        Row("", round(share, 1), 1, t["core.calc_rows.map_value"], total=True, estimate=True, unit="%")))
