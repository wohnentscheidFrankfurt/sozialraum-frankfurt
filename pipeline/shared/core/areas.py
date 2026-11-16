"""Area tables of a use case: one row per area of a level, and city values as rows of city_values.csv
(docs/architecture.md, Use-case packages). Pure module."""
from __future__ import annotations

from typing import Callable

import pandas as pd


def per_area(cells: pd.DataFrame, level: str, compute: Callable[[str, pd.DataFrame], dict]) -> pd.DataFrame:
    """One row per area of `level` (in the order of the cells): `id` and the values of `compute(key, cells)`."""
    return pd.DataFrame([{"id": key, **compute(key, g)} for key, g in cells.groupby(level, sort=False)])


def city_rows(values: dict, kind: str = "computed", without: frozenset = frozenset()) -> list[dict]:
    """City values as rows (indicator, value, kind); no ends of a range and no IDs of `without` (counts)."""
    return [{"indicator": k, "value": v, "kind": kind} for k, v in values.items()
            if k not in without and not k.endswith(("_LOW", "_HIGH"))]
