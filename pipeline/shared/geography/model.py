"""Areas (districts and quarters) and points in areas. All geometries in EPSG:25832."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
import shapely

AIRPORT_MERGED = "Sachsenhausen-Süd und Flughafen"
MIN_OVERLAP_M2 = 10_000  # a site counts for an area if it covers at least 1 ha of it
SMALL_POP = 1000  # districts under 1,000 residents in the grid or in the monitoring do not count (docs/architecture.md, Use-case packages)


@dataclass
class Area:
    id: str
    name: str
    quarter: str
    survey_area: str
    geom: object


def map_quarter_name(name: str) -> str:
    """Sachsenhausen-Süd and Flughafen are one quarter, as at votemanager."""
    name = name.strip()
    return AIRPORT_MERGED if name in ("Sachsenhausen-Süd", "Flughafen") else name


def assign_points(xs, ys, areas: list[Area]) -> np.ndarray:
    """Id of the area each point (EPSG:25832) lies in, else None. On borders the first area wins."""
    points = shapely.points(np.asarray(xs, dtype=float), np.asarray(ys, dtype=float))
    tree = shapely.STRtree([a.geom for a in areas])
    source, hit = tree.query(points, predicate="intersects")
    result = np.full(len(points), None, dtype=object)
    for i, t in sorted(zip(source, hit), reverse=True):
        result[i] = areas[t].id
    return result


def names_in_area(area: Area, sites) -> list[str]:
    """Titles of the sites that cover at least 1 ha of the area."""
    return [s.title for s in sites if s.geom is not None and area.geom.intersection(s.geom).area >= MIN_OVERLAP_M2]


def is_small(pop_monitoring: pd.Series, pop: pd.Series) -> pd.Series:
    """1 for a small district, else 0."""
    return ((pop_monitoring.fillna(0) < SMALL_POP) | (pop.fillna(0) < SMALL_POP)).astype(int)
