"""Building gaps (Baulücken): unbuilt ALKIS parcels at a street that are wide enough and used for housing. Pure."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
import shapely
from shapely.geometry.base import BaseGeometry

from pipeline.shared.geography.model import Area, assign_points

MAIN_MIN_M2 = 30  # a building is a main building from this footprint (and when its function is no minor one)
BUILT_MAX_M2 = 20  # a parcel counts as unbuilt under this much main building ...
BUILT_MAX_SHARE = 0.05  # ... or under this share of its area, whichever is larger
MIN_AREA_M2 = 300  # smallest parcel
HOUSING_SHARE_MIN = 0.8  # share of the parcel in a housing land use
HALF_WIDTH_M = 7.5  # a circle of 15 m fits into the parcel
FRONT_TOLERANCE_M = 1.5  # a street edge counts as the front within this distance
MIN_FRONT_M = 15  # smallest front
WALL_TOLERANCE_M = 0.3  # a neighbour wall counts within this distance
WALL_MIN_M = 5  # a row gap needs this much neighbour wall
FREE_FRONT_M = 30  # a free gap needs this much front
HIGH_M = 2.5  # cover: a pixel is high from this height above ground
NDVI_GREEN = 0.2  # cover: a pixel is green from this NDVI
GREEN_MAX = 0.5  # cover: a parcel with more green than this is no gap
BUILDING_MAX = 0.10  # cover: a parcel with more building than this is no gap
OPEN_MIN = 0.5  # cover: a parcel counts as open from this share of open ground
NAN_WARN = 0.05  # cover: share of pixels without value that gives a warning
SIMPLIFY_M = 0.5  # simplification of the overlay geometry

# "parcels" is the count of all parcels, every other key the parcels dropped at that step, in order.
GEOMETRY_STEPS = ("parcels", "main_building", "small", "use", "narrow", "front", "no_wall")


@dataclass(frozen=True)
class Gap:
    gml_id: str
    kz: str
    area_m2: float
    front_m: float
    wall_m: float
    kind: str  # "row" | "free"
    created: str
    addresses: int
    geom: BaseGeometry  # EPSG:25832
    x: float  # representative point
    y: float


def _polygonal(geom: BaseGeometry) -> BaseGeometry:
    """make_valid may return a GeometryCollection: keep the polygons."""
    if geom.geom_type in ("Polygon", "MultiPolygon"):
        return geom
    polygons = [g for g in shapely.get_parts(geom) if g.geom_type in ("Polygon", "MultiPolygon")]
    return shapely.union_all(polygons) if polygons else shapely.Polygon()


def _valid(geoms: np.ndarray) -> np.ndarray:
    bad = ~shapely.is_valid(geoms)
    if bad.any():
        geoms = geoms.copy()
        geoms[bad] = [_polygonal(shapely.make_valid(g)) for g in geoms[bad]]
    return geoms


def _sum_by_first(first: np.ndarray, weights: np.ndarray, size: int) -> np.ndarray:
    return np.bincount(first, weights=weights, minlength=size)


def _front(near: BaseGeometry) -> float:
    """Length of the front: the boundary within FRONT_TOLERANCE_M of access, piece by piece. Each open piece also runs
    FRONT_TOLERANCE_M up the side edge at both ends; that much is taken off (a closed ring keeps its length). The
    line parts are merged first, also out of a GeometryCollection (a corner touches the buffer at a point): the ring
    can start inside the front and split it."""
    parts = [g for g in shapely.get_parts(near) if g.geom_type in ("LineString", "LinearRing", "MultiLineString")]
    if not parts:
        return 0.0
    lines = shapely.line_merge(shapely.union_all(parts))
    total = 0.0
    for part in shapely.get_parts(lines):
        if part.geom_type not in ("LineString", "LinearRing"):
            continue
        total += part.length if part.is_closed else max(part.length - 2 * FRONT_TOLERANCE_M, 0.0)
    return total


def find_gaps(parcels: pd.DataFrame, buildings: pd.DataFrame, landuse: pd.DataFrame) -> tuple[list[Gap], dict[str, int]]:
    """Rule steps 1 to 6. parcels: gml_id, kz, created, addresses, geometry. buildings: main, geometry. landuse:
    housing, access, geometry. Returns the gaps (sorted by gml_id) and the count per step of GEOMETRY_STEPS."""
    counts = {"parcels": len(parcels)}
    table = parcels.reset_index(drop=True)
    geoms = _valid(table["geometry"].to_numpy())
    area = shapely.area(geoms)
    keep = np.ones(len(table), dtype=bool)

    def drop(step: str, ok: np.ndarray) -> None:
        nonlocal keep
        counts[step] = int((keep & ~ok).sum())
        keep = keep & ok

    # 1 no main building (the area of the geometry, not the official one)
    main = _valid(buildings.loc[buildings["main"], "geometry"].to_numpy())
    tree = shapely.STRtree(main)
    p, b = tree.query(geoms, predicate="intersects")
    built = _sum_by_first(p, shapely.area(shapely.intersection(geoms[p], main[b])), len(table))
    drop("main_building", built < np.maximum(BUILT_MAX_M2, BUILT_MAX_SHARE * area))
    # 2 area
    drop("small", area >= MIN_AREA_M2)
    # 3 housing use
    uses = _valid(landuse["geometry"].to_numpy())
    housing = landuse["housing"].to_numpy(dtype=bool)
    p, u = shapely.STRtree(uses).query(geoms, predicate="intersects")
    inside = shapely.area(shapely.intersection(geoms[p], uses[u])) * housing[u]
    drop("use", _sum_by_first(p, inside, len(table)) / np.where(area > 0, area, 1) >= HOUSING_SHARE_MIN)
    # 4 width: a circle of 15 m fits
    idx = np.flatnonzero(keep)
    wide = np.zeros(len(table), dtype=bool)
    wide[idx] = ~shapely.is_empty(shapely.buffer(geoms[idx], -HALF_WIDTH_M))
    drop("narrow", wide)
    # 5 front at a street, a way or a square (not a parking lot)
    access = uses[landuse["access"].to_numpy(dtype=bool)]
    front = np.zeros(len(table))
    if len(access):
        zone = shapely.buffer(shapely.union_all(access), FRONT_TOLERANCE_M)
        shapely.prepare(zone)
        front[idx] = [_front(line) for line in shapely.intersection(shapely.boundary(geoms[idx]), zone)]
    drop("front", front >= MIN_FRONT_M)
    # 6 neighbour wall or a wide front
    idx = np.flatnonzero(keep)
    boundary = shapely.boundary(geoms[idx])
    c, b = tree.query(boundary, predicate="dwithin", distance=WALL_TOLERANCE_M)
    along = shapely.length(shapely.intersection(boundary[c], shapely.buffer(main[b], WALL_TOLERANCE_M)))
    wall = np.zeros(len(table))
    wall[idx] = _sum_by_first(c, along, len(idx))
    drop("no_wall", (wall >= WALL_MIN_M) | (front >= FREE_FRONT_M))

    rows = np.flatnonzero(keep)
    points = shapely.point_on_surface(geoms[rows])
    gaps = [Gap(gml_id=str(table["gml_id"][i]), kz=str(table["kz"][i]), area_m2=float(area[i]),
                front_m=float(front[i]), wall_m=float(wall[i]), kind="row" if wall[i] >= WALL_MIN_M else "free",
                created=str(table["created"][i]), addresses=int(table["addresses"][i]), geom=geoms[i],
                x=float(shapely.get_x(pt)), y=float(shapely.get_y(pt)))
            for i, pt in zip(rows, points)]
    return sorted(gaps, key=lambda g: g.gml_id), counts


def ndvi(cir: np.ndarray) -> np.ndarray:
    """NDVI of a CIR image (H x W x 3): band 0 is near infrared, band 1 red."""
    return (cir[..., 0] - cir[..., 1]) / np.maximum(cir[..., 0] + cir[..., 1], 1)


def cover_shares(geom: BaseGeometry, ndom: np.ndarray, ndvi: np.ndarray, x0: int, y1: int) -> dict[str, float]:
    """Cover classes of the pixels whose centre lies in geom.

    The grids hold 1 m pixels, row 0 in the north, the west edge at x0 and the north edge at y1. A pixel without nDOM
    counts only in nan_share. The four classes are shares of the valid pixels."""
    rows, cols = ndom.shape
    x, y = np.meshgrid(x0 + 0.5 + np.arange(cols), y1 - 0.5 - np.arange(rows))
    inside = shapely.contains_xy(geom, x, y)
    px = int(inside.sum())
    valid = inside & ~np.isnan(ndom)
    n = int(valid.sum())
    high, green = ndom[valid] >= HIGH_M, ndvi[valid] >= NDVI_GREEN

    def share(mask: np.ndarray) -> float:
        return float(mask.sum() / n) if n else 0.0

    return {"px": px, "building": share(high & ~green), "tree": share(high & green), "green": share(~high & green),
            "open": share(~high & ~green), "nan_share": float((px - n) / px) if px else 0.0}


COUNT_REASONS = ("parking", "yard", "storage", "brownfield")  # a hand verdict "counts" names one of these
NOT_REASONS = ("new_building", "construction", "new_area", "green", "square", "school", "play", "access", "other")
VERDICTS = ("counts", "not", "site")  # "site": the aerial image does not decide, a visit is needed
BY = ("aerial", "site")

# Smallest area (m²) of each suitability, in ascending order. A gap fits the largest one at or under its area.
SUITABILITY = ((300, "coop"), (365, "house_for_all"), (1270, "student"), (2000, "multi_family"), (5400, "complex"))

# Parcels dropped after the geometry steps, in funnel order. "no_verdict" is last: it is the work still to do.
CANDIDATE_STEPS = ("zone", "no_cover", "green", "built", "not_open", "not", "site", "no_verdict")
_JUDGEABLE = ("", "not", "site", "no_verdict")  # past the cover filters: a gap for the hand verdict
# The map draws these. A gap judged not, or not judged yet (after a new delivery), stays in the funnel and the checks.
_DRAWN = ("", "site")


def suitability(area_m2: float) -> str:
    """Key of the largest SUITABILITY threshold at or under the area (only gaps from MIN_AREA_M2 are asked)."""
    key = SUITABILITY[0][1]
    for threshold, name in SUITABILITY:
        if area_m2 >= threshold:
            key = name
    return key


@dataclass(frozen=True)
class Candidate:
    gap: Gap
    housing: bool  # the representative point lies in a housing zone
    cover: dict | None  # cover shares, None if the gap was not measured
    verdict: dict | None  # hand verdict row, None if not judged

    @property
    def reason(self) -> str:
        """The filter that takes the gap out, in funnel order; "" if it counts."""
        if not self.housing:
            return "zone"
        if self.cover is None or self.cover["px"] == 0 or self.cover["nan_share"] >= 1:
            return "no_cover"  # not measured, or no valid height pixel (the shares would all read 0)
        if self.cover["tree"] + self.cover["green"] > GREEN_MAX:
            return "green"
        if self.cover["building"] > BUILDING_MAX:
            return "built"
        if self.cover["open"] < OPEN_MIN:
            return "not_open"
        if self.verdict is None:
            return "no_verdict"
        # a value outside VERDICTS does not count: it reads as not yet judged (the check reports it as FAIL)
        return {"counts": "", "not": "not", "site": "site"}.get(self.verdict["verdict"], "no_verdict")

    @property
    def judgeable(self) -> bool:
        """The gap passed zone and cover: it needs a hand verdict."""
        return self.reason in _JUDGEABLE

    @property
    def drawn(self) -> bool:
        """The map draws the gap: it counts or must be checked on site."""
        return self.reason in _DRAWN

    @property
    def counts(self) -> bool:
        return self.reason == ""


def judge(gaps: list[Gap], zones: list[BaseGeometry], cover: pd.DataFrame, verdicts: pd.DataFrame) -> list[Candidate]:
    """Zone, cover and verdict of each gap, in the order of gaps. cover is indexed by gml_id, verdicts has a gml_id column."""
    zone_tree = shapely.STRtree(zones)
    cover_rows = cover.to_dict("index")
    verdict_rows = {r["gml_id"]: r for r in verdicts.to_dict("records")}
    return [Candidate(gap=g, housing=len(zone_tree.query(shapely.Point(g.x, g.y), predicate="intersects")) > 0,
                      cover=cover_rows.get(g.gml_id), verdict=verdict_rows.get(g.gml_id)) for g in gaps]


def funnel(geometry_counts: dict[str, int], candidates: list[Candidate]) -> dict[str, float]:
    """The geometry counts, then the gaps dropped at each of CANDIDATE_STEPS, the counted gaps and their area.
    parcels minus every drop equals counted."""
    out: dict[str, float] = dict(geometry_counts)
    for step in CANDIDATE_STEPS:
        out[step] = sum(1 for c in candidates if c.reason == step)
    counted = [c for c in candidates if c.counts]
    out["counted"] = len(counted)
    out["counted_m2"] = float(sum(c.gap.area_m2 for c in counted))
    return out


def _sums(candidates: list[Candidate], areas: list[Area]) -> tuple[pd.DataFrame, list]:
    ids = assign_points([c.gap.x for c in candidates], [c.gap.y for c in candidates], areas)
    sums = {a.id: 0.0 for a in areas}
    for c, area_id in zip(candidates, ids):
        if area_id is not None and c.counts:
            sums[area_id] += c.gap.area_m2
    return pd.DataFrame({"id": list(sums), "GAP_AREA": list(sums.values())}), ids


def area_values(candidates: list[Candidate], districts: list[Area], quarters: list[Area]
                ) -> tuple[pd.DataFrame, pd.DataFrame, list[Candidate], list[Candidate]]:
    """Counted m² per district and per quarter (every area, 0 where none), by the representative point of each gap.

    Only drawn candidates enter. Also returned: the drawn candidates in no district, and the counted ones in a district
    but in no quarter (the quarters then sum to less than the districts)."""
    drawn = [c for c in candidates if c.drawn]
    district_table, district_ids = _sums(drawn, districts)
    quarter_table, quarter_ids = _sums(drawn, quarters)
    outside = [c for c, d in zip(drawn, district_ids) if d is None]
    no_quarter = [c for c, d, q in zip(drawn, district_ids, quarter_ids) if d is not None and q is None and c.counts]
    return district_table, quarter_table, outside, no_quarter
