"""Titles and ⓘ of land values and pending plans, and the ⓘ of their overlays (texts.<lang>.yaml). Pure module."""
from __future__ import annotations

import datetime

from pipeline.shared.core.indicator import BOTH, Indicator, Source
from pipeline.shared.core.texts import Texts, package_texts, per_language

T: dict[str, Texts] = package_texts(__file__)
BORIS_AS_OF = "1.1.2026"  # the date in German form (html cover note, test); the texts write BORIS_DATE per language
BORIS_DATE = datetime.date(2026, 1, 1)


def _values(t: Texts) -> dict[str, str]:
    return {"boris_as_of": t.date(BORIS_DATE), "boris_year": str(BORIS_DATE.year)}


def _sources(t: Texts) -> list[Source]:
    return [Source(**{k: t.fill(f"sources.boris.{k}", **_values(t)) for k in ("title", "as_of", "license")})]


def _indicators(t: Texts) -> list[Indicator]:
    v = _values(t)
    return [
        Indicator("LAND_VALUE", t["LAND_VALUE.title"], t["core.groups.land"], "€/m²", BOTH, t["LAND_VALUE.source"],
                  t.fill("LAND_VALUE.as_of", **v), t["LAND_VALUE.calc"], "orange", 0, rule=t["LAND_VALUE.rule"],
                  legend_note=t.fill("LAND_VALUE.legend_note", **v), section="land"),
        Indicator("LAND_PENDING_PLAN", t["LAND_PENDING_PLAN.title"], t["core.groups.planning"], "", BOTH,
                  t["LAND_PENDING_PLAN.source"], t["LAND_PENDING_PLAN.as_of"], t["LAND_PENDING_PLAN.calc"],
                  layer=False, type="yes_no", rule=t["LAND_PENDING_PLAN.rule"], section="planning"),
    ]


def _overlays(t: Texts) -> dict[str, dict]:
    v = _values(t)
    return {name: {f: t.fill(f"overlays.{name}.{f}", **v) for f in t.tree(f"overlays.{name}")}
            for name in ("pending_plans", "land_value")}


SOURCES: dict[str, list[Source]] = per_language(_sources, T)
INDICATORS: dict[str, list[Indicator]] = per_language(_indicators, T)
OVERLAYS: dict[str, dict[str, dict]] = per_language(_overlays, T)
# BORIS use codes of the overlay and building types, spelled out for the tooltip
USE_NAMES: dict[str, dict[str, str]] = per_language(lambda t: t.tree("use_names"), T)
BUILDING_NAMES: dict[str, dict[str, str]] = per_language(lambda t: t.tree("building_names"), T)


def use_name(code: str, building: str, t: Texts) -> str:
    """„Mischgebiet, Mehrfamilienhäuser“: the area, then the building type where the zone has one (a code we do not
    know stays as it is)."""
    uses, buildings = USE_NAMES[t.lang], BUILDING_NAMES[t.lang]
    return ", ".join(x for x in (uses.get(code, code), buildings.get(building, building)) if x)
