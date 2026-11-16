"""Titles and ⓘ of ABG and Nassauische Heimstätte. Pure module."""
from __future__ import annotations

from pipeline.shared.core import palette
from pipeline.shared.core.calc_example import CalcExample, Row
from pipeline.shared.core.indicator import (QUARTERS_ONLY, QUARTERS_RULE, TIP_DWELLINGS_RULE, TIP_DWELLINGS_UNCERTAINTY, Z11_AS_OF, Z22_AS_OF,
                                             Indicator, Source, estimate_range)
from pipeline.use_cases.ownership_cells.catalog import OWN_LEGEND_NOTE

# ABG and Nassauische Heimstätte per Stadtteil: count of 2011 × change up to 2022
# (README)
PUBLIC_SOURCE = ("Zensus 2011 und 2022, 100-m-Gitter; Tabellen 4000W-1011, 3000G-2007, 4000W-2013 · ABG-Neubauten bis "
                 "2021: eigene Recherche")
PUBLIC_AS_OF = f"{Z22_AS_OF} · Basis {Z11_AS_OF}"
# every dwelling the Zensus 2022 counts as municipal goes to ABG and Nassauische Heimstätte (public_housing/model.py:
# quarter table, "public" = abg + nh + new)
PUBLIC_COUNTING_RULE = ("Die Karte zählt alle Wohnungen, die der Zensus als kommunal führt, zu ABG und Nassauische "
                        "Heimstätte.")
# 72 % of the summed half ranges come from the unfilled secrecy gap 2011 (README, Limits)
PUBLIC_CAUSE = ("Die Abweichung kommt vor allem daher, dass der Zensus 2011 einen Teil der Wohnungen aus "
                "Datenschutzgründen keiner Eigentumsform zuordnet.")

ABG_NEW_BUILDINGS = Source("ABG-Neubauten: eigene Recherche aus öffentlichen Quellen", "8.10.2026",
                           "Quellen in der Recherche")
SOURCES = [ABG_NEW_BUILDINGS]

INDICATORS: list[Indicator] = [
    Indicator("OWN_PUBLIC", "ABG und Nassauische Heimstätte", "Eigentum", "%", QUARTERS_ONLY, PUBLIC_SOURCE,
              PUBLIC_AS_OF, "", f"color:{palette.PUBLIC}",
              rule=f"{QUARTERS_RULE} {PUBLIC_COUNTING_RULE} {TIP_DWELLINGS_RULE}",
              uncertainty=f"{estimate_range('OWN_PUBLIC')} {PUBLIC_CAUSE} {TIP_DWELLINGS_UNCERTAINTY}", estimate=True,
              color=palette.PUBLIC, legend_note=OWN_LEGEND_NOTE, section="ownership"),
]


def public_calc_example(area: str, row: dict, total: float, share: float) -> CalcExample:
    """The written sum of ABG und NH: the count of 2011 the factor scales × the factor of the change, + the dwellings of
    2011 without owner in 2022, + the new sites, ÷ all dwellings.

    The row of 2011 without owner is the value of the build minus the other rows, so it also holds the secrecy gap of
    2011 and the rounding."""
    scaled, value = round(row["abg_scaled"] + row["nh_scaled"]), round(row["public_value"])
    new = round(row["new"] + row["research_new"])
    return CalcExample(area, (
        Row("", round(row["scaled_2011"]), 0,
            "Wohnungen von ABG und Nassauischer Heimstätte 2011, deren Eigentumsform der Zensus 2022 nennt", estimate=True),
        Row("×", round(row["factor"], 2), 2, "Veränderung der Gebäude bis 2022 im Stadtteil"),
        Row("", scaled, 0, "", total=True, estimate=True),
        Row("+", value - scaled - new, 0,
            "Wohnungen von ABG und Nassauischer Heimstätte 2011 an Orten, für die der Zensus 2022 keine "
            "Eigentumsform nennt",
            estimate=True),
        Row("+", new, 0, "Wohnungen an neuen Standorten seit 2011", estimate=True),
        Row("", value, 0, "Wohnungen 2022", total=True, estimate=True),
        Row("÷", round(total), 0, "alle Wohnungen"),
        Row("", round(share, 1), 1, "Wert auf der Karte", total=True, estimate=True, unit="%")))
