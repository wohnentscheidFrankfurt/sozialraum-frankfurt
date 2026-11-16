"""Dwellings per ownership type and cell: estimate 2022, gaps from 2011 (README). Pure module."""
from __future__ import annotations

import numpy as np
import pandas as pd

from pipeline.shared.core.geometry import from_3035_to_wgs84
from pipeline.shared.zensus.model import CLASSES

GROUPS = {"OWN_PUBLIC": ["municipal"], "OWN_COOP": ["coop"], "OWN_COMPANY": ["housing_company", "other_company"],
          "OWN_PERSON": ["condo", "person"], "OWN_STATE": ["state"], "OWN_NONPROFIT": ["nonprofit"]}
GRID_GROUPS = ["OWN_PUBLIC", "OWN_STATE", "OWN_COOP", "OWN_COMPANY", "OWN_PERSON", "OWN_NONPROFIT"]
MIN_DWELLINGS_PER_CELL = 10
GRID_SCALE = 100000  # the browser gets the corners as integers: degrees x GRID_SCALE (5 decimals)
THRESHOLD_DECIMALS = 6  # compared rounded: 10 dwellings can sum to 9.999999999999998
# Backtest 2011 on 1,187 cells with at least 10 dwellings and an owner (research/results/formula_review.txt, round 2):
# share of cells with the right main group, and where the public group (ABG and NH) leads. Research numbers, no build input.
BACKTEST_CELLS_RIGHT, BACKTEST_PUBLIC_RIGHT = 96, 74  # %


def factors(dwellings: dict[str, int], buildings: dict[str, int]) -> dict[str, float]:
    return {k: (dwellings[k] / buildings[k] if buildings.get(k) else 0.0) for k in CLASSES}


def grid_factors(cells: pd.DataFrame, dwellings: dict[str, int]) -> dict[str, float]:
    """Factors of today: dwellings of table 4000W-2002 ÷ buildings of the class in the cells."""
    return factors(dwellings, {k: int(cells[f"bld_{k}"].sum()) for k in CLASSES})


def estimate(cells: pd.DataFrame, f: dict[str, float]) -> pd.DataFrame:
    raw = pd.DataFrame({k: cells[f"bld_{k}"] * f[k] for k in CLASSES})
    total = raw.sum(axis=1)
    scale = (cells["dwellings"] / total.where(total > 0)).fillna(0.0)
    out = pd.DataFrame({"cell_id": cells["cell_id"]})
    for k in CLASSES:
        out[f"dw_{k}"] = raw[k] * scale
    out["dw_unassigned"] = cells["dwellings"].where(total == 0, 0)
    return out


def fill_from_2011(ownership: pd.DataFrame, cells: pd.DataFrame, cells_2011: pd.DataFrame) -> pd.DataFrame:
    """Cells without an ownership type in 2022 get the dwellings of 2011 per class, at most up to the dwellings of 2022
    (README). "Bund oder Land" 2011 counts as municipal there, because the Zensus 2022 lists the
    Nassauische Heimstätte as municipal (pipeline/use_cases/public_housing/README.md); this part is also in dw_nh_2011."""
    out = ownership.reset_index(drop=True).copy()
    columns = [f"dw_{k}" for k in CLASSES] + ["dw_unassigned"]
    out[columns] = out[columns].astype(float)
    d = out[["cell_id", "dw_unassigned"]].merge(cells[["cell_id", "dwellings"]], on="cell_id", how="left")
    d = d.merge(cells_2011, on="cell_id", how="left")
    w11 = pd.DataFrame({k: d[f"dw_{k}_2011"].fillna(0).astype(float) for k in CLASSES})
    s = w11.sum(axis=1)
    target = (d["dw_unassigned"] > 0) & (s > 0)
    a = (d["dwellings"] / s.where(target)).clip(upper=1).fillna(0.0)
    for k in CLASSES:
        out.loc[target, f"dw_{k}"] = (w11[k] * a)[target]
    out.loc[target, "dw_municipal"] = ((w11["municipal"] + w11["state"]) * a)[target]
    out.loc[target, "dw_state"] = 0.0
    out["dw_from_2011"] = (s * a).where(target, 0.0)
    out["dw_nh_2011"] = (w11["state"] * a).where(target, 0.0)
    rest = (out["dw_unassigned"] - out["dw_from_2011"]).clip(lower=0)
    all_spread = target & (s > d["dwellings"])  # more dwellings in 2011 than 2022: all spread, no rounding rest
    out["dw_unassigned"] = rest.where(~all_spread, 0.0)
    return out


def grid_rows(cells: pd.DataFrame) -> list[list]:
    """Cells with at least MIN_DWELLINGS_PER_CELL estimated dwellings: south, west, height, width (integers, degrees x
    GRID_SCALE, rounded to 5 decimals; north is south + height), the group with the most estimated dwellings (the
    colour), a flag and counts per group (every number in the tooltip is a count; docs/data-rules.md, Level). Flag 0: buildings 2022.
    Flag 1: the cell has no owner in 2022; dwellings 2011 in the classes of 2011."""
    per_group = lambda column: np.column_stack([sum(cells[column.format(k)].fillna(0) for k in GROUPS[g])
                                                for g in GRID_GROUPS])
    estimated = np.column_stack([sum(cells[f"dw_{k}"] for k in GROUPS[g]) for g in GRID_GROUPS])
    buildings, dwellings_2011 = per_group("bld_{}"), per_group("dw_{}_2011")
    no_owner = buildings.sum(axis=1) == 0
    counts = np.where(no_owner[:, None], dwellings_2011, buildings)
    keep = estimated.sum(axis=1).round(THRESHOLD_DECIMALS) >= MIN_DWELLINGS_PER_CELL
    cells, estimated, counts, no_owner = cells[keep], estimated[keep], counts[keep], no_owner[keep]
    west, south = from_3035_to_wgs84(cells["x3035"].to_numpy() - 50.0, cells["y3035"].to_numpy() - 50.0)
    east, north = from_3035_to_wgs84(cells["x3035"].to_numpy() + 50.0, cells["y3035"].to_numpy() + 50.0)
    scaled = lambda degrees: np.round(np.round(degrees, 5) * GRID_SCALE).astype(int)
    south, west, north, east = scaled(south), scaled(west), scaled(north), scaled(east)
    return [[int(s), int(w), int(n - s), int(e - w), int(np.argmax(r)), int(f), *(int(x) for x in c)]
            for s, w, n, e, r, f, c in zip(south, west, north, east, estimated, no_owner, counts)]
