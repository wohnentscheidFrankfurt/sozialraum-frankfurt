"""Low flat roofs: the funnel of the build, the variants of the rule at taller walls, and the roof candidates by BORIS
zone class and by AdV function (research/2026-11-10-flat-roofs.md). Runs the model of the use case `flat_roofs` on the
sources, as the build does.

  .venv/bin/python -I research/scripts/flat_roofs_breakdown.py > research/results/2026-11-10-flat-roofs.txt
"""
import sys

import pandas as pd
import shapely

sys.path.insert(0, ".")
from pipeline import config
from pipeline.shared.readers.gml import parse_features
from pipeline.use_cases.flat_roofs import model
from pipeline.use_cases.flat_roofs.model import (MODULE_M2, MODULE_SHARE, NEIGHBOUR_GAP_M, TALLER_BY_M, WALL_GAP_M,
                                                 find_roofs, funnel)
from pipeline.use_cases.flat_roofs.sources import _MUNICIPALITY, name_of, read_parts, read_zones

CLASSES = ["housing (W, M; development state B)", "Gemeinbedarf (GB)", "commerce (G, GE, GI)", "other"]


def all_zones() -> list[tuple[str, str, object]]:
    """Every BORIS zone of Frankfurt as (art, development state, geometry). The build keeps W and M with state B."""
    zones = []
    for path in sorted(config.BORIS_DIR.glob("boris_*.gml")):
        for f in parse_features(path.read_text(encoding="utf-8")):
            m = _MUNICIPALITY.search(f.raw)
            if f.geom is not None and m and m.group(1).strip() == "Frankfurt am Main":
                zones.append((f.props.get("art", ""), f.props.get("entwicklungszustand", ""), f.geom))
    return zones


def zone_class(art: str) -> str:
    if art.startswith("GB"):
        return CLASSES[1]
    if art[:1] == "G":
        return CLASSES[2]
    return CLASSES[3]


def classify(roofs, zones) -> list[str]:
    """Housing as in the build (zones of read_zones); else the class of the first other zone at the point, else other."""
    housing = shapely.STRtree(read_zones(config.BORIS_DIR))
    others = shapely.STRtree([g for _, _, g in zones])
    out = []
    for r in roofs:
        point = shapely.Point(r.x, r.y)
        if len(housing.query(point, predicate="intersects")):
            out.append(CLASSES[0])
            continue
        hits = others.query(point, predicate="intersects")
        classes = {zone_class(zones[i][0]) for i in hits}
        out.append(next((c for c in CLASSES[1:3] if c in classes), CLASSES[3]))
    return out


def old_taller(parts: pd.DataFrame, roofs) -> list[bool]:
    """The rule of the first version (variant A): a building within NEIGHBOUR_GAP_M, or any part of the same building
    (touching or not), is more than TALLER_BY_M higher than the roof. Such a roof dropped out as a whole."""
    highest = parts.groupby("building")["height_m"].max().fillna(0.0)
    tree = shapely.STRtree(parts["geometry"].to_numpy())
    building_of = parts["building"].to_numpy()
    out = []
    for r in roofs:
        near = set(building_of[tree.query(r.geom.buffer(NEIGHBOUR_GAP_M), predicate="intersects")]) - {r.building}
        neighbour = float(highest[list(near)].max()) if near else 0.0
        out.append(max(neighbour, float(highest[r.building])) > r.height_m + TALLER_BY_M)
    return out


def counted_with_gap(parts: pd.DataFrame, zones, gap: float) -> float:
    """Counted m² with another strip width. The model reads WALL_GAP_M at call time."""
    model.WALL_GAP_M = gap
    try:
        return funnel(find_roofs(parts, zones))["counted_m2"]
    finally:
        model.WALL_GAP_M = WALL_GAP_M


