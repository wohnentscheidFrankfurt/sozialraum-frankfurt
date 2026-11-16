"""The table of the city values (rows indicator, value, kind): assembly writes it, steps read it as a dict.
Pure module."""
from __future__ import annotations

import math

import pandas as pd

from pipeline.shared.core.stats import STORED_DECIMALS


def city_values_frame(rows: list[dict]) -> pd.DataFrame:
    """City values of all use cases (rows indicator, value, kind), stored with STORED_DECIMALS. Stops on an
    indicator that two rows deliver."""
    df = pd.DataFrame(rows, columns=["indicator", "value", "kind"])
    duplicates = sorted(df.loc[df["indicator"].duplicated(), "indicator"].unique())
    if duplicates:
        raise ValueError(f"duplicate indicators in the city values: {duplicates}")
    df["value"] = pd.to_numeric(df["value"], errors="coerce").round(STORED_DECIMALS)
    return df


def city_value_dict(df: pd.DataFrame) -> dict[str, float | None]:
    return {k: (None if (isinstance(v, float) and math.isnan(v)) else float(v))
            for k, v in zip(df["indicator"], df["value"])}
