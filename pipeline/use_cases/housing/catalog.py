"""Titles and ⓘ of the means of the Zensus grid. Pure module."""
from __future__ import annotations

from pipeline.shared.core.calc_example import CalcExample, Row
from pipeline.shared.core.indicator import (BOTH, DASH_MEANING, FIELD_EDGE, Z22, Z22_AS_OF, Indicator, field_mean,
                                            tooltip_rounding, year_of)

Z22_YEAR = year_of(Z22_AS_OF)
VACANCY_RULE = (f"{DASH_MEANING} Die Karte verteilt die leeren Wohnungen, die das 1-km-Gitter mehr zählt, auf diese "
                "Felder.")
FIELD_UNSURE = f"{FIELD_EDGE} Viele Feldwerte nennt der Zensus selbst unsicher."
# The count of the vacancy layers in the map tooltip (README); the ⓘ of each layer explains it
COUNT_STEP = 10
VACANCY_ROUNDING = tooltip_rounding("leer stehenden Wohnungen", COUNT_STEP)
VACANCY_UNCERTAINTY_COUNT = "Die leer stehenden Wohnungen im Tooltip können so stark abweichen wie der Anteil."
Z22_VACANCY = "Zensus 2022, 100-m- und 1-km-Gitter"



def _vacancy(vid: str, title: str, source: str, legend_note: str, count_title: str) -> list[Indicator]:
    """Share (layer) and count (tooltip) of the vacant dwellings. The Rechnung of the share is the worked example
    alone (README, „Worked example“)."""
    group = "Wohnungsbestand"
    return [Indicator(vid, title, group, "%", BOTH, source, Z22_AS_OF, "", "blue",
                      rule=f"{VACANCY_RULE} {VACANCY_ROUNDING}", uncertainty=f"{FIELD_UNSURE} {VACANCY_UNCERTAINTY_COUNT}",
                      estimate=True, legend_note=legend_note, section="stock"),
            Indicator(f"{vid}_DWELLINGS", count_title, group, "Leer stehende Wohnungen", BOTH, source, Z22_AS_OF,
                      "Quote je Feld mal seine Wohnungen, zusammengezählt.", "blue", 0, layer=False, criterion=False,
                      estimate=True, round_to=COUNT_STEP, count_of=vid, section="stock")]


INDICATORS: list[Indicator] = [
    Indicator("HOU_RENTERS", "Mieteranteil", "Miete", "%", BOTH, Z22 + ", Eigentümerquote", Z22_AS_OF,
              "", "orange",
              rule=f"{DASH_MEANING} Die Karte setzt die Eigentümerquote dann auf 0 %.",
              uncertainty=FIELD_UNSURE,
              legend_note=f"Anteil der bewohnten Wohnungen, die nicht von ihren Eigentümer*innen bewohnt werden, {Z22_YEAR}",
              section="rent"),
    Indicator("HOU_RENT", "Miete im Bestand", "Miete", "€/m²", BOTH, Z22 + ", Nettokaltmiete",
              Z22_AS_OF, f"Nettokaltmiete je m². {field_mean('vermieteten Wohnungen')}", "orange", 1,
              uncertainty=FIELD_EDGE,
              rule="Es zählen laufende Mietverträge, nicht Neuvermietungen. Felder ohne Wert („–“) zählen nicht.",
              legend_note=f"Nettokaltmiete je m² im Durchschnitt aller Mietverträge, {Z22_YEAR}", section="rent"),
    *_vacancy("HOU_VACANT_MARKET", "Leerstand (marktaktiv)", Z22_VACANCY + ", marktaktive Leerstandsquote",
              f"Anteil leerer, binnen 3 Monaten verfügbarer Wohnungen in Wohngebäuden, {Z22_YEAR}",
              "Leerstand (marktaktiv), Wohnungen"),
    *_vacancy("HOU_VACANT_ALL", "Leerstand insgesamt", Z22_VACANCY + ", Leerstandsquote",
              f"Anteil leerer Wohnungen in Wohngebäuden, {Z22_YEAR}", "Leerstand insgesamt, Wohnungen"),
]
COUNTS = frozenset(k.id for k in INDICATORS if not k.criterion)  # counts are no comparison values


# The Stadtteil of each worked example: the one with the highest share. The numbers come from the build.
CALC_EXAMPLE_QUARTERS = {"HOU_VACANT_ALL": "Innenstadt", "HOU_VACANT_MARKET": "Bahnhofsviertel",
                         "HOU_RENTERS": "Riederwald"}
VACANT_WORDS = {"HOU_VACANT_ALL": "leer stehende Wohnungen",
                "HOU_VACANT_MARKET": "leer stehende Wohnungen, binnen drei Monaten verfügbar"}
OCCUPIED = "bewohnte Wohnungen"


def _result(share: float, estimate: bool) -> Row:
    return Row("", round(share, 1), 1, "Wert auf der Karte", total=True, estimate=estimate, unit="%")


def vacancy_calc_example(vid: str, area: str, fields: float, km: float, dwellings: float, share: float) -> CalcExample:
    """The written sum of a vacancy rate: vacant dwellings of the 100 m fields plus those the 1 km grid adds, divided
    by the dwellings. Without a 1 km part (rounded 0) the first row is the rounded total, the count of the tooltip."""
    word = VACANT_WORDS[vid]
    if round(km) > 0:
        rows = [Row("", round(fields), 0, "in den 100-m-Feldern", estimate=True),
                Row("+", round(km), 0, "aus dem 1-km-Gitter, verteilt auf Felder mit „–“", estimate=True),
                Row("", round(fields + km), 0, word, total=True, estimate=True)]
    else:
        rows = [Row("", round(fields + km), 0, word, estimate=True)]
    rows += [Row("÷", round(dwellings), 0, "alle Wohnungen"), _result(share, True)]
    return CalcExample(area, tuple(rows))


def renters_calc_example(area: str, occupied: float, owners: float, share: float) -> CalcExample:
    """The written sum of the renters: occupied dwellings minus the owner-occupied ones, divided by the occupied."""
    return CalcExample(area, (Row("", round(occupied), 0, OCCUPIED, estimate=True),
                              Row("−", round(owners), 0, "von ihren Eigentümer*innen bewohnt", estimate=True),
                              Row("", round(occupied - owners), 0, "nicht von ihren Eigentümer*innen bewohnt",
                                  total=True, estimate=True),
                              Row("÷", round(occupied), 0, OCCUPIED, estimate=True),
                              _result(share, False)))