def table(frame: pd.DataFrame, key: str, order=None) -> str:
    g = frame.groupby(key).agg(roofs=("area_m2", "size"), area_m2=("area_m2", "sum"))
    g["counted_roofs"] = frame[frame["counts"]].groupby(key).size().reindex(g.index).fillna(0).astype(int)
    g["counted_m2"] = frame[frame["counts"]].groupby(key)["usable_m2"].sum().reindex(g.index).fillna(0)
    g = g.reindex(order) if order else g.sort_values("area_m2", ascending=False)
    g.loc["total"] = g.sum()
    return g.fillna(0).astype({"roofs": int, "counted_roofs": int}).round(0).to_string(float_format=lambda v: f"{v:,.0f}")


parts = read_parts(config.LOD2_PARTS_CSV)
housing_zones = read_zones(config.BORIS_DIR)
roofs = find_roofs(parts, housing_zones)
f = funnel(roofs)
counted = [r for r in roofs if r.counts]
print("Funnel (all candidates, m²)")
print(f"candidates:           {len(roofs):>6} roofs  {f['candidates_m2']:>12,.0f}")
print(f"- not in housing zone:  {sum(r.reason == 'zone' for r in roofs):>4} roofs  {f['not_housing_m2']:>12,.0f}")
print(f"- under 3.2 m:          {sum(r.reason == 'very_low' for r in roofs):>4} roofs  {f['very_low_m2']:>12,.0f}")
print(f"- wall strip ({WALL_GAP_M} m):    {sum(r.wall_m2 > 0 for r in counted):>4} roofs  {f['wall_m2']:>12,.0f}")
print(f"= counted:            {len(counted):>6} roofs  {f['counted_m2']:>12,.0f}")
print(f"x {MODULE_SHARE} / {MODULE_M2:.0f} m² = {f['modules']:,.0f} modules (own estimate)")
print(f"counted roofs that lose all of their area to the strip: {sum(r.usable_m2 <= 0.01 for r in counted)}; "
      f"smallest rest {min(r.usable_m2 for r in counted if r.wall_m2 > 0):,.1f} m²")

print("\nVariants of the rule at taller walls (counted m²)")
taller = old_taller(parts, roofs)
whole_out = sum(r.area_m2 for r, t in zip(roofs, taller) if r.counts and not t)
print(f"A  whole roof out (first version):     {sum(r.counts and not t for r, t in zip(roofs, taller)):>5} roofs "
      f"{whole_out:>10,.0f}")
print(f"B  no rule:                            {len(counted):>5} roofs {sum(r.area_m2 for r in counted):>10,.0f}")
three = counted_with_gap(parts, housing_zones, 3.0)
print(f"C  strip of 3 m:                       {len(counted):>5} roofs {three:>10,.0f}")
print(f"C  strip of {WALL_GAP_M} m (build):             {len(counted):>5} roofs {f['counted_m2']:>10,.0f}")

any_state = shapely.STRtree([g for art, _, g in all_zones() if art[:1] in ("W", "M")])
extra = [r for r in roofs if r.reason == "zone" and not r.very_low
         and len(any_state.query(shapely.Point(r.x, r.y), predicate="intersects"))]
print(f"\nRoofs that would count with W and M zones of any development state: {len(extra)} roofs, "
      f"{sum(r.usable_m2 for r in extra):,.0f} m² (without their strips)")

frame = pd.DataFrame({"area_m2": [r.area_m2 for r in roofs], "usable_m2": [r.usable_m2 for r in roofs],
                      "counts": [r.counts for r in roofs], "function": [f"{r.use} {name_of(r.use)}" for r in roofs],
                      "reason": [r.reason or "counts" for r in roofs]})
frame["zone"] = classify(roofs, all_zones())
print("\nBy BORIS zone class (counted_m2 without the wall strips)")
print(table(frame, "zone", CLASSES))
print("\nBy reason")
print(table(frame, "reason", ["counts", "zone", "very_low"]))
print("\nBy AdV function (all candidates)")
print(table(frame, "function"))
print("\nBy AdV function (zone class housing only)")
print(table(frame[frame["zone"] == CLASSES[0]], "function"))
