"""Titles and ⓘ of the dwellings by year of construction. Pure module."""
from __future__ import annotations

from pipeline.shared.core.calc_example import CalcExample, Row
from pipeline.shared.core.indicator import (BOTH, FIELD_EDGE, FIELD_SUM, Z11_AS_OF, Z22, Z22_AS_OF, Indicator,
                                            tooltip_rounding, year_of)

# Dwellings by year of construction (README): the class in 2011, capped per cell at the dwellings of 2022 (count),
# and its share of the dwellings in 2022 (both are estimates).
CONSTRUCTION_SOURCE = "Zensus 2011, 100-m-Gitter, Wohnungen nach Baujahr"
CONSTRUCTION_SHARE_SOURCE = CONSTRUCTION_SOURCE + " · " + Z22 + ", Wohnungen"
CONSTRUCTION_AS_OF = Z11_AS_OF
CONSTRUCTION_SHARE_AS_OF = CONSTRUCTION_AS_OF + " · " + Z22_AS_OF
SHARE_LEGEND_NOTE = (f"Anteil an allen Wohnungen {year_of(Z22_AS_OF)}, geschätzt aus dem Baujahr laut Zensus "
                     f"{year_of(Z11_AS_OF)}")
CONSTRUCTION_RULE = ("Felder ohne Wohnungen 2022 zählen nicht. Nach völliger Zerstörung zählt das Jahr des "
                     "Wiederaufbaus.")
CONSTRUCTION_UNCERTAINTY = f"Neue Wohnungen in alten Gebäuden seit 2011 fehlen. {FIELD_EDGE}"
CONSTRUCTION_COUNT_STEP = 10  # README: the 2011 grid changes small values for secrecy; the map rounds
# the ⓘ of the share explains its count in the tooltip
CONSTRUCTION_COUNT_ROUNDING = tooltip_rounding("Wohnungen", CONSTRUCTION_COUNT_STEP)


def _construction(kid: str, title: str, years: str, extra_rule: str = "") -> list[Indicator]:
    """Share (layer) and count (tooltip) of the dwellings of one class of the year of construction. The Rechnung of
    the share is the worked example alone (README, „Worked example“)."""
    group = "Wohnungsbestand"
    rule = CONSTRUCTION_RULE + (f" {extra_rule}" if extra_rule else "") + f" {CONSTRUCTION_COUNT_ROUNDING}"
    calc = (f"Wohnungen in Gebäuden mit Baujahr {years} laut Zensus 2011, je Feld höchstens so viele wie 2022 dort "
            f"stehen")
    return [Indicator(kid, title, group, "%", BOTH, CONSTRUCTION_SHARE_SOURCE, CONSTRUCTION_SHARE_AS_OF,
                      "", "orange", rule=rule,
                      uncertainty=CONSTRUCTION_UNCERTAINTY, estimate=True, legend_note=SHARE_LEGEND_NOTE,
                      section="stock"),
            Indicator(f"{kid}_DWELLINGS", f"{title}, Wohnungen", group, "Wohnungen", BOTH, CONSTRUCTION_SOURCE,
                      CONSTRUCTION_AS_OF, f"{calc}. {FIELD_SUM}", "orange", 0, layer=False, criterion=False,
                      estimate=True, round_to=CONSTRUCTION_COUNT_STEP, count_of=kid, section="stock")]


INDICATORS: list[Indicator] = [
    *_construction("HOU_PRE1919", "Altbau vor 1919", "vor 1919", "Bauten vor 1870 zählen mit."),
    *_construction("HOU_1949_1978", "Nachkriegsbau 1949–1978", "1949 bis 1978"),
]
COUNTS = frozenset(k.id for k in INDICATORS if not k.criterion)  # counts are no comparison values


# The Stadtteil of each worked example, fixed. The numbers come from the build.
CALC_EXAMPLE_QUARTERS = {"HOU_PRE1919": "Nordend-Ost", "HOU_1949_1978": "Altstadt"}
YEARS = {"HOU_PRE1919": "vor 1919", "HOU_1949_1978": "1949 bis 1978"}


def construction_calc_example(kid: str, area: str, raw: int, capped: int, dwellings: float,
                              share: float) -> CalcExample:
    """The written sum of a class: the dwellings of 2011, minus those above the dwellings of 2022 per 100-m field,
    divided by all dwellings of 2022. Without a cap (rounded 0) the cap row and the total row go."""
    years = YEARS[kid]
    first = f"Wohnungen in Gebäuden mit Baujahr {years}, Zensus 2011"
    if raw > capped:
        rows = [Row("", raw, 0, first),
                Row("−", raw - capped, 0, "mehr Wohnungen, als 2022 im selben 100-m-Feld stehen"),
                Row("", capped, 0, f"Wohnungen in Gebäuden mit Baujahr {years}", total=True, estimate=True)]
    else:
        rows = [Row("", capped, 0, first)]
    rows += [Row("÷", round(dwellings), 0, "alle Wohnungen 2022"),
             Row("", round(share, 1), 1, "Wert auf der Karte", total=True, estimate=True, unit="%")]
    return CalcExample(area, tuple(rows))
