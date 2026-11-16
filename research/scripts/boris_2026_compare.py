"""Compares the built land values (interim/, after a build) with the values of 1.1.2026 that the WMS gives at the
centre of every inner cell (research/results/boris_2026_cells.csv, from boris_2026_cells.py).

  .venv/bin/python -I research/scripts/boris_2026_compare.py > research/results/boris_2026_compare.txt
"""
import re
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, ".")
from pipeline.shared.core.stats import weighted_median


def direct(zones: str) -> float:
    """Mean of the residential and mixed zones with building land at the point, as the build counts them."""
    values = []
    for z in filter(None, zones.split(";")):
        _, brw, development, use = z.split("|")
        m = re.fullmatch(r"(\d+(?:,\d+)?) EUR/m²", brw)
        if development == "Baureifes Land" and use[:1] in ("W", "M") and m:
            values.append(float(m.group(1).replace(",", ".")))
    return np.mean(values) if values else np.nan


d = pd.read_csv("research/results/boris_2026_cells.csv", dtype=str).fillna("")
d["direct"] = d["zones"].map(direct)
cells = pd.read_csv("interim/cells_2022.csv", usecols=["cell_id", "district", "quarter", "pop"])
built = pd.read_csv("interim/land_value_cells.csv")
m = cells.merge(built, on="cell_id").merge(d[["cell_id", "direct"]], on="cell_id")
both = m.dropna(subset=["land_value", "direct"])
differ = (both["land_value"] - both["direct"]).abs() > 0.5
print(f"inner cells: {len(m)}; with a value in the build: {m['land_value'].notna().sum()}; "
      f"in the direct query: {m['direct'].notna().sum()}; in both: {len(both)}")
print(f"cells in both with another value: {differ.sum()} ({both.loc[differ, 'pop'].sum()} residents of "
      f"{m['pop'].sum()})")
print(f"only in the build: {(m['land_value'].notna() & m['direct'].isna()).sum()}; only in the direct query: "
      f"{(m['land_value'].isna() & m['direct'].notna()).sum()}")
for level in ("quarter", "district"):
    rows = [(k, weighted_median(g["land_value"], g["pop"]), weighted_median(g["direct"], g["pop"]))
            for k, g in m.groupby(level)]
    r = pd.DataFrame(rows, columns=["id", "built", "direct"]).dropna()
    other = r[(r["built"] - r["direct"]).abs() > 0.5]
    print(f"{level}: {len(r)} areas, {len(other)} with another median")
    if len(other):
        print(other.to_string(index=False))
print(f"city: built {weighted_median(m['land_value'], m['pop'])}, direct {weighted_median(m['direct'], m['pop'])}")
