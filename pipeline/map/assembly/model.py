"""Joins the area tables of all use cases per level; computes nothing else
(docs/architecture.md, Use-case packages). Pure module."""
from __future__ import annotations

import pandas as pd

from pipeline.shared.geography.model import is_small


def join_area_table(df: pd.DataFrame, table: pd.DataFrame) -> pd.DataFrame:
    """Left join of an area table on `id`; a column may come from one table only, and an id may appear once per table
    (a duplicate id would multiply the rows of the area)."""
    shared = sorted((set(df.columns) & set(table.columns)) - {"id"})
    if shared:
        raise ValueError(f"columns in two area tables: {shared}")
    return df.merge(table, on="id", how="left", validate="one_to_one")


def add_small(districts: pd.DataFrame) -> pd.DataFrame:
    """Adds the column `small` (1 for a district below the population threshold, from grid and monitoring) after the
    joins. Stops when a joined table already has a column `small`."""
    if "small" in districts.columns:
        raise ValueError("column small in an area table: assembly sets it after the joins")
    return districts.assign(small=is_small(districts["POP_MONITORING"], districts["POP"]))
