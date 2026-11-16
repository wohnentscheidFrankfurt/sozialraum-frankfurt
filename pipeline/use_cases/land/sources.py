"""BORIS Hessen land value zones (sources/hessen/boris/), their values of 2026 and pending development plans (planAS
WFS)."""
from __future__ import annotations

import csv
import re
from pathlib import Path

from pipeline.shared.core.geometry import Feature, Site
from pipeline.shared.readers.gml import parse_features
from pipeline.use_cases.land.model import Zone

_MUNICIPALITY = re.compile(r"<boris:BR_Gemeinde>.*?<boris:name>([^<]*)</boris:name>", re.S)


def is_residential_zone(municipality: str, development_state: str, use: str) -> bool:
    """Frankfurt, building land ("B"), residential or mixed use (W…, M…)."""
    return municipality == "Frankfurt am Main" and development_state == "B" and use[:1] in ("W", "M")


def read_zones(folder: Path) -> list[Zone]:
    zones = []
    for path in sorted(folder.glob("boris_*.gml")):
        for f in parse_features(path.read_text(encoding="utf-8")):
            m = _MUNICIPALITY.search(f.raw)
            if f.geom is not None and m and is_residential_zone(m.group(1).strip(), f.props.get("entwicklungszustand", ""),
                                                                 f.props.get("art", "")):
                zones.append(Zone(f.geom, float(f.props["bodenrichtwert"]), f.props.get("art", ""),
                                  f.props["bodenrichtwertNummer"], f.props.get("ergaenzung", "")))
    return zones


def read_values(path: Path) -> dict[str, tuple[float, str]]:
    """Value in €/m² and Stichtag per zone number (sources/hessen/boris/values_2026.csv); numbers without a value
    are left out."""
    with path.open(encoding="utf-8", newline="") as f:
        return {r["number"]: (float(r["value"]), r["as_of"]) for r in csv.DictReader(f) if r["value"]}


def read_pending_plans(features: list[Feature]) -> list[Site]:
    return [Site(f.props.get("titel", ""), f.props.get("projekt_nr", ""), f.geom) for f in features if f.geom is not None]
