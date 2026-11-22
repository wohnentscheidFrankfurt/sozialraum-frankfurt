"""Titles and ⓘ of the means of the Zensus grid (texts.<lang>.yaml). Pure module."""
from __future__ import annotations

from pipeline.shared.core.calc_example import CalcExample, Row
from pipeline.shared.core.indicator import BOTH, Indicator, field_mean, tooltip_rounding, year_of
from pipeline.shared.core.texts import Texts, package_texts, per_language

T: dict[str, Texts] = package_texts(__file__)
COUNT_STEP = 10  # the count of the vacancy layers in the map tooltip (README); the ⓘ of each layer explains it


def _vacancy(t: Texts, vid: str, year: str) -> list[Indicator]:
    """Share (layer) and count (tooltip) of the vacant dwellings. The Rechnung of the share is the worked example
    alone (README, „Worked example“)."""
    group, as_of, source = t["core.groups.stock"], t["core.z22_as_of"], t[f"{vid}.source"]
    rounding = tooltip_rounding(t, "vacant_dwellings_phrase", COUNT_STEP)
    return [Indicator(vid, t[f"{vid}.title"], group, "%", BOTH, source, as_of, "", "blue",
                      rule=t.fill("vacancy.rule", rounding=rounding), uncertainty=t["vacancy.uncertainty"],
                      estimate=True, legend_note=t.fill(f"{vid}.legend_note", year=year), section="stock"),
            Indicator(f"{vid}_DWELLINGS", t[f"{vid}.count_title"], group, t["units.vacant_dwellings"], BOTH, source, as_of,
                      t["vacancy.count_calc"], "blue", 0, layer=False, criterion=False, estimate=True,
                      round_to=COUNT_STEP, count_of=vid, section="stock")]


def _indicators(t: Texts) -> list[Indicator]:
    year, rent = year_of(t["core.z22_as_of"]), t["core.groups.rent"]
    return [
        Indicator("HOU_RENTERS", t["HOU_RENTERS.title"], rent, "%", BOTH, t["HOU_RENTERS.source"],
                  t["HOU_RENTERS.as_of"], "", "orange", rule=t["HOU_RENTERS.rule"],
                  uncertainty=t["HOU_RENTERS.uncertainty"], legend_note=t.fill("HOU_RENTERS.legend_note", year=year),
                  section="rent"),
        Indicator("HOU_RENT", t["HOU_RENT.title"], rent, "€/m²", BOTH, t["HOU_RENT.source"], t["HOU_RENT.as_of"],
                  t.fill("HOU_RENT.calc", mean=field_mean(t, "rented_dwellings_phrase")), "orange", 1,
                  uncertainty=t["HOU_RENT.uncertainty"], rule=t["HOU_RENT.rule"],
                  legend_note=t.fill("HOU_RENT.legend_note", year=year), section="rent"),
        *_vacancy(t, "HOU_VACANT_MARKET", year),
        *_vacancy(t, "HOU_VACANT_ALL", year),
    ]


INDICATORS: dict[str, list[Indicator]] = per_language(_indicators, T)
COUNTS = frozenset(k.id for k in INDICATORS["de"] if not k.criterion)  # counts are no comparison values


# The Stadtteil of each worked example: the one with the highest share. The numbers come from the build.
CALC_EXAMPLE_QUARTERS = {"HOU_VACANT_ALL": "Innenstadt", "HOU_VACANT_MARKET": "Bahnhofsviertel",
                         "HOU_RENTERS": "Riederwald"}


def _result(share: float, estimate: bool, t: Texts) -> Row:
    return Row("", round(share, 1), 1, t["core.calc_rows.map_value"], total=True, estimate=estimate, unit="%")


def vacancy_calc_example(vid: str, area: str, fields: float, km: float, dwellings: float, share: float,
                         t: Texts) -> CalcExample:
    """The written sum of a vacancy rate: vacant dwellings of the 100 m fields plus those the 1 km grid adds, divided
    by the dwellings. Without a 1 km part (rounded 0) the first row is the rounded total, the count of the tooltip.
    t: the texts of this package (T[lang])."""
    word = t[f"calc_example.vacant.{vid}"]
    if round(km) > 0:
        rows = [Row("", round(fields), 0, t["calc_example.in_fields"], estimate=True),
                Row("+", round(km), 0, t["calc_example.from_km"], estimate=True),
                Row("", round(fields + km), 0, word, total=True, estimate=True)]
    else:
        rows = [Row("", round(fields + km), 0, word, estimate=True)]
    rows += [Row("÷", round(dwellings), 0, t["core.calc_rows.all_dwellings"]), _result(share, True, t)]
    return CalcExample(area, tuple(rows))


def renters_calc_example(area: str, occupied: float, owners: float, share: float, t: Texts) -> CalcExample:
    """The written sum of the renters: occupied dwellings minus the owner-occupied ones, divided by the occupied.
    t: the texts of this package (T[lang])."""
    return CalcExample(area, (Row("", round(occupied), 0, t["calc_example.occupied"], estimate=True),
                              Row("−", round(owners), 0, t["calc_example.owner_occupied"], estimate=True),
                              Row("", round(occupied - owners), 0, t["calc_example.not_owner_occupied"],
                                  total=True, estimate=True),
                              Row("÷", round(occupied), 0, t["calc_example.occupied"], estimate=True),
                              _result(share, False, t)))
