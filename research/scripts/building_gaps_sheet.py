"""Judgement sheet of the building gaps (pipeline/use_cases/building_gaps/README.md): for every candidate past the cover
filters (model Candidate.judgeable) without a verdict row, an RGB and a CIR crop of the DOP20 WMS (0.2 m, flight
2025) with the parcel outline in magenta and the ALKIS buildings in cyan. The label names the slot, gml_id, area,
front, kind, cover shares, parcel year, address count and the position. PNG pages go to
research/results/building_gaps_sheet/ with index.csv (page, slot, gml_id).
The crops stay in cache/dop/ (<cache_stem>_rgb20.png, <cache_stem>_cir20.png).

Call from the repo root: .venv/bin/python -I research/scripts/building_gaps_sheet.py [--per-page 12] [--cols 3]
[--size 300] [--all] [--ids ID,ID] [--out FOLDER]"""
from __future__ import annotations

import argparse
import csv
import math
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import pymupdf  # noqa: E402
import shapely  # noqa: E402
from pyproj import Transformer  # noqa: E402

from pipeline import config as c  # noqa: E402
from pipeline.engine.download import download  # noqa: E402
from pipeline.use_cases.building_gaps.model import find_gaps, judge  # noqa: E402
from pipeline.use_cases.building_gaps.sources import (  # noqa: E402
    cache_stem, read_buildings, read_cover, read_landuse, read_parcels, read_verdicts, read_zones)

CONTEXT_M = 15  # the crop reaches this far around the parcel
RES_M = 0.2  # metres per pixel of the crop ...
MAX_PX = 2500  # ... unless a side would get more pixels than this
LAYERS = {"rgb": "he_dop20_rgb", "cir": "he_dop20_cir"}
MAGENTA, WHITE, CYAN = (1, 0, 1), (1, 1, 1), (0, 0.9, 1)
LABEL_PT = 10
LABEL_LINES = 3
GAP_PT = 6
WORKERS = 4
TO_WGS84 = Transformer.from_crs(25832, 4326, always_xy=True)


def box(geom) -> tuple[float, float, float, float, float]:
    """Crop box of a parcel (x0, y0, x1, y1 in EPSG:25832) and its metres per pixel."""
    bx0, by0, bx1, by1 = geom.bounds
    x0, y0, x1, y1 = (math.floor(bx0 - CONTEXT_M), math.floor(by0 - CONTEXT_M), math.ceil(bx1 + CONTEXT_M),
                      math.ceil(by1 + CONTEXT_M))
    return x0, y0, x1, y1, max(RES_M, max(x1 - x0, y1 - y0) / MAX_PX)


def crop_url(layer: str, x0: float, y0: float, x1: float, y1: float, res: float) -> str:
    w, h = round((x1 - x0) / res), round((y1 - y0) / res)
    return (f"{c.DOP_WMS}?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetMap&LAYERS={layer}&STYLES=&CRS=EPSG:25832"
            f"&BBOX={x0},{y0},{x1},{y1}&WIDTH={w}&HEIGHT={h}&FORMAT=image/png")


def crop_path(gml_id: str, kind: str) -> Path:
    return c.DOP_CACHE / f"{cache_stem(gml_id)}_{kind}20.png"


def rings(geom):
    for poly in shapely.get_parts(geom):
        if poly.geom_type == "Polygon" and not poly.is_empty:
            yield poly.exterior.coords
            for hole in poly.interiors:
                yield hole.coords


def label(slot: int, cand) -> list[str]:
    g, cov = cand.gap, cand.cover or {}
    lon, lat = TO_WGS84.transform(g.x, g.y)
    shares = " ".join(f"{k[0]}{cov.get(k, float('nan')):.0%}" for k in ("building", "tree", "green", "open"))
    return [f"#{slot} {g.gml_id}  {g.area_m2:,.0f} m²  {g.kind}",
            f"front {g.front_m:.0f} m wall {g.wall_m:.0f} m  {shares}",
            f"created {g.created[:4] or '?'}  addr {g.addresses}  {lat:.5f} N {lon:.5f} E"]


