"""Dwellings by year of construction: the class in 2011, capped per cell at the dwellings of 2022, ÷ all dwellings
in 2022 (README). The old stock barely changed; new buildings count in the denominator. Pure module."""
from __future__ import annotations

import pandas as pd

from pipeline.shared.core.stats import share

CLASSES_2011 = (("HOU_PRE1919", "dw_pre1919_2011"), ("HOU_1949_1978", "dw_1949_1978_2011"))


def capped_class_2011(g: pd.DataFrame, column: str) -> pd.Series:
    """Per cell: the class count of 2011, at most the dwellings of 2022. A cell without a count in 2011 gives 0.
    Dormitories counted as dwellings in 2011 but not in 2022 would else push a share far up (README, Why)."""
    return g[column].fillna(0).clip(upper=g["dwellings"].fillna(0))


def construction_values(g: pd.DataFrame) -> dict:
    z: dict = {}
    for kid, column in CLASSES_2011:
        count = int(capped_class_2011(g, column).sum())
        z[kid], z[f"{kid}_DWELLINGS"] = share(count, g["dwellings"].fillna(0).sum()), count
    return z


def construction_parts(g: pd.DataFrame, column: str) -> tuple[int, int, float]:
    """The parts of the worked example of a class: its count in 2011 (uncapped), the count capped per cell (the
    count of the tooltip), and the dwellings of 2022."""
    return int(g[column].fillna(0).sum()), int(capped_class_2011(g, column).sum()), float(g["dwellings"].fillna(0).sum())
