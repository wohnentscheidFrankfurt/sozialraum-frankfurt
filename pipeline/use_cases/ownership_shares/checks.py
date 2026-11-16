"""Checks of the ownership shares. Pure module."""
from __future__ import annotations

import pandas as pd

from pipeline.shared.core.checks import FAIL, OK, WARN, Check, check_tolerance, number
from pipeline.shared.core.checks import check_examples as shared_check_examples
from pipeline.use_cases.ownership_cells.model import GROUPS
from pipeline.use_cases.ownership_shares.catalog import EXAMPLES
from pipeline.use_cases.ownership_shares.model import GROUP_IDS
from pipeline.shared.zensus.model import CLASSES



def check_ownership_shares(quarters: pd.DataFrame, tolerance: float = 0.1) -> Check:
    """ABG+NH and Genossenschaften come from their use cases; the shares must still add up to 100."""
    total = quarters[list(GROUP_IDS)].sum(axis=1)
    bad = quarters.loc[(total - 100).abs() > tolerance, "name"].tolist()
    return Check("Ownership: shares per Stadtteil add up to 100 %", FAIL if bad else OK,
                 f"off by more than {tolerance} in {bad}" if bad else f"{len(quarters)} Stadtteile, allowed ± {tolerance}")


def check_dwellings(quarters: pd.DataFrame, tolerance: float = 0.1) -> Check:
    """The counts per group are the shares of the map: 100 × count ÷ sum of the six counts equals the share."""
    counts = quarters[[f"{g}_DWELLINGS" for g in GROUP_IDS]]
    total = counts.sum(axis=1)
    bad = []
    for g in GROUP_IDS:
        off = (100 * quarters[f"{g}_DWELLINGS"] / total - quarters[g]).abs() > tolerance
        if off.any():
            bad.append(f"{g} in {quarters.loc[off, 'name'].tolist()}")
    return Check("Ownership: dwellings per group match the shares", FAIL if bad else OK,
                 "off by more than " + f"{tolerance}: " + "; ".join(bad) if bad
                 else f"{len(quarters)} Stadtteile, allowed ± {tolerance}")


def check_dwellings_total(quarters: pd.DataFrame, totals: pd.DataFrame, tolerance: float = 0.5) -> Check:
    """The six counts add up to all dwellings of the Stadtteil. totals: id and total (all dwellings)."""
    q = quarters.merge(totals, on="id")
    off = (q[[f"{g}_DWELLINGS" for g in GROUP_IDS]].sum(axis=1) - q["total"]).abs() > tolerance
    bad = q.loc[off, "name"].tolist()
    return Check("Ownership: the six counts add up to all dwellings", FAIL if bad else OK,
                 f"off by more than {tolerance} in {bad}" if bad else f"{len(q)} Stadtteile, allowed ± {tolerance}")


def check_city_shares(city: dict, table: dict[str, int]) -> list[Check]:
    """City share of each group against table 4000W-2002 (WARN only: the table counts every dwelling)."""
    out = []
    for group, classes in GROUPS.items():
        expected = 100 * sum(table[k] for k in classes) / sum(table[k] for k in CLASSES)
        out.append(check_tolerance(f"Ownership: city share {group} against 4000W", city[group], expected,
                                   absolute=2, on_failure=WARN))
    return out


def check_rest(rest: pd.DataFrame) -> Check:
    """README, Checks: ABG, NH and Genossenschaften must not take more than all dwellings of a Stadtteil."""
    bad = rest.loc[rest["rest"] < 0, "name"].tolist()
    return Check("Ownership: rest after ABG, NH and Genossenschaften not negative", FAIL if bad else OK,
                 f"negative in {bad}" if bad else f"{len(rest)} Stadtteile")


def check_ranges(quarters: pd.DataFrame, halves: pd.DataFrame, tolerance: float = 1e-6) -> Check:
    """The range the map shows at a value is the value ± the half range the ⓘ counts, bounded to 0 to 100
    (docs/data-rules.md, Uncertainty). quarters: the stored table with name; halves: id and the half range
    of each group per Stadtteil."""
    q = quarters.merge(halves, on="id", suffixes=("", "_HALF"))
    groups = [g for g in halves.columns if g != "id"]
    missing = quarters.loc[~quarters["id"].isin(halves["id"]), "name"].tolist()
    bad, widest = ([f"no half range for {missing}"] if missing else []), []
    for g in groups:
        v, h = q[g], q[f"{g}_HALF"]
        has = v.notna()
        off = has & (((q[f"{g}_LOW"] - (v - h).clip(lower=0)).abs() > tolerance)
                     | ((q[f"{g}_HIGH"] - (v + h).clip(upper=100)).abs() > tolerance) | (h < 0) | h.isna())
        if off.any():
            bad.append(f"{g} in {q.loc[off, 'name'].tolist()}")
        if (has & h.notna()).any():
            low, high = h[has].min(), h[has].max()
            widest.append(f"{g} {number(low)}" if low == high else
                          f"{g} {number(low)} to {number(high)} (widest {q.loc[h[has].idxmax(), 'name']})")
    return Check("Ownership: range at the value = value ± half range of the ⓘ", FAIL if bad else OK,
                 "; ".join(bad) if bad else f"{len(q)} Stadtteile; half range in points: " + "; ".join(widest))


def check_city_within_range(city: dict, halves: dict, table: dict[str, int], tolerance: float = 1e-9) -> Check:
    """Table share against Unsicherheit: the share of table 4000W-2002 lies within the city value ± the half range of
    Frankfurt (ABG, NH and Genossenschaften: the half ranges of the Stadtteile added up). WARN only."""
    total = sum(table[k] for k in CLASSES)
    rows = []
    for group, classes in GROUPS.items():
        expected = 100 * sum(table[k] for k in classes) / total
        rows.append((abs(city[group] - expected) > halves[group] + tolerance,
                     f"{group} {number(city[group])} against {number(expected)} (± {number(halves[group])})"))
    outside = [t for out, t in rows if out]
    return Check("Ownership: share of 4000W within the range of the city value", WARN if outside else OK,
                 "outside: " + "; ".join(outside) if outside else "; ".join(t for _, t in rows))


def check_examples(texts: dict[str, str], examples: list[dict] = EXAMPLES) -> Check:
    """The examples in the ⓘ of OWN_COMPANY: every phrase stands in its source. texts: source key -> text."""
    return shared_check_examples("Ownership: examples in the ⓘ of OWN_COMPANY stand in their sources", texts, examples)
