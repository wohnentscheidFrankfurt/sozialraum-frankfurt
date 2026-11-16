"""CityGML 1.0 of the 3D-Gebäudemodell LoD2 (AdV profile): buildings with their parts, and the delivery notes.

Stdlib only. A building holds `bldg:BuildingPart` elements; a building without parts is one part itself. A part
counts only its ground surface (exterior rings) and the roof type and height of the model. Sources: pipeline/use_cases
of the flat roofs and sources/README.md (hessen/lod2).
"""
from __future__ import annotations

import io
import re
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, Iterator

_BLDG = "{http://www.opengis.net/citygml/building/1.0}"
_GML = "{http://www.opengis.net/gml}"
_CORE = "{http://www.opengis.net/citygml/1.0}"

Ring = tuple[tuple[float, float], ...]


@dataclass(frozen=True)
class Part:
    roof_type: str
    height_m: float | None
    ground_m2: float
    rings: tuple[Ring, ...]


@dataclass(frozen=True)
class Building:
    id: str
    function: str
    created: str  # core:creationDate, "" if missing
    parts: tuple[Part, ...]


def _area(ring: Ring) -> float:
    """Shoelace area on x and y, relative to the first point (UTM values lose digits in the products)."""
    if not ring:
        return 0.0
    x0, y0 = ring[0]
    return abs(sum((a[0] - x0) * (b[1] - y0) - (b[0] - x0) * (a[1] - y0) for a, b in zip(ring, ring[1:]))) / 2


def _ground_rings(element: ET.Element) -> tuple[Ring, ...]:
    """Exterior rings of the GroundSurface of this element (not of its parts), x and y only."""
    rings = []
    for bounded in element.findall(_BLDG + "boundedBy"):
        ground = bounded.find(_BLDG + "GroundSurface")
        if ground is None:
            continue
        for exterior in ground.iter(_GML + "exterior"):
            for pos in exterior.iter(_GML + "posList"):
                dim = int(pos.get("srsDimension", "3"))
                values = [float(v) for v in (pos.text or "").split()]
                rings.append(tuple((values[i], values[i + 1]) for i in range(0, len(values) - dim + 1, dim)))
    return tuple(rings)


def _part(element: ET.Element) -> Part:
    height = element.findtext(_BLDG + "measuredHeight")
    rings = _ground_rings(element)
    return Part(element.findtext(_BLDG + "roofType") or "", float(height) if height else None,
                sum(_area(r) for r in rings), rings)


def read_buildings(stream: BinaryIO) -> Iterator[Building]:
    """Buildings of one CityGML file in file order. Each element is cleared after use."""
    for _, element in ET.iterparse(stream, events=("end",)):
        if element.tag != _BLDG + "Building":
            continue
        parts = element.findall(_BLDG + "consistsOfBuildingPart/" + _BLDG + "BuildingPart")
        yield Building(element.get(_GML + "id") or "", element.findtext(_BLDG + "function") or "",
                       element.findtext(_CORE + "creationDate") or "",
                       tuple(_part(p) for p in parts) if parts else (_part(element),))
        element.clear()


def read_meta(text: str) -> tuple[int, str]:
    """(Anzahl der 3D-Gebäude, Lieferdatum as ISO date) of the txt file next to a gml file."""
    count = re.search(r"^Anzahl der 3D-Gebäude:\s*(\d+)\s*$", text, re.M)
    delivered = re.search(r"^Lieferdatum:\s*(\d{4}-\d{2}-\d{2})\s*$", text, re.M)
    if count is None or delivered is None:
        raise ValueError("Anzahl der 3D-Gebäude or Lieferdatum missing in the delivery note")
    return int(count.group(1)), delivered.group(1)


def _footprint(rings: tuple[Ring, ...]) -> str:
    return ";".join(" ".join(f"{x:.1f},{y:.1f}" for x, y in ring) for ring in rings)


def _signature(building: Building) -> tuple:
    return building.function, building.parts


def extract_package(package: Path) -> tuple[list[dict], list[dict]]:
    """Walks the ZIP of Gemarkung ZIPs. Returns the part rows of the unique buildings and one row per Gemarkung.
    A building that stands in two Gemarkungen must be identical in both; the first copy is kept."""
    rows: list[dict] = []
    gemarkungen: list[dict] = []
    seen: dict[str, tuple[str, tuple]] = {}
    with zipfile.ZipFile(package) as outer:
        for name in outer.namelist():
            if not name.lower().endswith(".zip"):
                continue
            with zipfile.ZipFile(io.BytesIO(outer.read(name))) as inner:
                gml = next(n for n in inner.namelist() if n.endswith("-LoD2.gml"))
                gemarkung = gml.rsplit("/", 1)[-1].removesuffix("-LoD2.gml")
                txt = next(n for n in inner.namelist() if n.endswith("-LoD2.txt"))
                count, delivered = read_meta(inner.read(txt).decode("utf-8"))
                parsed = 0
                with inner.open(gml) as stream:
                    for building in read_buildings(stream):
                        parsed += 1
                        if building.id in seen:
                            first, signature = seen[building.id]
                            if signature != _signature(building):
                                raise ValueError(f"{building.id} differs between {first} and {gemarkung}")
                            continue
                        seen[building.id] = (gemarkung, _signature(building))
                        for number, part in enumerate(building.parts):
                            rows.append({"building": building.id, "function": building.function,
                                         "gemarkung": gemarkung, "created": building.created[:4], "part": number,
                                         "roof_type": part.roof_type, "height_m": part.height_m,
                                         "ground_m2": round(part.ground_m2, 1), "footprint": _footprint(part.rings)})
                gemarkungen.append({"gemarkung": gemarkung, "buildings": count, "parsed": parsed,
                                    "delivered": delivered})
    return rows, gemarkungen
