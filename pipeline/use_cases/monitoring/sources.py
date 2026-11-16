"""Monitoring 2024 (CSV in sources/, written by research/scripts/mon.py)."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

MONITORING_COLUMNS = {"Einheit": "unit", "EW": "pop", "HH": "households", "EW15_65": "pop_15_65",
                      "Mindestsich_%": "min_income", "Arbeitslosendichte_%": "unemployment",
                      "Benacht_Index": "deprivation_index"}
# the number label of the source row of each table as printed (e.g. "202/203/213"); empty where the table has no row
GROUP_COLUMNS = {"Gruppe_Arbeitslosendichte_%": "unemployment_group", "Gruppe_Mindestsich_%": "min_income_group",
                 "Gruppe_Benacht_Index": "deprivation_index_group"}


def label_members(label: str) -> tuple[int, ...]:
    """The district numbers of a row label. A later part may drop the leading digits of the first one:
    "424/25" is 424 and 425, "591/92" is 591 and 592, "010" is 10. The tables print the same district differently,
    so labels are compared as numbers."""
    parts = label.split("/")
    first = parts[0]
    return (int(first), *(int(p) if len(p) >= len(first) else int(first[:len(first) - len(p)] + p) for p in parts[1:]))


def monitoring_frame(raw: pd.DataFrame) -> pd.DataFrame:
    """Renames the columns; `unit_members` and the three group columns hold tuples of district numbers (None: no row)."""
    missing = [c for c in GROUP_COLUMNS if c not in raw.columns]
    if missing:
        raise ValueError(f"Monitoring CSV: column {', '.join(missing)} missing (run research/scripts/mon.py)")
    frame = raw.rename(columns=MONITORING_COLUMNS | GROUP_COLUMNS)
    frame["unit_members"] = frame["unit"].map(label_members)
    for column in GROUP_COLUMNS.values():
        frame[column] = frame[column].map(lambda label: None if pd.isna(label) else label_members(label))
    return frame


def read_monitoring(path: Path) -> pd.DataFrame:
    return monitoring_frame(pd.read_csv(path, dtype={"STBZ": str, "Einheit": str} | dict.fromkeys(GROUP_COLUMNS, str)))
