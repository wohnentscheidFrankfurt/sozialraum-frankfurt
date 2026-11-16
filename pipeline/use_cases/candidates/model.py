"""Evaluation of the candidate templates (README). Pure module."""
from __future__ import annotations

import math

import pandas as pd

from pipeline.use_cases.candidates.catalog import CITY_VALUE


def shown(x: float, decimals: int) -> float:
    """The value as the map shows it, rounded half up (the browser uses the same rule: `floor(x * 10^d + 0.5) / 10^d`)."""
    return math.floor(x * 10 ** decimals + 0.5) / 10 ** decimals


def threshold(criterion: dict, city_values: dict) -> float | None:
    """The fixed threshold, or the city value of `city` (default: the criterion's own indicator)."""
    if criterion["threshold"] != CITY_VALUE:
        return criterion["threshold"]
    return city_values.get(criterion.get("city", criterion["indicator"]))


def meets(value, op: str, limit) -> bool:
    if value is None or limit is None or (isinstance(value, float) and math.isnan(value)):
        return False
    if op == ">=":
        return value >= limit
    if op == "<":
        return value < limit
    if op == "==":
        return value == limit
    raise ValueError(f"unknown comparison {op!r}")


def evaluate(areas: pd.DataFrame, criteria: list[dict], city_values: dict, decimals: dict[str, int],
             ranked: frozenset[str] | set[str] = frozenset()) -> pd.DataFrame:
    """Criteria met per area, compared on the shown values: value and threshold are rounded to the decimals of the
    criterion's indicator (`city` if set). A ranked indicator is compared unrounded. Small districts (under 1,000
    residents) do not count. Stadtteile have no such rule."""
    rows = []
    kept = areas[areas["small"] == 0] if "small" in areas.columns else areas
    for _, p in kept.iterrows():
        n = sum(_meets_shown(p[k["indicator"]], k, city_values, decimals, ranked)
                for k in criteria)
        rows.append({"area": p["id"], "met": int(n), "full": int(bool(criteria) and n == len(criteria))})
    return pd.DataFrame(rows, columns=["area", "met", "full"])


def _meets_shown(value, criterion: dict, city_values: dict, decimals: dict[str, int], ranked) -> bool:
    limit = threshold(criterion, city_values)
    key = criterion.get("city", criterion["indicator"])
    missing = value is None or limit is None or (isinstance(value, float) and math.isnan(value))
    if not missing and key not in ranked:
        value, limit = shown(value, decimals[key]), shown(limit, decimals[key])
    return meets(value, criterion["op"], limit)
