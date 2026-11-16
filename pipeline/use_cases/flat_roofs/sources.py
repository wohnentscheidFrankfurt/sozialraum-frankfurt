"""LoD2 parts extract (sources/hessen/lod2/), BORIS housing zones and the HBO synopsis; the source vocabulary of low
flat roofs."""
from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd
import shapely
from shapely.geometry.base import BaseGeometry

from pipeline.shared.readers.gml import parse_features
from pipeline.shared.readers.pdf import page_texts

FLAT_ROOF = "1000"  # AdV roofType: Flachdach

# Gebäudefunktion of the AdV code list (AX_Gebaeude, Kennung 31001) for the codes among the roof candidates. Names from
# the ALKIS Objektartenkatalog (AdV, GeoInfoDok 7.x) as printed in the ALKIS-OK Berlin
# (https://www.berlin.de/sen/stadt/_assets/service/rechtsvorschriften/bereich-geoportal/liegenschaftskataster/alkis-ok_berlin.pdf).
# 31001_2073 (one roof of 274 m²) is not in that list. 31001_9998 reads "Nach Quellenlage nicht zu spezifizieren", which
# confuses a first-time reader. Both read "Gebäude", like every unknown code.
FUNCTION_NAMES: dict[str, str] = {
    "31001_1000": "Wohngebäude",
    "31001_1100": "Gemischt genutztes Gebäude mit Wohnen",
    "31001_2000": "Gebäude für Wirtschaft oder Gewerbe",
    "31001_2050": "Geschäftsgebäude",
    "31001_2460": "Gebäude zum Parken",
    "31001_2461": "Parkhaus",
    "31001_2512": "Pumpstation",
    "31001_3000": "Gebäude für öffentliche Zwecke",
    "31001_3010": "Verwaltungsgebäude",
    "31001_3044": "Gemeindehaus",
    "31001_3072": "Feuerwehr",
}

# Functions that are no roof for modules. Names as in the AdV code lists; 2523, 3040, 3041 and 3051 are
# checked against the list above, the others are the codes the extract delivers (51xxx and 53xxx are Bauwerk codes).
EXCLUDED = frozenset({
    "31001_2523",  # Umformer
    "31001_2740",  # Gewächshaus (Treibhaus)
    "31001_3040",  # Gebäude für religiöse Zwecke
    "31001_3041",  # Kirche
    "31001_3051",  # Krankenhaus
    "51009_1610",  # Überdachung
    "53001_1800",  # Bauwerk im Verkehrsbereich
    "51001_1002",  # Turm
})

# The municipality is read as in use_cases/land/sources.py (a source module may not import another use case).
_MUNICIPALITY = re.compile(r"<boris:BR_Gemeinde>.*?<boris:name>([^<]*)</boris:name>", re.S)


def name_of(code: str) -> str:
    return FUNCTION_NAMES.get(code, "Gebäude")


def _polygon(footprint: str) -> BaseGeometry:
    polygons = [shapely.Polygon(np.array(ring.replace(",", " ").split(), dtype=float).reshape(-1, 2))
                for ring in footprint.split(";")]
    geom = polygons[0] if len(polygons) == 1 else shapely.union_all(polygons)
    return geom if geom.is_valid else _polygonal(shapely.make_valid(geom))


def _polygonal(geom: BaseGeometry) -> BaseGeometry:
    """make_valid may return a GeometryCollection (polygons plus slivers as lines or points): keep the polygons."""
    if geom.geom_type in ("Polygon", "MultiPolygon"):
        return geom
    polygons = [g for g in shapely.get_parts(geom) if g.geom_type in ("Polygon", "MultiPolygon")]
    return shapely.union_all(polygons) if polygons else shapely.Polygon()


def read_parts(path: Path) -> pd.DataFrame:
    """One row per building part: building, use (function code), excluded, flat, height_m (NaN if unknown),
    ground_m2, gemarkung, created, geometry (EPSG:25832)."""
    raw = pd.read_csv(path, dtype={"building": str, "function": str, "gemarkung": str, "created": str,
                                   "roof_type": str, "footprint": str}, keep_default_na=False,
                      na_values={"height_m": [""]})
    return pd.DataFrame({
        "building": raw["building"], "use": raw["function"], "excluded": raw["function"].isin(EXCLUDED),
        "flat": raw["roof_type"] == FLAT_ROOF, "height_m": raw["height_m"].astype(float),
        "ground_m2": raw["ground_m2"].astype(float), "gemarkung": raw["gemarkung"], "created": raw["created"],
        "geometry": [_polygon(f) for f in raw["footprint"]]})


def read_gemarkungen(path: Path) -> pd.DataFrame:
    """gemarkung, buildings (count of the delivery's txt), parsed, delivered."""
    return pd.read_csv(path, dtype={"gemarkung": str, "delivered": str})


def read_zones(folder: Path) -> list[BaseGeometry]:
    """Housing zones of Frankfurt: building land ("B"), `art` W… or M… Same rule as `land` (a test compares both)."""
    zones = []
    for path in sorted(folder.glob("boris_*.gml")):
        for f in parse_features(path.read_text(encoding="utf-8")):
            m = _MUNICIPALITY.search(f.raw)
            if (f.geom is not None and m and m.group(1).strip() == "Frankfurt am Main"
                    and f.props.get("entwicklungszustand", "") == "B" and f.props.get("art", "")[:1] in ("W", "M")):
                zones.append(f.geom)
    return zones


def read_building_code(path: Path) -> list[str]:
    """Page texts of the synopsis of the Hessische Bauordnung (Baupaket I): old and new wording side by side."""
    return page_texts(path)
