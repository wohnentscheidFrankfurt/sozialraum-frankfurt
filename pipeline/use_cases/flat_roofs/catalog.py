"""Title, ⓘ, overlay texts and the worked sum of the low flat roofs (texts.<lang>.yaml). Pure module."""
from __future__ import annotations

import datetime
import math

from pipeline.shared.core.calc_example import CalcExample, Row
from pipeline.shared.core.indicator import BOTH, Indicator, Source
from pipeline.shared.core.texts import Texts, package_texts, per_language
from pipeline.use_cases.flat_roofs.model import (HEIGHT_MAX_M, HEIGHT_MIN_M, MIN_ROOF_M2, MODULE_M2, MODULE_SHARE,
                                                 TALLER_BY_M, VERY_LOW_M, WALL_GAP_M, Roof)

T: dict[str, Texts] = package_texts(__file__)
# The dates in German form: the checks compare them with the sources; the texts write the dates per language.
LOD2_AS_OF = "26.6.2026"  # delivery of the building model; the check compares it with the gemarkung table
LOD2_DATE = datetime.date(2026, 6, 26)
LOD2_CREATED_YEAR = "2020"  # the year most footprints were captured in (Unsicherheit; the check compares it)
BORIS_ZONES_AS_OF = "1.1.2024"  # the zones are those of the WFS 2024 (land README)
BORIS_ZONES_DATE = datetime.date(2024, 1, 1)
MODULES_STEP = 100  # the module estimate of the written sum is rounded half up to this step


def _number(x: float, t: Texts) -> str:
    """A length or an area for a text: whole number if it is one, else one decimal."""
    return t.number(x, 0 if float(x).is_integer() else 1)


def _values(t: Texts) -> dict[str, str]:
    return {"min_roof": _number(MIN_ROOF_M2, t), "height_min": _number(HEIGHT_MIN_M, t),
            "height_max": _number(HEIGHT_MAX_M, t), "module": _number(MODULE_M2, t),
            "very_low": _number(VERY_LOW_M, t), "taller_by": _number(TALLER_BY_M, t),
            "wall_gap": _number(WALL_GAP_M, t), "created_year": LOD2_CREATED_YEAR,
            "lod2_as_of": t.date(LOD2_DATE), "zones_as_of": t.date(BORIS_ZONES_DATE)}


def _indicators(t: Texts) -> list[Indicator]:
    v = _values(t)
    return [Indicator("ROOF_FLAT", t["ROOF_FLAT.title"], t["core.groups.land"], "m²", BOTH, t["ROOF_FLAT.source"],
                      t.fill("ROOF_FLAT.as_of", **v), t.fill("ROOF_FLAT.calc", **v), "color:#8a5a2b", 0,
                      rule=t.fill("ROOF_FLAT.rule", **v), uncertainty=t.fill("ROOF_FLAT.uncertainty", **v),
                      legend_note=t["ROOF_FLAT.legend_note"], section="land")]


def _sources(t: Texts) -> list[Source]:
    return [Source(**{k: t.fill(f"sources.lod2.{k}", **_values(t)) for k in ("title", "as_of", "license")})]


def _overlays(t: Texts) -> dict[str, dict]:
    v = _values(t)
    return {"flat_roofs": {f: t.fill(f"overlays.flat_roofs.{f}", **v) for f in t.tree("overlays.flat_roofs")}}


INDICATORS: dict[str, list[Indicator]] = per_language(_indicators, T)
SOURCES: dict[str, list[Source]] = per_language(_sources, T)
# The overlay: title in the list, the two key rows, tip before the values in the tooltip, result protocol of the ⓘ
OVERLAYS: dict[str, dict[str, dict]] = per_language(_overlays, T)
# Why a roof does not count, after „Zählt nicht:“ in its tooltip (Roof.reason)
NOT_COUNTED: dict[str, dict[str, str]] = per_language(
    lambda t: {k: t.fill(f"not_counted.{k}", **_values(t)) for k in t.tree("not_counted")}, T)


def _height_down(height_m: float, t: Texts) -> str:
    """A height rounded down to 0.1 m, so it never reads as a threshold it misses (3,17 m reads 3,1, not 3,2). The
    epsilon keeps 6.4 at 6,4 against float noise."""
    return t.number(math.floor(height_m * 10 + 1e-6) / 10, 1)


def roof_text(r: Roof, t: Texts) -> str:
    """The tooltip of a roof after the tip: area, height, function, and why it does not count or, for a counted roof,
    the strip in front of a taller wall. t: the texts of this package (T[lang])."""
    names = t.tree("function_names")
    text = t.fill("roof_tip", area=t.number(r.area_m2, 0), height=_height_down(r.height_m, t),
                  use_name=names.get(r.use, t["function_default"]))
    if r.reason:
        return t.fill("roof_not_counted", tip=text, reason=NOT_COUNTED[t.lang][r.reason])
    if round(r.wall_m2) >= 1:
        return t.fill("roof_wall", tip=text, wall=t.number(r.wall_m2, 0))
    return text


def funnel_calc_example(f: dict[str, float], t: Texts) -> CalcExample:
    """The funnel of the city as a written sum, ending in the module estimate (rounded to MODULES_STEP). A row that
    rounds to 0 goes. t: the texts of this package (T[lang])."""
    v = _values(t)
    modules = MODULES_STEP * math.floor(f["modules"] / MODULES_STEP + 0.5)
    rows = [Row("", round(f["candidates_m2"]), 0, t.fill("calc_example.candidates", **v)),
            Row("−", round(f["not_housing_m2"]), 0, t["calc_example.not_housing"]),
            Row("−", round(f["very_low_m2"]), 0, t.fill("calc_example.very_low", **v)),
            Row("−", round(f["wall_m2"]), 0, t["calc_example.wall"]),
            Row("", round(f["counted_m2"]), 0, t["calc_example.counted"], total=True),
            Row("×", MODULE_SHARE, 1, t["calc_example.module_share"]),
            Row("÷", round(MODULE_M2), 0, t["calc_example.per_module"]),
            Row("", modules, 0, t["calc_example.modules"], total=True, estimate=True)]
    return CalcExample(t["calc_example.area"], tuple(r for r in rows if r.number != 0), t["calc_example.label"])
