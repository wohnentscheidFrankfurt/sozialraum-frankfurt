"""Monitoring 2024 per district, Stadtteil and Frankfurt (README). Pure module."""
from __future__ import annotations

import pandas as pd

from pipeline.shared.core.areas import city_rows
from pipeline.shared.core.stats import weighted_mean

INDICATORS_COLUMNS = {"SOC_MIN_INCOME": ("min_income", "pop"), "SOC_UNEMPLOYED": ("unemployment", "pop_15_65"),
                      "SOC_INDEX": ("deprivation_index", "pop")}  # ID -> (column, weight)
# monitoring indicators for quarters -> weight
QUARTER_WEIGHTS = {"SOC_MIN_INCOME": "POP_MONITORING", "SOC_UNEMPLOYED": "POP_15_65"}
# a Stadtteil gets a mean only when the districts with a value hold at least this share of its weight
# (docs/data-rules.md, Areas, not persons)
QUARTER_MIN_COVERAGE = 0.95
# indicators whose table can merge other districts than the map unit -> group column
GROUP_COLUMNS = {"SOC_MIN_INCOME": "min_income_group", "SOC_UNEMPLOYED": "unemployment_group"}


def _list_de(numbers) -> str:
    """„202, 203 und 213“: ascending, integers without leading zeros."""
    names = [str(n) for n in sorted(numbers)]
    return f"{', '.join(names[:-1])} und {names[-1]}" if len(names) > 1 else names[0]


def _shared_value(unit: pd.DataFrame, column: str, known: set[int]) -> str | None:
    """The member numbers of the source row when it holds districts outside the unit, else None. The frame holds the
    row label of each indicator as district numbers (sources.py)."""
    groups = {g for g in unit[column] if g is not None}
    if len(groups) > 1:
        raise ValueError(f"unit {unit['unit'].iloc[0]}: {column} differs between its districts: {sorted(groups)}")
    if not groups:
        return None
    group = groups.pop()
    if set(group) - known:
        raise ValueError(f"unit {unit['unit'].iloc[0]}: {column} names unknown districts {sorted(set(group) - known)}")
    return _list_de(group) if set(group) - set(unit["unit_members"].iloc[0]) else None


def monitoring_by_district(monitoring: pd.DataFrame) -> pd.DataFrame:
    known = {number for members in monitoring["unit_members"] for number in members}
    rows = []
    for unit, g in monitoring.groupby("unit", sort=False):
        row = {"district": unit, "POP_MONITORING": g["pop"].fillna(0).sum(), "HOUSEHOLDS": g["households"].fillna(0).sum(),
               "POP_15_65": g["pop_15_65"].fillna(0).sum()}
        for target, (column, weight) in INDICATORS_COLUMNS.items():
            value = weighted_mean(g[column], g[weight].fillna(0))
            if value is None:
                present = g[column].dropna()
                value = float(present.iloc[0]) if len(present) else None
            row[target] = value
        for target, column in GROUP_COLUMNS.items():
            row[f"{target}_SHARED"] = _shared_value(g, column, known)
        rows.append(row)
    return pd.DataFrame(rows)


def quarter_monitoring(situation: pd.DataFrame, district_quarter: dict[str, str]) -> pd.DataFrame:
    s = situation.assign(quarter=situation["district"].map(district_quarter))
    rows = []
    for quarter, g in s.groupby("quarter", sort=False):
        row = {"quarter": quarter, "POP_MONITORING": g["POP_MONITORING"].sum()}
        for k, weight in QUARTER_WEIGHTS.items():
            total = g[weight].sum()
            covered = g.loc[g[k].notna(), weight].sum()
            row[k] = weighted_mean(g[k], g[weight]) if total > 0 and covered / total >= QUARTER_MIN_COVERAGE else None
        rows.append(row)
    return pd.DataFrame(rows)


def monitoring_city(published: dict[str, float]) -> list[dict]:
    """City values: the published values. The Benachteiligungsindex is a rank and has no city value.
    The check recomputes them from the districts (checks.py)."""
    return city_rows({k: published[k] for k in QUARTER_WEIGHTS}, kind="published")