def draw_cell(page, cand, buildings, tree, left: float, top: float, size: float) -> None:
    g = cand.gap
    x0, y0, x1, y1, _ = box(g.geom)
    scale = size / max(x1 - x0, y1 - y0)
    frame = shapely.box(x0, y0, x1, y1)
    near = shapely.intersection(buildings[tree.query(frame, predicate="intersects")], frame)
    for n, kind in enumerate(("rgb", "cir")):
        ox = left + n * (size + GAP_PT)
        rect = pymupdf.Rect(ox, top, ox + (x1 - x0) * scale, top + (y1 - y0) * scale)
        page.insert_image(rect, filename=str(crop_path(g.gml_id, kind)))

        def pt(x, y):
            return pymupdf.Point(ox + (x - x0) * scale, top + (y1 - y) * scale)

        shape = page.new_shape()
        for b in near:
            for ring in rings(b):
                shape.draw_polyline([pt(x, y) for x, y in ring])
        shape.finish(color=CYAN, width=0.8, closePath=True)
        for color, width in ((WHITE, 3.2), (MAGENTA, 1.8)):
            for ring in rings(g.geom):
                shape.draw_polyline([pt(x, y) for x, y in ring])
            shape.finish(color=color, width=width, closePath=True)
        shape.commit()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-page", type=int, default=12)
    ap.add_argument("--cols", type=int, default=3)
    ap.add_argument("--size", type=float, default=300, help="side of one crop in pixels")
    ap.add_argument("--all", action="store_true", help="also the candidates that have a verdict row")
    ap.add_argument("--ids", default="", help="only these gml_ids, comma-separated")
    ap.add_argument("--out", type=Path, default=ROOT / "research" / "results" / "building_gaps_sheet")
    args = ap.parse_args()

    buildings_table = read_buildings(c.ALKIS_BUILDINGS_CSV)
    gaps, _ = find_gaps(read_parcels(c.ALKIS_PARCELS_CSV), buildings_table, read_landuse(c.ALKIS_LANDUSE_CSV))
    candidates = judge(gaps, read_zones(c.BORIS_DIR), read_cover(c.BUILDING_GAPS_COVER_CSV),
                       read_verdicts(c.BUILDING_GAPS_REFERENCE_CSV))
    wanted = set(filter(None, args.ids.split(",")))
    todo = [x for x in candidates if x.judgeable and (args.all or x.verdict is None)
            and (not wanted or x.gap.gml_id in wanted)]
    print(f"{len(gaps)} gaps, {sum(x.judgeable for x in candidates)} past the cover filters, "
          f"{sum(x.drawn for x in candidates)} drawn, {len(todo)} on the sheet")
    if not todo:
        print(f"nothing to draw; the pages and index.csv in {args.out} stay as they are")
        return

    def fetch(cand) -> None:
        x0, y0, x1, y1, res = box(cand.gap.geom)
        for kind, layer in LAYERS.items():
            download(crop_url(layer, x0, y0, x1, y1, res), crop_path(cand.gap.gml_id, kind))

    with ThreadPoolExecutor(WORKERS) as pool:
        list(pool.map(fetch, todo))  # list(): raise the errors of the workers

    buildings = buildings_table["geometry"].to_numpy()
    tree = shapely.STRtree(buildings)
    args.out.mkdir(parents=True, exist_ok=True)
    for old in args.out.glob("page_*.png"):
        old.unlink()
    cell_w, cell_h = 2 * args.size + 3 * GAP_PT, args.size + LABEL_LINES * (LABEL_PT + 2) + 2 * GAP_PT
    rows_per_page = math.ceil(args.per_page / args.cols)
    index = []
    for p, start in enumerate(range(0, len(todo), args.per_page), 1):
        doc = pymupdf.open()
        page = doc.new_page(width=args.cols * cell_w, height=rows_per_page * cell_h)
        page.draw_rect(page.rect, color=None, fill=WHITE)
        for i, cand in enumerate(todo[start:start + args.per_page]):
            slot = start + i + 1
            left, top = (i % args.cols) * cell_w + GAP_PT, (i // args.cols) * cell_h + GAP_PT
            draw_cell(page, cand, buildings, tree, left, top, args.size)
            for n, line in enumerate(label(slot, cand)):
                page.insert_text((left, top + args.size + (n + 1) * (LABEL_PT + 2)), line, fontsize=LABEL_PT)
            index.append({"page": p, "slot": slot, "gml_id": cand.gap.gml_id, "kz": cand.gap.kz,
                          "area_m2": round(cand.gap.area_m2), "created": cand.gap.created[:10],
                          "addresses": cand.gap.addresses})
        page.get_pixmap(dpi=72).save(args.out / f"page_{p:02d}.png")
    with open(args.out / "index.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["page", "slot", "gml_id", "kz", "area_m2", "created", "addresses"])
        writer.writeheader()
        writer.writerows(index)
    print(f"{len(index)} candidates on {math.ceil(len(index) / args.per_page)} pages in {args.out}")


if __name__ == "__main__":
    main()
