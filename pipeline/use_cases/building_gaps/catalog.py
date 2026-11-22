"""Title, ⓘ, overlay texts, tooltip and worked sum of the building gaps (Baulücken; texts.<lang>.yaml). Pure module."""
from __future__ import annotations

import datetime
import math

from pipeline.shared.core.calc_example import CalcExample, Row
from pipeline.shared.core.indicator import BOTH, Indicator, Source
from pipeline.shared.core.texts import Texts, package_texts, per_language
from pipeline.use_cases.building_gaps.model import (BUILDING_MAX, BUILT_MAX_M2, BUILT_MAX_SHARE, FREE_FRONT_M,
                                                    HALF_WIDTH_M, HOUSING_SHARE_MIN, MIN_AREA_M2, MIN_FRONT_M,
                                                    WALL_MIN_M, Candidate, suitability)

T: dict[str, Texts] = package_texts(__file__)
# The dates in German form: the checks compare them with the sources; the texts write the dates per language.
ALKIS_AS_OF = "4.11.2026"  # delivery of the ALKIS extract; the check compares it with the portion date of the NAS
ALKIS_DATE = datetime.date(2026, 11, 4)
DOM_YEAR = "2023"  # flight of the height models DOM1 and DGM1
DOP_AS_OF = "19.8.2025"  # flight of the orthophoto of most candidates; the check compares it with the cover extract
DOP_DATE = datetime.date(2025, 8, 19)
BORIS_ZONES_AS_OF = "1.1.2024"  # the zones are those of the WFS 2024 (land README)
BORIS_ZONES_DATE = datetime.date(2024, 1, 1)
COLOUR = "#c51b7d"  # magenta of the layer; the overlay in web/js uses the same tone
HOUSE_FOR_ALL_URL = "https://gemeinwohlbau.de/idee"


def _values(t: Texts) -> dict[str, str]:
    return {"built_share": t.number(BUILT_MAX_SHARE * 100, 0, "%"), "built_m2": t.number(BUILT_MAX_M2, 0),
            "min_area": t.number(MIN_AREA_M2, 0), "width": t.number(2 * HALF_WIDTH_M, 0),
            "housing_share": t.number(HOUSING_SHARE_MIN * 100, 0, "%"), "min_front": t.number(MIN_FRONT_M, 0),
            "wall_min": t.number(WALL_MIN_M, 0), "free_front": t.number(FREE_FRONT_M, 0),
            "building_max": t.number(BUILDING_MAX * 100, 0, "%"), "alkis_as_of": t.date(ALKIS_DATE),
            "alkis_year": str(ALKIS_DATE.year), "dom_year": DOM_YEAR, "dop_as_of": t.date(DOP_DATE),
            "zones_as_of": t.date(BORIS_ZONES_DATE)}


def _indicators(t: Texts) -> list[Indicator]:
    v = _values(t)
    return [Indicator("GAP_AREA", t["GAP_AREA.title"], t["core.groups.land"], "m²", BOTH, t["GAP_AREA.source"],
                      t.fill("GAP_AREA.as_of", **v), t["GAP_AREA.calc"], f"color:{COLOUR}", 0,
                      rule=t.fill("GAP_AREA.rule", **v), uncertainty=t.fill("GAP_AREA.uncertainty", **v),
                      legend_note=t.fill("GAP_AREA.legend_note", **v), section="land")]


def _sources(t: Texts) -> list[Source]:
    v = _values(t)
    fields = ("title", "as_of", "license")
    return [Source(**{k: t.fill(f"sources.{name}.{k}", **v) for k in fields}, **extra)
            for name, extra in (("data", {}), ("examples", {}), ("house_for_all", {"url": HOUSE_FOR_ALL_URL}))]


def _overlays(t: Texts) -> dict[str, dict]:
    v = _values(t)
    return {"building_gaps": {f: t.fill(f"overlays.building_gaps.{f}", **v) for f in t.tree("overlays.building_gaps")}}


