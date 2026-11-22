"""Titles and ⓘ of the dwellings by year of construction (texts.<lang>.yaml). Pure module."""
from __future__ import annotations

from pipeline.shared.core.calc_example import CalcExample, Row
from pipeline.shared.core.indicator import BOTH, Indicator, tooltip_rounding, year_of
from pipeline.shared.core.texts import Texts, package_texts, per_language

T: dict[str, Texts] = package_texts(__file__)
CONSTRUCTION_COUNT_STEP = 10  # README: the 2011 grid changes small values for secrecy; the map rounds


def _construction(t: Texts, kid: str) -> list[Indicator]:
    """Share (layer) and count (tooltip) of the dwellings of one class of the year of construction. The Rechnung of
    the share is the worked example alone (README, „Worked example“). The ⓘ of the share explains its count."""
    title, years = t[f"{kid}.title"], t[f"years.{kid}"]
    legend_note = t.fill("legend_note", year_2022=year_of(t["core.z22_as_of"]), year_2011=year_of(t["core.z11_as_of"]))
    rounding = tooltip_rounding(t, "dwellings_phrase", CONSTRUCTION_COUNT_STEP)
    return [Indicator(kid, title, t["core.groups.stock"], "%", BOTH, t["share_source"], t["share_as_of"], "", "orange",
                      rule=t.fill(f"{kid}.rule", rounding=rounding), uncertainty=t["uncertainty"], estimate=True,
                      legend_note=legend_note, section="stock"),
            Indicator(f"{kid}_DWELLINGS", t.fill("count_title", title=title), t["core.groups.stock"],
                      t["units.dwellings"], BOTH, t["source"], t["core.z11_as_of"],
                      t.fill("count_calc", years=years), "orange", 0, layer=False, criterion=False, estimate=True,
                      round_to=CONSTRUCTION_COUNT_STEP, count_of=kid, section="stock")]


def _indicators(t: Texts) -> list[Indicator]:
    return [*_construction(t, "HOU_PRE1919"), *_construction(t, "HOU_1949_1978")]


INDICATORS: dict[str, list[Indicator]] = per_language(_indicators, T)
COUNTS = frozenset(k.id for k in INDICATORS["de"] if not k.criterion)  # counts are no comparison values


# The Stadtteil of each worked example, fixed. The numbers come from the build.
CALC_EXAMPLE_QUARTERS = {"HOU_PRE1919": "Nordend-Ost", "HOU_1949_1978": "Altstadt"}


def construction_calc_example(kid: str, area: str, raw: int, capped: int, dwellings: float, share: float,
                              t: Texts) -> CalcExample:
    """The written sum of a class: the dwellings of 2011, minus those above the dwellings of 2022 per 100-m field,
    divided by all dwellings of 2022. Without a cap (rounded 0) the cap row and the total row go.
    t: the texts of this package (T[lang])."""
    years = t[f"years.{kid}"]
    first = t.fill("calc_example.first", years=years)
    if raw > capped:
        rows = [Row("", raw, 0, first),
                Row("−", raw - capped, 0, t["calc_example.capped"]),
                Row("", capped, 0, t.fill("calc_example.class_total", years=years), total=True, estimate=True)]
    else:
        rows = [Row("", capped, 0, first)]
    rows += [Row("÷", round(dwellings), 0, t["calc_example.all_2022"]),
             Row("", round(share, 1), 1, t["core.calc_rows.map_value"], total=True, estimate=True, unit="%")]
    return CalcExample(area, tuple(rows))
