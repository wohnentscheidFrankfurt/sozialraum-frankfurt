"""Texts of the ownership estimate and of the overlay „Eigentum je 100-m-Feld“ (texts.<lang>.yaml). Pure module."""
from __future__ import annotations

from pipeline.shared.core.indicator import Source, year_of
from pipeline.shared.core.texts import Texts, package_texts, per_language
from pipeline.use_cases.ownership_cells.model import BACKTEST_CELLS_RIGHT, BACKTEST_PUBLIC_RIGHT, MIN_DWELLINGS_PER_CELL

T: dict[str, Texts] = package_texts(__file__)


def _years(t: Texts) -> dict[str, str]:
    return {"year_2022": year_of(t["core.z22_as_of"]), "year_2011": year_of(t["core.z11_as_of"])}


# The as-of date and the legend notes of the ownership groups; the other ownership use cases take them by language
OWN_AS_OF: dict[str, str] = per_language(lambda t: t["own_as_of"], T)
OWN_LEGEND_NOTE: dict[str, str] = per_language(lambda t: t.fill("legend_note", **_years(t)), T)
OWN_LEGEND_NOTE_COOP: dict[str, str] = per_language(lambda t: t.fill("legend_note_coop", **_years(t)), T)
ZENSUS_2022: dict[str, Source] = per_language(lambda t: Source(**t.tree("sources.zensus_2022")), T)
ZENSUS_2011: dict[str, Source] = per_language(lambda t: Source(**t.tree("sources.zensus_2011")), T)
SOURCES: dict[str, list[Source]] = per_language(lambda t: [ZENSUS_2022[t.lang], ZENSUS_2011[t.lang]], T)
# The group in the dative, for the grid tooltip (web/js/04_overlays.js)
GROUP_DATIVE: dict[str, dict[str, str]] = per_language(lambda t: t.tree("group_dative"), T)


def _grid_overlay(t: Texts) -> dict[str, str]:
    """ⓘ of the overlay „Eigentum je 100-m-Feld“ (docs/data-rules.md, Level; docs/texts.md, ⓘ protocol)."""
    numbers = {"min_dwellings": MIN_DWELLINGS_PER_CELL, "cells_right": BACKTEST_CELLS_RIGHT,
               "public_right": BACKTEST_PUBLIC_RIGHT}
    return {field: t.fill(f"grid_overlay.{field}", **numbers) for field in t.tree("grid_overlay")}


GRID_OVERLAY: dict[str, dict[str, str]] = per_language(_grid_overlay, T)
