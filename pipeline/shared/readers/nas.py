"""ALKIS NAS (XML, NBA delivery of the Hessian land survey): parcels, buildings and land use as WKT.

Stdlib and pandas only. The file is large (6 GB), so the reader streams it with `iterparse` and clears each feature
and each `wfs:Insert` after use. A ring is the points of all `gml:posList` and `gml:pos` of its `gml:curveMember`
segments in document order. An arc (`gml:Arc`, `gml:ArcString`) becomes a polyline. Coordinates are EPSG:25832 and rounded to 0.01 m.
Source vocabulary of the use cases lives in their `sources.py`, not here.
"""
from __future__ import annotations

import math
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO

import pandas as pd

_ADV = "{http://www.adv-online.de/namespaces/adv/gid/7.1}"
_GML = "{http://www.opengis.net/gml/3.2}"
_WFS = "{http://www.opengis.net/wfs/2.0}"

# Land-use feature classes (without the prefix AX_).
LANDUSE_CLASSES = frozenset({
    "Wohnbauflaeche", "FlaecheGemischterNutzung", "IndustrieUndGewerbeflaeche",
    "FlaecheBesondererFunktionalerPraegung", "SportFreizeitUndErholungsflaeche", "Strassenverkehr", "Weg", "Platz",
    "Friedhof", "Landwirtschaft", "Wald", "Gehoelz", "UnlandVegetationsloseFlaeche", "Bahnverkehr", "Fliessgewaesser",
    "StehendesGewaesser", "Flugverkehr", "Schiffsverkehr", "Hafenbecken", "TagebauGrubeSteinbruch", "Sumpf", "Halde",
})

_POINT_TAGS = (_GML + "posList", _GML + "pos")


@dataclass(frozen=True)
class NasExtract:
    parcels: pd.DataFrame  # gml_id, kz, official_m2, created, addresses, wkt
    buildings: pd.DataFrame  # gml_id, function, wkt
    landuse: pd.DataFrame  # gml_id, cls, function, wkt
    portion_date: str  # ISO date of adv:AX_Portionskennung/adv:datum


_ARC_TAGS = (_GML + "Arc", _GML + "ArcString")
_MAX_STEP_DEG = 5.0
_MAX_CHORD_M = 1.0

Point = tuple[float, float]


def _element_points(element: ET.Element) -> list[Point]:
    points: list[Point] = []
    for child in element.iter():
        if child.tag not in _POINT_TAGS:
            continue
        values = [float(v) for v in (child.text or "").split()]
        dim = 2 if child.tag == _GML + "pos" else int(child.get("srsDimension", "2"))
        points += [(values[i], values[i + 1]) for i in range(0, len(values) - dim + 1, dim)]
    return points


def _densify_arc(start: Point, mid: Point, end: Point) -> list[Point]:
    """Points of the circular arc start -> mid -> end, every 5 degrees or at most 1 m apart. Collinear: straight."""
    (x1, y1), (x2, y2), (x3, y3) = start, mid, end
    det = 2 * (x1 * (y2 - y3) + x2 * (y3 - y1) + x3 * (y1 - y2))
    chord = math.hypot(x3 - x1, y3 - y1)
    if chord == 0 or abs(det) < 1e-9 * max(chord, 1.0) ** 2:
        return [start, mid, end]
    s1, s2, s3 = x1 * x1 + y1 * y1, x2 * x2 + y2 * y2, x3 * x3 + y3 * y3
    cx = (s1 * (y2 - y3) + s2 * (y3 - y1) + s3 * (y1 - y2)) / det
    cy = (s1 * (x3 - x2) + s2 * (x1 - x3) + s3 * (x2 - x1)) / det
    radius = math.hypot(x1 - cx, y1 - cy)
    a0, a2 = math.atan2(y1 - cy, x1 - cx), math.atan2(y3 - cy, x3 - cx)
    counter_clockwise = (x2 - x1) * (y3 - y1) - (y2 - y1) * (x3 - x1) > 0
    sweep = (a2 - a0) % (2 * math.pi) if counter_clockwise else -((a0 - a2) % (2 * math.pi))
    steps = max(math.ceil(abs(math.degrees(sweep)) / _MAX_STEP_DEG), math.ceil(radius * abs(sweep) / _MAX_CHORD_M), 2)
    points = [(cx + radius * math.cos(a0 + sweep * i / steps), cy + radius * math.sin(a0 + sweep * i / steps))
              for i in range(1, steps)]
    return [start, *points, end]


