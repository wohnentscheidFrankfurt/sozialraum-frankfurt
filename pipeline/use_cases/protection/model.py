"""Preservation statutes (§ 172 BauGB) per cell and per area."""
from __future__ import annotations

import numpy as np
import pandas as pd
import shapely
from shapely.ops import unary_union

from pipeline.shared.core.geometry import Site
from pipeline.shared.core.stats import share
from pipeline.shared.geography.model import Area, names_in_area


def inside(sites: list[Site], xs, ys) -> np.ndarray:
    area = unary_union([s.geom for s in sites])
    shapely.prepare(area)
    return shapely.contains_xy(area, np.asarray(xs), np.asarray(ys))


def names_by_area(areas: list[Area], level: str, groups: dict[str, list[Site]]) -> pd.DataFrame:
    """One row per area; one column per group with the names of its sites that cover at least 1 ha."""
    return pd.DataFrame([{level: a.id, **{column: "; ".join(names_in_area(a, sites)) for column, sites in groups.items()}}
                         for a in areas])


def protection_values(g: pd.DataFrame) -> dict:
    """Residents in cells whose centre lies in a valid social preservation area ÷ residents of the area."""
    return {"PROT_SOCIAL": share(g.loc[g["in_social_preservation"] == 1, "pop"].sum(), g["pop"].sum())}
