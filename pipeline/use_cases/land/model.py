"""Standard land values (BORIS) per point and pending development plans per area."""
from __future__ import annotations

from dataclasses import dataclass, replace

import numpy as np
import pandas as pd
import shapely

from pipeline.shared.core.geometry import Site
from pipeline.shared.core.stats import weighted_median
from pipeline.shared.geography.model import Area, names_in_area


@dataclass(frozen=True)
class Zone:
    geom: object
    value: float  # standard land value in €/m²
    use: str  # BORIS use code, for example W or M
    number: str = ""  # BORIS zone number (bodenrichtwertNummer)
    building: str = ""  # BORIS building type (ergaenzung), for example EFH or MFH


def with_values(zones: list[Zone], values: dict[str, float]) -> list[Zone]:
    """The zones with the value of the same number; a zone whose number has no value drops out (land README, Formula)."""
    return [replace(z, value=values[z.number]) for z in zones if z.number in values]


def land_value_at(xs, ys, zones: list[Zone]) -> np.ndarray:
    """Land value at the point; where zones overlap, their mean."""
    values = np.array([z.value for z in zones])
    tree = shapely.STRtree([z.geom for z in zones])
    points = shapely.points(np.asarray(xs, dtype=float), np.asarray(ys, dtype=float))
    source, hit = tree.query(points, predicate="intersects")
    total, count = np.zeros(len(points)), np.zeros(len(points))
    np.add.at(total, source, values[hit])
    np.add.at(count, source, 1)
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(count > 0, total / count, np.nan)


def pending_plans_by_area(areas: list[Area], level: str, plans: list[Site]) -> pd.DataFrame:
    rows = []
    for a in areas:
        names = names_in_area(a, plans)
        rows.append({level: a.id, "LAND_PENDING_PLAN": int(bool(names)), "pending_plan_names": "; ".join(names)})
    return pd.DataFrame(rows)


def land_values(g: pd.DataFrame) -> dict:
    """Median land value of the cells of an area, weighted by residents; each cell has the zone at its centre."""
    return {"LAND_VALUE": weighted_median(g["land_value"], g["pop"])}
