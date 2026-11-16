"""Cells of the Zensus grid in and around Frankfurt."""
from __future__ import annotations

import numpy as np
import pandas as pd
import shapely
from shapely.ops import unary_union

from pipeline.shared.core.geometry import to_25832
from pipeline.shared.core.grid import cell_center
from pipeline.shared.geography.model import Area, assign_points

CLASSES = ("condo", "person", "coop", "municipal", "housing_company", "other_company", "state", "nonprofit")  # ownership types, Zensus codes 1 to 8
# Size of a building = number of dwellings in it (pipeline/use_cases/ownership_history/README.md); Zensus codes 1 to 5
SIZES = ["1", "2", "3_6", "7_12", "13_plus"]
BBOX_3035 = (4211500, 2989900, 4235500, 3013900)
EDGE_M = 71  # half the diagonal of a 100 m cell


def in_bbox(x: int, y: int) -> bool:
    x0, y0, x1, y1 = BBOX_3035
    return x0 <= x <= x1 and y0 <= y <= y1


def square_meets_bbox(x: int, y: int, size: int) -> bool:
    """True when the square with the lower left corner (x, y) and the side `size` reaches into BBOX_3035."""
    x0, y0, x1, y1 = BBOX_3035
    return x <= x1 and x + size >= x0 and y <= y1 and y + size >= y0


def assemble_cells(cells: dict[str, dict], districts: list[Area], count_columns: list[str],
                   value_columns: list[str]) -> pd.DataFrame:
    """Frame of all cells within the city or at its edge, with coordinates, district and quarter."""
    df = pd.DataFrame.from_dict(cells, orient="index").rename_axis("cell_id").reset_index()
    for column in count_columns:
        df[column] = df[column].fillna(0).astype(int)
    for column in value_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")
    xy = np.array([cell_center(c) for c in df["cell_id"]])
    df["x3035"], df["y3035"] = xy[:, 0], xy[:, 1]
    df["x25832"], df["y25832"] = to_25832(df["x3035"], df["y3035"])
    df["district"] = assign_points(df["x25832"], df["y25832"], districts)
    df["quarter"] = df["district"].map({d.id: d.quarter for d in districts})
    city = unary_union([d.geom for d in districts]).buffer(EDGE_M)
    near = shapely.contains_xy(city, df["x25832"].to_numpy(), df["y25832"].to_numpy())
    df["edge"] = (df["district"].isna() & near).astype(int)
    front = ["cell_id", "x3035", "y3035", "x25832", "y25832", "district", "quarter", "edge"]
    df = df[df["district"].notna() | (df["edge"] == 1)]
    return df[front + [c for c in df.columns if c not in front]].reset_index(drop=True)