def _curve_points(element: ET.Element) -> list[Point]:
    """Points in document order. Arcs become dense polylines."""
    if element.tag in _ARC_TAGS:
        points = _element_points(element)
        dense = points[:1]
        for i in range(0, len(points) - 2, 2):
            dense += _densify_arc(*points[i:i + 3])[1:]
        return dense
    if element.tag in _POINT_TAGS:
        return _element_points(element)
    return [p for child in element for p in _curve_points(child)]


def _ring_points(ring: ET.Element) -> list[Point]:
    """Points of a ring in document order without repeats; the ring is closed."""
    points: list[Point] = []
    for x, y in _curve_points(ring):
        point = (round(x, 2), round(y, 2))
        if not points or points[-1] != point:
            points.append(point)
    if points and points[0] != points[-1]:
        points.append(points[0])
    return points


def _format(points: list[tuple[float, float]]) -> str:
    return "(" + ",".join(f"{x:.2f} {y:.2f}" for x, y in points) + ")"


def _wkt(feature: ET.Element) -> str:
    """MULTIPOLYGON of all polygon patches of the feature, "" if there is none."""
    polygons = []
    for patch in list(feature.iter(_GML + "PolygonPatch")) + list(feature.iter(_GML + "Polygon")):
        exterior = patch.find(_GML + "exterior")
        if exterior is None:
            continue
        outer = _ring_points(exterior)
        if len(outer) < 4:
            continue
        holes = [r for r in (_ring_points(i) for i in patch.findall(_GML + "interior")) if len(r) >= 4]
        polygons.append("(" + ",".join(_format(r) for r in [outer] + holes) + ")")
    return "MULTIPOLYGON(" + ",".join(polygons) + ")" if polygons else ""


def _text(feature: ET.Element, name: str) -> str:
    return (feature.findtext(_ADV + name) or "").strip()


def read_nas(stream: BinaryIO) -> NasExtract:
    parcels: list[dict] = []
    buildings: list[dict] = []
    landuse: list[dict] = []
    portion_date = ""
    for _, element in ET.iterparse(stream, events=("end",)):
        tag = element.tag
        if tag == _WFS + "Insert":
            element.clear()
        elif tag == _ADV + "AX_Portionskennung":
            portion_date = _text(element, "datum")[:10]
        elif tag == _ADV + "AX_Flurstueck":
            wkt = _wkt(element)
            if wkt:
                parcels.append({
                    "gml_id": element.get(_GML + "id"), "kz": _text(element, "flurstueckskennzeichen"),
                    "official_m2": float(_text(element, "amtlicheFlaeche") or "nan"),
                    "created": _text(element, "zeitpunktDerEntstehung"),
                    "addresses": len(element.findall(_ADV + "weistAuf")), "wkt": wkt})
            element.clear()
        elif tag == _ADV + "AX_Gebaeude":
            wkt = _wkt(element)
            if wkt:
                buildings.append({"gml_id": element.get(_GML + "id"), "function": _text(element, "gebaeudefunktion"),
                                  "wkt": wkt})
            element.clear()
        elif tag.startswith(_ADV + "AX_") and tag[len(_ADV) + 3:] in LANDUSE_CLASSES:
            wkt = _wkt(element)
            if wkt:
                landuse.append({"gml_id": element.get(_GML + "id"), "cls": tag[len(_ADV) + 3:],
                                "function": _text(element, "funktion"), "wkt": wkt})
            element.clear()
    return NasExtract(
        pd.DataFrame(parcels, columns=["gml_id", "kz", "official_m2", "created", "addresses", "wkt"]),
        pd.DataFrame(buildings, columns=["gml_id", "function", "wkt"]),
        pd.DataFrame(landuse, columns=["gml_id", "cls", "function", "wkt"]),
        portion_date)


def extract_package(zip_path: Path) -> NasExtract:
    """Read the one XML file inside the delivery ZIP (ValueError if it holds none or several)."""
    with zipfile.ZipFile(zip_path) as package:
        names = [n for n in package.namelist() if n.lower().endswith(".xml")]
        if len(names) != 1:
            raise ValueError(f"{zip_path}: {len(names)} XML files, expected 1 (the package „Alle Dateien“ holds a ZIP)")
        with package.open(names[0]) as stream:
            return read_nas(stream)
