"""Geometry helpers: features, transformations between EPSG:3035, EPSG:25832 and WGS84, GeoJSON."""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import NamedTuple

import numpy as np
from pyproj import Transformer
from shapely.geometry import mapping
from shapely.ops import transform

from pipeline.shared.core.texts import Texts


class Feature(NamedTuple):
    """A feature read from GML: leaf properties, geometry in EPSG:25832 (or None), raw text."""
    props: dict[str, str]
    geom: object
    raw: str


@dataclass(frozen=True)
class Site:
    """A named area from a source: a statute or a plan."""
    title: str
    project_no: str
    geom: object
    date: str = ""  # ISO date from the source, may be empty


_TO_25832 = Transformer.from_crs(3035, 25832, always_xy=True)
_25832_TO_WGS84 = Transformer.from_crs(25832, 4326, always_xy=True)
_3035_TO_WGS84 = Transformer.from_crs(3035, 4326, always_xy=True)


def to_25832(xs, ys):
    return _TO_25832.transform(np.asarray(xs, dtype=float), np.asarray(ys, dtype=float))


def from_3035_to_wgs84(xs, ys):
    return _3035_TO_WGS84.transform(xs, ys)


def _round(obj):
    if isinstance(obj, float):
        return round(obj, 5)
    if isinstance(obj, (list, tuple)):
        return [_round(x) for x in obj]
    if isinstance(obj, dict):
        return {k: _round(v) for k, v in obj.items()}
    return obj


def to_wgs84(geom, tolerance_m: float = 5.0) -> dict:
    g = geom.simplify(tolerance_m, preserve_topology=True) if tolerance_m else geom
    return _round(mapping(transform(_25832_TO_WGS84.transform, g)))


def feature_collection(entries) -> dict:
    """entries: iterable of (properties, geometry in EPSG:25832, tolerance in m)."""
    return {"type": "FeatureCollection", "features": [
        {"type": "Feature", "properties": p, "geometry": to_wgs84(g, t)}
        for p, g, t in entries if g is not None and not g.is_empty]}


def site_properties(site) -> dict:
    return {"title": site.title, "project_no": site.project_no}


def iso_date(iso: str) -> dt.date | None:
    """'1993-02-25' -> the date; dates that cannot be read give None."""
    try:
        return dt.date.fromisoformat(iso[:10])
    except ValueError:
        return None


def site_properties_with_date(site, t: Texts) -> dict:
    """The title and number of the site, and its date written in the language of t ("" if it cannot be read)."""
    day = iso_date(site.date)
    return site_properties(site) | {"date": t.date(day) if day else ""}
