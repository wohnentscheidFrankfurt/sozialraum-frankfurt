"""Reads features from WFS GML (3.1 or 3.2, with or without gml prefix)."""
from __future__ import annotations

import html
import re
from pathlib import Path

from shapely.geometry import Polygon
from shapely.ops import unary_union

from pipeline.shared.core.geometry import Feature

_LEAF = re.compile(r"<[A-Za-z_]+:([A-Za-z_0-9]+)>([^<>]*)</[A-Za-z_]+:\1>")
_POLYGON = re.compile(r"<(?:gml:)?Polygon\b.*?</(?:gml:)?Polygon>", re.S)
_POSLIST = re.compile(r"<(?:gml:)?posList[^>]*>(.*?)</(?:gml:)?posList>", re.S)


def _points(text: str) -> list[tuple[float, float]]:
    v = [float(x) for x in text.split()]
    return list(zip(v[0::2], v[1::2]))


def parse_features(text: str) -> list[Feature]:
    """props holds only leaf elements; geometries are joined polygons in the source CRS."""
    features = []
    for part in re.split(r"<(?:wfs:member|gml:featureMember)>", text)[1:]:
        props: dict[str, str] = {}
        for name, value in _LEAF.findall(part):
            if name != "posList":
                props.setdefault(name, html.unescape(" ".join(value.split())))
        polygons = []
        for pl in _POLYGON.findall(part):
            rings = _POSLIST.findall(pl)
            if rings:
                polygons.append(Polygon(_points(rings[0]), [_points(r) for r in rings[1:]]).buffer(0))
        features.append(Feature(props, unary_union(polygons) if polygons else None, part))
    return features


def read_features(path: Path) -> list[Feature]:
    return parse_features(path.read_text(encoding="utf-8"))


def count_with_area(features: list[Feature]) -> int:
    """The WFS check counts only features with an area."""
    return sum(1 for f in features if f.geom is not None)
