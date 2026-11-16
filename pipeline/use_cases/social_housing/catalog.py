"""Titles and ⓘ of the social housing indicators; the step checks SH_AS_OF against the report. Pure module."""
from __future__ import annotations

from pipeline.shared.core.calc_example import CalcExample, Row
from pipeline.shared.core.checks import de_thousands
from pipeline.shared.core.indicator import QUARTERS_ONLY, QUARTERS_RULE, Indicator, Source, year_of

SH_AS_OF = "31.12.2025"  # the step social_housing checks the year against the report
SH_SOURCE = f"Amt für Wohnungswesen, Jahresbericht Kommunale Wohnraumversorgung {SH_AS_OF[-4:]}"
SH_REPORT_NO = "(B 223/2026)"
# numbers in the rules below; the checks compare them with the report (check_social_housing_protocol)
SH_OUTSIDE_STOCK, SH_HIGHER_INCOME, SH_CONTRACT_ONLY = 362, 4867, 2294
SOURCES = [Source(f"Jahresbericht Kommunale Wohnraumversorgung {year_of(SH_AS_OF)} (Amt für Wohnungswesen)", SH_AS_OF,
                  "Stadt Frankfurt am Main"),
           Source("Statistikportal Frankfurt, Wohnungsbestand und Räume (Statistische Gebäudedatei)", SH_AS_OF,
                  "dl-de/by-2-0, Stadt Frankfurt am Main")]
SH_END_OF = f"Ende {year_of(SH_AS_OF)}"  # as-of date as the map shows it

INDICATORS: list[Indicator] = [
    Indicator("SH_SHARE", "Sozialwohnungen", "Wohnungsbestand", "%", QUARTERS_ONLY,
              f"{SH_SOURCE}, Tabelle 1.2 {SH_REPORT_NO} · Statistikportal Frankfurt, Wohnungsbestand (Gebäudedatei)",
              SH_END_OF, "", "blue",
              rule=f"{QUARTERS_RULE} Ab 2025 zählen nur tatsächlich geförderte Wohnungen. Die "
                   f"{de_thousands(SH_HIGHER_INCOME)} geförderten Wohnungen für höhere Einkommen zählen nicht. "
                   f"{SH_OUTSIDE_STOCK} Sozialwohnungen außerhalb Frankfurts zählen ebenfalls nicht. "
                   f"{de_thousands(SH_CONTRACT_ONLY)} nur vertraglich gesicherte Wohnungen zählen nicht.",
                   legend_note=f"Anteil an allen Wohnungen, {SH_END_OF}", section="stock"),
    Indicator("SH_COUNT", "Sozialwohnungen, Anzahl", "Wohnungsbestand", "Wohnungen", QUARTERS_ONLY,
              f"{SH_SOURCE}, Tabelle 1.2 {SH_REPORT_NO}", SH_END_OF, "Sozialwohnungen im Stadtteil", "blue", 0,
              layer=False, criterion=False, count_of="SH_SHARE", section="stock"),  # a tooltip line of the share, no rule
]


# The Stadtteil of the worked example, fixed. The numbers come from the build.
CALC_EXAMPLE_QUARTERS = {"SH_SHARE": "Bonames"}


def social_housing_calc_example(area: str, count: int, dwellings: float, share: float) -> CalcExample:
    """The written sum of the share: the social dwellings divided by all dwellings of the Stadtteil."""
    return CalcExample(area, (Row("", count, 0, "Sozialwohnungen"),
                              Row("÷", round(dwellings), 0, "Wohnungen im Stadtteil, mit Wohnheimen"),
                              Row("", round(share, 1), 1, "Wert auf der Karte", total=True, unit="%")))
