"""Weighted statistics that skip missing values and weights of zero."""
from __future__ import annotations

import numpy as np
import pandas as pd

# Stored values keep eight decimals; the map rounds once when it shows them. Two stored decimals rounded twice:
# 16.44673 -> 16.45 -> "16,5" instead of "16,4". Eight, because a share with a denominator up to 10^6 lies at least
# 1/(20 * 10^6) away from a rounding boundary of the map; six decimals could still cross it.
STORED_DECIMALS = 8


def _valid(values, weights):
    w = np.asarray(pd.to_numeric(pd.Series(list(values)), errors="coerce"), dtype=float)
    g = np.asarray(pd.to_numeric(pd.Series(list(weights)), errors="coerce"), dtype=float)
    m = np.isfinite(w) & np.isfinite(g) & (g > 0)
    return w[m], g[m]


def weighted_mean(values, weights) -> float | None:
    w, g = _valid(values, weights)
    if g.sum() == 0:
        return None
    return float((w * g).sum() / g.sum())


def weighted_median(values, weights) -> float | None:
    """Lower weighted median."""
    w, g = _valid(values, weights)
    if g.sum() == 0:
        return None
    o = np.argsort(w, kind="stable")
    c = np.cumsum(g[o]) / g.sum()
    return float(w[o][np.searchsorted(c, 0.5)])


def share(part: float, whole: float) -> float | None:
    """Percentage of part in whole; None if whole is not positive."""
    return float(100 * part / whole) if whole > 0 else None


def coverage(values: pd.Series, basis: pd.Series) -> float | None:
    """Percentage of the basis that has a value."""
    b = basis.fillna(0)
    return share(b[values.notna()].sum(), b.sum())
