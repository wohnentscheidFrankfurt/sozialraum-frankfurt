"""Reference files in reference/ (values the checks compare with)."""
from __future__ import annotations

from pathlib import Path

import pandas as pd


def read_reference(path: Path, key: str = "key") -> dict[str, float]:
    """The rows of a file with a value column, as key column -> value."""
    df = pd.read_csv(path)
    return dict(zip(df[key], df["value"]))


def read_column(path: Path, column: str) -> list:
    """One column of a file without a value column (a list of expected keys)."""
    return pd.read_csv(path)[column].tolist()
