"""Means of the Zensus 2022 grid per area: renters, rent, vacancy (README). Pure module."""
from __future__ import annotations

import pandas as pd

from pipeline.shared.core.grid import km_cell
from pipeline.shared.core.stats import coverage, weighted_mean


def fill_rate(cells: pd.DataFrame, rate: str, dash: str, km_rates: dict[str, float]) -> pd.Series:
    """Vacancy rate (percent) per cell with the „–“ cells filled from the 1 km grid (README, Formula).

    Per 1 km cell, the vacant dwellings the 1 km rate implies (rate × dwellings of all given cells in it) minus the
    vacant dwellings of the cells with a value are spread over the „–“ cells, by their dwellings. A negative rest gives
    them 0. A 1 km cell without „–“ cell or without a 1 km rate keeps its values. Pass inner and edge cells: the 1 km
    cell holds both, and the caller aggregates the inner ones."""
    dwellings = cells["dwellings"].fillna(0)
    is_dash = cells[dash] == 1
    km = cells["cell_id"].map(km_cell)
    km_rate = km.map(km_rates)
    implied = (km_rate / 100 * dwellings).groupby(km).transform("sum")
    known = (cells[rate].fillna(0) / 100 * dwellings).where(~is_dash, 0).groupby(km).transform("sum")
    dash_dwellings = dwellings.where(is_dash, 0).groupby(km).transform("sum")
    fillable = is_dash & km_rate.notna() & (dash_dwellings > 0)
    spread = 100 * ((implied - known).clip(lower=0) / dash_dwellings.where(dash_dwellings > 0))
    return cells[rate].where(~fillable, spread).astype(float)


def _occupied(g: pd.DataFrame) -> pd.Series:
    return g["dwellings"] * (1 - g["vacancy_rate"].fillna(0) / 100)


def _vacant_dwellings(g: pd.DataFrame, rate: str) -> float | None:
    """Vacant dwellings of the area: rate ÷ 100 × dwellings per cell, summed (NaN counts 0); None without any rate."""
    if g[rate].notna().sum() == 0:
        return None
    return float((g[rate].fillna(0) / 100 * g["dwellings"].fillna(0)).sum())


def _weighted(values: pd.Series, weights: pd.Series) -> pd.Series:
    """True where weighted_mean counts the cell: a value and a weight above 0."""
    return values.notna() & (weights.fillna(0) > 0)


def vacancy_parts(g: pd.DataFrame, rate: str, dash: str) -> tuple[float, float, float]:
    """The parts of the worked example of a vacancy rate, on the filled rates (fill_rate): vacant dwellings of the
    cells with a value, vacant dwellings of the „–“ cells (from the 1 km grid), dwellings of the cells with a rate."""
    vacant = g[rate].fillna(0) / 100 * g["dwellings"].fillna(0)
    is_dash = g[dash] == 1
    dwellings = g["dwellings"].where(_weighted(g[rate], g["dwellings"]), 0).sum()
    return float(vacant[~is_dash].sum()), float(vacant[is_dash].sum()), float(dwellings)


def renter_parts(g: pd.DataFrame) -> tuple[float, float]:
    """The parts of the worked example of the renters: occupied dwellings of the cells with an owner rate, and of them
    the owner-occupied dwellings."""
    occupied = _occupied(g).where(_weighted(g["owner_rate"], _occupied(g)), 0)
    return float(occupied.sum()), float((g["owner_rate"].fillna(0) / 100 * occupied).sum())


def housing_values(g: pd.DataFrame) -> dict:
    owner_rate = weighted_mean(g["owner_rate"], _occupied(g))
    return {"HOU_RENTERS": None if owner_rate is None else 100 - owner_rate,
            "HOU_RENT": weighted_mean(g["rent_sqm"], g["rented_dwellings"]),
            "HOU_VACANT_MARKET": weighted_mean(g["vacancy_rate_market"], g["dwellings"]),
            "HOU_VACANT_ALL": weighted_mean(g["vacancy_rate"], g["dwellings"]),
            "HOU_VACANT_MARKET_DWELLINGS": _vacant_dwellings(g, "vacancy_rate_market"),
            "HOU_VACANT_ALL_DWELLINGS": _vacant_dwellings(g, "vacancy_rate")}


def housing_coverage(g: pd.DataFrame) -> dict:
    """Share of the weight that holds a value, per housing indicator. The check report lists low coverage per area;
    Frankfurt has no coverage value."""
    return {"COV_HOU_RENTERS": coverage(g["owner_rate"], _occupied(g)),
            "COV_HOU_RENT": coverage(g["rent_sqm"], g["rented_dwellings"]),
            "COV_HOU_VACANT_MARKET": coverage(g["vacancy_rate_market"], g["dwellings"]),
            "COV_HOU_VACANT_ALL": coverage(g["vacancy_rate"], g["dwellings"])}
