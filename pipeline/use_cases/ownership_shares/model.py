"""Shares of the ownership groups per Stadtteil and Frankfurt (README, Formula; docs/data-rules.md, Ownership).
ABG and NH come from public_housing, Genossenschaften from coops; the four other groups share the rest in proportion
to their estimate (ownership_cells). Denominator: all dwellings of the Stadtteil in 2022. Districts get only the
counted buildings. Pure module."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import pandas as pd

from pipeline.shared.core.stats import share
from pipeline.use_cases.ownership_cells.model import GROUPS
from pipeline.shared.zensus.model import CLASSES

BUILDING_IDS = {"condo": "BLD_CONDO", "person": "BLD_PERSON", "coop": "BLD_COOP", "municipal": "BLD_MUNICIPAL",
                "housing_company": "BLD_HOUSING_COMPANY", "other_company": "BLD_OTHER_COMPANY", "state": "BLD_STATE",
                "nonprofit": "BLD_NONPROFIT"}  # ownership class -> ID of the building count
OTHER_GROUPS = ("OWN_COMPANY", "OWN_PERSON", "OWN_STATE", "OWN_NONPROFIT")
# half range in percentage points: in the backtest on 2011 the range holds the count in 40 of 45 Stadtteile
# (research/results/formula_review.txt, round 2; docs/data-rules.md, Uncertainty)
HALF_POINTS = {"OWN_COMPANY": 3.5, "OWN_PERSON": 5.4, "OWN_STATE": 1.4, "OWN_NONPROFIT": 2.0}
GROUP_IDS = ("OWN_PUBLIC", "OWN_COOP", *OTHER_GROUPS)
DWELLING_COLUMNS = tuple(f"{g}_DWELLINGS{end}" for g in GROUP_IDS for end in ("", "_LOW", "_HIGH"))
BACKTEST_HITS, BACKTEST_AREAS = 40, 45  # Stadtteile within HALF_POINTS in that backtest, the same for all four groups


def all_dwellings(g: pd.DataFrame) -> float:
    """All dwellings of the cells in g (Zensus 2022), cells without a count as 0."""
    return float(g["dwellings"].fillna(0).sum())


def estimated_dwellings(g: pd.DataFrame) -> dict[str, float]:
    """Dwellings per ownership class of the estimate, without the dwellings without owner."""
    return {k: float(g[f"dw_{k}"].fillna(0).sum()) for k in CLASSES}


def group_shares(dwellings: dict[str, float], public: dict, coop: dict, total: float) -> dict:
    """Shares of the six groups and the ends of their ranges. public, coop: dwellings ("value") and half range
    ("half"). total: all dwellings of the area. The rest after ABG, NH and Genossenschaften goes to the four other
    groups in proportion to their estimate. The shares add up to 100 when the rest is not negative and one of the four
    other groups has dwellings."""
    rest = total - public["value"] - coop["value"]
    others = {g: sum(dwellings[k] for k in GROUPS[g]) for g in OTHER_GROUPS}
    weight = sum(others.values())
    z = {"OWN_PUBLIC": share(public["value"], total), "OWN_COOP": share(coop["value"], total)}
    z |= {g: share(rest * others[g] / weight if weight else 0.0, total) for g in OTHER_GROUPS}
    for g, half in half_points(public, coop, total).items():
        z[f"{g}_LOW"] = None if z[g] is None else max(0.0, z[g] - half)
        z[f"{g}_HIGH"] = None if z[g] is None else min(100.0, z[g] + half)
    return z


def group_dwellings(dwellings: dict[str, float], public: dict, coop: dict, total: float,
                    shares: dict | None = None) -> dict:
    """Dwellings of the six groups with the ends of their ranges: share ÷ 100 × all dwellings. The half range of ABG,
    NH and Genossenschaften is their own ("half"), the four others use HALF_POINTS. The low end is bounded at 0, the
    high end is not. Without dwellings all values are None. shares: the result of group_shares, if the caller
    has it already."""
    z = shares or group_shares(dwellings, public, coop, total)
    halves = {"OWN_PUBLIC": public["half"], "OWN_COOP": coop["half"],
              **{g: points / 100 * total for g, points in HALF_POINTS.items()}}
    out = {}
    for g in GROUP_IDS:
        value = None if z[g] is None else z[g] / 100 * total
        half = None if value is None else halves[g]
        out |= {f"{g}_DWELLINGS": value,
                f"{g}_DWELLINGS_LOW": None if value is None else max(0.0, value - half),
                f"{g}_DWELLINGS_HIGH": None if value is None else value + half}
    return out


def half_points(public: dict, coop: dict, total: float) -> dict[str, float | None]:
    """Half range of each group in percentage points, before the bounds 0 and 100; None without dwellings."""
    if not total:
        return {g: None for g in GROUP_IDS}
    return {"OWN_PUBLIC": share(public["half"], total), "OWN_COOP": share(coop["half"], total), **HALF_POINTS}


def range_rows(halves: pd.DataFrame) -> list[dict]:
    """Smallest and largest half range of each group over the Stadtteile with a value, for the Unsicherheit of the ⓘ.
    halves: column id and one column per group (half_points per Stadtteil)."""
    return [{"indicator": g, "low": float(halves[g].min()), "high": float(halves[g].max())}
            for g in halves.columns if g != "id" and halves[g].notna().any()]


def building_counts(g: pd.DataFrame) -> dict[str, int]:
    return {BUILDING_IDS[k]: int(g[f"bld_{k}"].sum()) for k in CLASSES}


def quarter_values(g: pd.DataFrame, public: dict, coop: dict) -> dict:
    dwellings = estimated_dwellings(g)
    total = all_dwellings(g)
    shares = group_shares(dwellings, public, coop, total)
    return {**shares, **group_dwellings(dwellings, public, coop, total, shares),
            "COV_OWN": share(sum(dwellings.values()), total),
            **building_counts(g)}


def rest_dwellings(g: pd.DataFrame, public_value: float, coop_value: float) -> float:
    return all_dwellings(g) - public_value - coop_value


def by_quarter(table: pd.DataFrame, value: str, half: str) -> dict[str, dict]:
    """Dwellings and half range per Stadtteil from a working table with the column quarter, as the step stored it."""
    return {r["quarter"]: {"value": r[value], "half": r[half]} for r in table.to_dict("records")}


def city_total(table: pd.DataFrame, value: str) -> dict:
    """Sum over the Stadtteile with the builtin sum in row order; Frankfurt shows no range."""
    return {"value": sum(table[value].tolist()), "half": 0.0}


def require_quarters(quarters: Iterable, values: dict, what: str, step: str) -> None:
    missing = sorted(set(quarters) - set(values))
    if missing:
        raise ValueError(f"no value for {what} in {missing}; run `--step {step}` first")


@dataclass(frozen=True)
class OtherNumbers:
    """Numbers of the worked example of one of the four other groups in one Stadtteil."""
    buildings: dict[str, int]  # per class of the group
    factors: dict[str, float]  # per class of the group
    from_2011: float  # dwellings of the group in cells filled from 2011
    dwellings: float  # <group>_DWELLINGS
    total: float  # all dwellings of the Stadtteil


def other_numbers(g: pd.DataFrame, group: str, factors: dict[str, float], dwellings: float) -> OtherNumbers:
    """g: the cells of one Stadtteil merged with ownership_cells. Filled cells add dwellings, no buildings."""
    classes = GROUPS[group]
    filled = g["dw_from_2011"].fillna(0) > 0
    return OtherNumbers({k: int(g.loc[~filled, f"bld_{k}"].sum()) for k in classes},
                        {k: factors[k] for k in classes},
                        float(sum(g.loc[filled, f"dw_{k}"].fillna(0).sum() for k in classes)),
                        dwellings, all_dwellings(g))
