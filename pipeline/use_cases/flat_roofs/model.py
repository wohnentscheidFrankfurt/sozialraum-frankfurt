"""Low flat roofs of the LoD2 building model: candidates, wall strip, housing zone, funnel and area sums. Pure."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
import shapely
from shapely.geometry.base import BaseGeometry

from pipeline.shared.geography.model import Area, assign_points

HEIGHT_MIN_M = 2.5  # a low flat part is at least this high ...
HEIGHT_MAX_M = 8.0  # ... and under this height
MIN_ROOF_M2 = 200.0  # a building is a roof candidate from this much low flat roof
NEIGHBOUR_GAP_M = 1.0  # a part within this distance of the roof stands at its edge
TALLER_BY_M = 3.0  # a wall at the edge is taller when it is more than this much higher than the low flat roof
# strip kept free in front of a taller wall: the smallest Abstandsfläche, HBO § 6 Abs. 5 Satz 4 in the version of
# Baupaket I 2025 (checks.check_building_code)
WALL_GAP_M = 2.5
VERY_LOW_M = 3.2  # a roof under this height does not count
MODULE_SHARE = 0.5  # share of the counted roof a module estimate uses
MODULE_M2 = 25.0  # area of one module
SIMPLIFY_M = 1.0  # simplification of the overlay geometry


@dataclass(frozen=True)
class Roof:
    building: str
    use: str  # function code of the largest low flat part
    area_m2: float  # sum of the low flat parts
    height_m: float  # highest low flat part
    wall_m2: float  # part of area_m2 within WALL_GAP_M of a taller wall, 0 if none
    very_low: bool
    housing: bool
    geom: BaseGeometry  # the low flat parts as one geometry, EPSG:25832
    x: float  # representative point
    y: float

    @property
    def usable_m2(self) -> float:
        """The area a counted roof adds: all of it but the strip in front of taller walls."""
        return self.area_m2 - self.wall_m2

    @property
    def reason(self) -> str:
        """The filter that takes the whole roof out, in funnel order; "" if it counts. The wall strip is no reason."""
        if not self.housing:
            return "zone"
        return "very_low" if self.very_low else ""

    @property
    def counts(self) -> bool:
        return self.reason == ""


def find_roofs(parts: pd.DataFrame, zones: list[BaseGeometry]) -> list[Roof]:
    """Roofs of all buildings with at least MIN_ROOF_M2 of low flat parts (sources.read_parts), in building order."""
    height = parts["height_m"].to_numpy(dtype=float)
    low = (parts["flat"].to_numpy(dtype=bool) & ~parts["excluded"].to_numpy(dtype=bool)
           & (height >= HEIGHT_MIN_M) & (height < HEIGHT_MAX_M))
    low_parts = parts[low]
    area_by_building = low_parts.groupby("building")["ground_m2"].sum()
    candidates = set(area_by_building[area_by_building >= MIN_ROOF_M2].index)
    if not candidates:
        return []
    geometries = parts["geometry"].to_numpy()
    tree = shapely.STRtree(geometries)
    zone_tree = shapely.STRtree(zones)
    roofs = []
    for building, group in low_parts[low_parts["building"].isin(candidates)].groupby("building", sort=True):
        geom = shapely.union_all(group["geometry"].to_numpy())
        low_height = float(group["height_m"].max())
        area = float(group["ground_m2"].sum())
        point = geom.representative_point()
        roofs.append(Roof(
            building=building, use=group.loc[group["ground_m2"].idxmax(), "use"], area_m2=area, height_m=low_height,
            wall_m2=_wall_m2(geom, area, low_height, tree, geometries, height),
            very_low=low_height < VERY_LOW_M, housing=len(zone_tree.query(point, predicate="intersects")) > 0,
            geom=geom, x=point.x, y=point.y))
    return roofs


def _wall_m2(geom: BaseGeometry, area_m2: float, low_height: float, tree: shapely.STRtree,
             geometries: np.ndarray, height: np.ndarray) -> float:
    """The part of the roof within WALL_GAP_M of a taller wall. A wall is a part (of this or another building) within
    NEIGHBOUR_GAP_M of the roof and more than TALLER_BY_M higher. The area keeps the measure of the extract (ground_m2):
    the strip takes its share of the geometry."""
    near = tree.query(geom.buffer(NEIGHBOUR_GAP_M), predicate="intersects")
    walls = near[height[near] > low_height + TALLER_BY_M]  # NaN heights compare False
    if not len(walls) or geom.area == 0:
        return 0.0
    strip = geom.intersection(shapely.union_all(geometries[walls]).buffer(WALL_GAP_M))
    return area_m2 * strip.area / geom.area


def funnel(roofs: list[Roof]) -> dict[str, float]:
    """Sums in m² in the order of the filters: candidates minus the roofs out of a housing zone, minus the very low
    roofs, minus the wall strips of the counted roofs equals the counted area."""
    def total(reason: str | None = None) -> float:
        return float(sum(r.area_m2 for r in roofs if reason is None or r.reason == reason))
    counted = [r for r in roofs if r.counts]
    usable = float(sum(r.usable_m2 for r in counted))
    return {"candidates_m2": total(), "not_housing_m2": total("zone"), "very_low_m2": total("very_low"),
            "wall_m2": float(sum(r.wall_m2 for r in counted)), "counted_m2": usable,
            "modules": usable * MODULE_SHARE / MODULE_M2}


def _sums(roofs: list[Roof], areas: list[Area]) -> tuple[pd.DataFrame, np.ndarray]:
    ids = assign_points([r.x for r in roofs], [r.y for r in roofs], areas)
    sums = {a.id: 0.0 for a in areas}
    for r, area_id in zip(roofs, ids):
        if area_id is not None and r.counts:
            sums[area_id] += r.usable_m2
    return pd.DataFrame({"id": list(sums), "ROOF_FLAT": list(sums.values())}), ids


def area_values(roofs: list[Roof], districts: list[Area], quarters: list[Area]
                ) -> tuple[pd.DataFrame, pd.DataFrame, list[Roof], list[Roof]]:
    """Counted m² per district and per quarter (every area, 0 where none), by the representative point of each roof.

    Also returned: the roofs in no district (they drop out; the caller takes the funnel over the others) and the
    counted roofs in a district but in no quarter (the quarters then sum to less than the districts)."""
    district_table, district_ids = _sums(roofs, districts)
    quarter_table, quarter_ids = _sums(roofs, quarters)
    outside = [r for r, d in zip(roofs, district_ids) if d is None]
    no_quarter = [r for r, d, q in zip(roofs, district_ids, quarter_ids) if d is not None and q is None and r.counts]
    return district_table, quarter_table, outside, no_quarter