INDICATORS: dict[str, list[Indicator]] = per_language(_indicators, T)
SOURCES: dict[str, list[Source]] = per_language(_sources, T)
# The overlay: title in the list, one key row, tip before the text in the tooltip and the result protocol of the ⓘ
OVERLAYS: dict[str, dict[str, dict]] = per_language(_overlays, T)
# The kind of sealed or open land of a counted gap (model.COUNT_REASONS)
COUNT_TEXT: dict[str, dict[str, str]] = per_language(lambda t: t.tree("count_text"), T)
KIND_TEXT: dict[str, dict[str, str]] = per_language(lambda t: t.tree("kind_text"), T)
# What a counted gap could carry, keyed like model.SUITABILITY; reference/building_gaps_examples.csv holds the sources
SUITABILITY_TEXT: dict[str, dict[str, str]] = per_language(lambda t: t.tree("suitability_text"), T)
SITE_TEXT: dict[str, str] = per_language(lambda t: t["site_text"], T)


def iso_date(iso: str) -> datetime.date | None:
    """'2025-08-19' gives the date; anything else gives None."""
    parts = iso[:10].split("-")
    if len(parts) != 3 or not all(p.isdigit() for p in parts):
        return None
    return datetime.date(int(parts[0]), int(parts[1]), int(parts[2]))


def german_date(iso: str) -> str:
    """'2025-08-19' gives '19.8.2025'; anything else gives "". The checks compare it with the German dates."""
    day = iso_date(iso)
    return f"{day.day}.{day.month}.{day.year}" if day else ""


def gap_text(c: Candidate, kz: str, t: Texts) -> str:
    """The tooltip of a drawn gap after the tip: parcel, area, front and kind, then the verdict. kz is the parcel as
    text (sources.kz_text). Area and front are rounded down, so a gap never reads larger than it is. A counted gap
    starts its verdict with „Zählt:“; a gap to check on site gets the site text. A gap that is not drawn (judged not,
    not judged yet, or dropped by a filter) has no tooltip. t: the texts of this package (T[lang])."""
    if not c.drawn:
        raise ValueError(f"{c.gap.gml_id} is not drawn ({c.reason}): it has no tooltip")
    g = c.gap
    tip = t.fill("gap_tip", kz=kz, area=t.number(math.floor(g.area_m2), 0), front=t.number(math.floor(g.front_m), 0),
                 kind=KIND_TEXT[t.lang][g.kind])
    fits = SUITABILITY_TEXT[t.lang][suitability(g.area_m2)]
    v = c.verdict or {}
    if c.counts:
        what = COUNT_TEXT[t.lang].get(v.get("reason", ""), v.get("reason", ""))
        if v.get("by") == "site":
            checked = iso_date(v.get("checked", ""))
            return t.fill("gap_counted_site", tip=tip, what=what, checked=t.date(checked) if checked else "",
                          fits=fits)
        flight = iso_date((c.cover or {}).get("flight", "")) or DOP_DATE
        return t.fill("gap_counted_aerial", tip=tip, what=what, flight=t.date(flight), fits=fits)
    return t.fill("gap_to_check", tip=tip, site_text=SITE_TEXT[t.lang], fits=fits)


def funnel_calc_example(f: dict[str, float], t: Texts) -> CalcExample:
    """The funnel of the city as a written sum, in parcels, ending in the counted gaps and their area. A step that drops
    no parcel goes; the two totals always stand. t: the texts of this package (T[lang])."""
    v = _values(t)
    steps = {key: t.fill(f"calc_example.steps.{key}", **v) for key in t.tree("calc_example.steps")}
    rows = [Row("", round(f["parcels"]), 0, t["calc_example.parcels"])]
    rows += [Row("−", round(f[key]), 0, text) for key, text in steps.items() if round(f[key]) != 0]
    rows += [Row("", round(f["counted"]), 0, t["calc_example.counted"], total=True),
             Row("", round(f["counted_m2"]), 0, t["calc_example.counted_m2"], total=True)]
    return CalcExample(t["calc_example.area"], tuple(rows), t["calc_example.label"])
