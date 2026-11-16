"""ALKIS extracts (sources/hessen/alkis/: parcels, buildings, land use); the source vocabulary of building gaps."""
from __future__ import annotations

import re
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd
import shapely
from shapely.geometry.base import BaseGeometry

from pipeline.engine.download import download
from pipeline.shared.readers.gml import parse_features
from pipeline.shared.readers.raster import mosaic, png_rgb
from pipeline.use_cases.building_gaps.model import (HIGH_M, MAIN_MIN_M2, NDVI_GREEN, Gap, _polygonal, cover_shares,
                                                    find_gaps, ndvi)

# Gebäudefunktion codes of buildings that are no main building: Garage, Parkhaus, Tiefgarage, Umformer, Pumpstation,
# Gewächshaus, Überdachung and the like (AdV code list, Kennung 31001), 9998 "Nach Quellenlage nicht zu spezifizieren".
MINOR_FUNCTIONS = frozenset({"2460", "2461", "2462", "2463", "2464", "2465", "2523", "2513", "2512", "1313", "2740",
                             "9998"})
HOUSING_CLASSES = frozenset({"Wohnbauflaeche", "FlaecheGemischterNutzung"})  # AX_ land use classes of housing
ACCESS_CLASSES = frozenset({"Strassenverkehr", "Weg", "Platz"})  # AX_ classes a parcel front can lie at ...
PARKING = "5310"  # ... except a Platz of this function (Parkplatz)
DOP_LAYER_CIR = "he_dop20_cir"  # colour infrared orthophoto, 20 cm
DOP_LAYER_INFO = "he_dop_rgb_info"  # its GetFeatureInfo layer names the flight
PAD_M = 2  # the cover grid reaches this far around the parcel
# The thresholds measure_cover classifies with. update_sources writes them into alkis_meta.csv next to the cover file,
# and the check compares them with model.py (a changed threshold needs a rerun of update_sources).
COVER_THRESHOLDS = {"cover_high_m": HIGH_M, "cover_ndvi_green": NDVI_GREEN}
WORKERS = 4


def _read(path: Path) -> pd.DataFrame:
    raw = pd.read_csv(path, dtype=str, keep_default_na=False)
    geoms = shapely.make_valid(shapely.from_wkt(raw["wkt"].to_numpy()))
    raw["geometry"] = np.array([_polygonal(g) for g in geoms], dtype=object)
    return raw.drop(columns="wkt")


def read_parcels(path: Path) -> pd.DataFrame:
    """gml_id, kz, official_m2 (NaN if missing), created, addresses (count), geometry (EPSG:25832)."""
    raw = _read(path)
    raw["official_m2"] = pd.to_numeric(raw["official_m2"], errors="coerce")
    raw["addresses"] = pd.to_numeric(raw["addresses"], errors="coerce").fillna(0).astype(int)
    return raw[["gml_id", "kz", "official_m2", "created", "addresses", "geometry"]]


def read_buildings(path: Path) -> pd.DataFrame:
    """gml_id, function, main (no minor function and a footprint of at least MAIN_MIN_M2), geometry."""
    raw = _read(path)
    area = shapely.area(raw["geometry"].to_numpy())
    raw["main"] = (~raw["function"].isin(MINOR_FUNCTIONS)).to_numpy() & (area >= MAIN_MIN_M2)
    return raw[["gml_id", "function", "main", "geometry"]]


def read_landuse(path: Path) -> pd.DataFrame:
    """gml_id, cls, function, housing (a housing class), access (a street, way or square but no parking lot), geometry."""
    raw = _read(path)
    raw["housing"] = raw["cls"].isin(HOUSING_CLASSES)
    raw["access"] = raw["cls"].isin(ACCESS_CLASSES) & ~((raw["cls"] == "Platz") & (raw["function"] == PARKING))
    return raw[["gml_id", "cls", "function", "housing", "access", "geometry"]]


def candidates_for_cover(parcels_csv: Path, buildings_csv: Path, landuse_csv: Path) -> list[Gap]:
    """The geometry candidates: the one entry point of update_sources."""
    return find_gaps(read_parcels(parcels_csv), read_buildings(buildings_csv), read_landuse(landuse_csv))[0]


def dom_name(tx: int, ty: int) -> str:
    return f"DOM1_32_{tx}_{ty}_1_he.tif"


def dgm_name(tx: int, ty: int) -> str:
    return f"DGM1_32_{tx}_{ty}_1_he.tif"


def getmap_url(base: str, layer: str, x0: int, y0: int, x1: int, y1: int) -> str:
    """WMS 1.3.0 GetMap in EPSG:25832, PNG, one pixel per metre."""
    return (f"{base}?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetMap&LAYERS={layer}&STYLES=&CRS=EPSG:25832"
            f"&BBOX={x0},{y0},{x1},{y1}&WIDTH={x1 - x0}&HEIGHT={y1 - y0}&FORMAT=image/png")


def info_url(base: str, x: float, y: float) -> str:
    """WMS 1.3.0 GetFeatureInfo as text on the pixel at the point of a box of 100 m (a box of 1 m finds nothing)."""
    x0, y0 = int(np.floor(x)) - 50, int(np.floor(y)) - 50
    return (f"{base}?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetFeatureInfo&LAYERS={DOP_LAYER_INFO}&STYLES="
            f"&QUERY_LAYERS={DOP_LAYER_INFO}&CRS=EPSG:25832&BBOX={x0},{y0},{x0 + 100},{y0 + 100}&WIDTH=100&HEIGHT=100"
            f"&I=50&J=49&INFO_FORMAT=text/plain&FEATURE_COUNT=1")


def flight_date(text: str) -> str:
    """Date of the flight (bildflug = 'DD-MM-YYYY') as ISO date, "" if the answer holds none."""
    m = re.search(r"bildflug\s*=\s*'(\d{2})-(\d{2})-(\d{4})'", text)
    return f"{m.group(3)}-{m.group(2)}-{m.group(1)}" if m else ""


def cache_stem(gml_id: str) -> str:
    """File stem of a gml_id in the cache: each capital letter becomes an underscore and the lower-case letter. Why:
    two gml_ids can differ only in case, and a case-insensitive file system would give them one file."""
    return "".join(f"_{c.lower()}" if c.isupper() else c for c in gml_id)


def measure_cover(gaps: list[Gap], dom_zip: Path, dgm_zip: Path, wms: str, cache: Path, refresh: bool,
                  download=download) -> pd.DataFrame:
    """Cover classes per gap from nDOM (DOM1 - DGM1) and the NDVI of the CIR orthophoto, sorted by gml_id.

    The PNG and the flight text of each gap stay in cache (cache/<cache_stem>_cir.png, _info.txt)."""
    gaps = sorted(gaps, key=lambda g: g.gml_id)
    boxes = []
    for g in gaps:
        bx0, by0, bx1, by1 = g.geom.bounds
        boxes.append((int(np.floor(bx0)) - PAD_M, int(np.floor(by0)) - PAD_M, int(np.floor(bx1)) + PAD_M + 1,
                      int(np.floor(by1)) + PAD_M + 1))

    def fetch(i: int) -> None:
        g, (x0, y0, x1, y1) = gaps[i], boxes[i]
        download(getmap_url(wms, DOP_LAYER_CIR, x0, y0, x1, y1), cache / f"{cache_stem(g.gml_id)}_cir.png", refresh)
        download(info_url(wms, g.x, g.y), cache / f"{cache_stem(g.gml_id)}_info.txt", refresh)

    cache.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(WORKERS) as pool:
        list(pool.map(fetch, range(len(gaps))))  # list(): raise the errors of the workers
    rows = []
    with zipfile.ZipFile(dom_zip) as zd, zipfile.ZipFile(dgm_zip) as zg:
        for g, (x0, y0, x1, y1) in zip(gaps, boxes):
            ndom = mosaic(zd, dom_name, x0, y0, x1, y1) - mosaic(zg, dgm_name, x0, y0, x1, y1)
            cir = png_rgb((cache / f"{cache_stem(g.gml_id)}_cir.png").read_bytes())
            if cir.shape[:2] != ndom.shape:
                raise RuntimeError(f"orthophoto of {g.gml_id} has {cir.shape[:2]} pixels, expected {ndom.shape}")
            text = (cache / f"{cache_stem(g.gml_id)}_info.txt").read_text(errors="replace")
            rows.append({"gml_id": g.gml_id, **cover_shares(g.geom, ndom, ndvi(cir), x0, y1),
                         "flight": flight_date(text)})
    return pd.DataFrame(rows, columns=["gml_id", "px", "building", "tree", "green", "open", "nan_share", "flight"])


VERDICT_COLUMNS = ["gml_id", "kz", "verdict", "reason", "note", "checked", "by"]
# The municipality is read as in use_cases/land/sources.py (a source module may not import another use case).
_MUNICIPALITY = re.compile(r"<boris:BR_Gemeinde>.*?<boris:name>([^<]*)</boris:name>", re.S)


def read_cover(path: Path) -> pd.DataFrame:
    """Cover classes per gap (update_sources writes them), indexed by gml_id; flight is an ISO date or ""."""
    return pd.read_csv(path, dtype={"gml_id": str, "flight": str}, keep_default_na=False,
                       na_values={"flight": []}).set_index("gml_id")


def read_verdicts(path: Path) -> pd.DataFrame:
    """Hand verdicts: gml_id, kz, verdict, reason, note, checked, by, all str ("" where empty). A file with only the
    header gives an empty frame."""
    return pd.read_csv(path, dtype=str, keep_default_na=False)[VERDICT_COLUMNS]


def read_zones(folder: Path) -> list[BaseGeometry]:
    """Housing zones of Frankfurt: building land ("B"), `art` W… or M… Same rule as flat_roofs and land."""
    zones = []
    for path in sorted(folder.glob("boris_*.gml")):
        for f in parse_features(path.read_text(encoding="utf-8")):
            m = _MUNICIPALITY.search(f.raw)
            if (f.geom is not None and m and m.group(1).strip() == "Frankfurt am Main"
                    and f.props.get("entwicklungszustand", "") == "B" and f.props.get("art", "")[:1] in ("W", "M")):
                zones.append(f.geom)
    return zones


def kz_text(kz: str) -> str:
    """Flurstückskennzeichen as text: "060503024000420001__" gives "Gemarkung 0503, Flur 24, Nr. 42/1"; without a
    Nenner "Nr. 104"."""
    number, denominator = kz[9:14].lstrip("0") or "0", kz[14:18].strip("_").lstrip("0")
    nr = f"{number}/{denominator}" if denominator else number
    return f"Gemarkung {kz[2:6]}, Flur {kz[6:9].lstrip('0') or '0'}, Nr. {nr}"


def read_meta(path: Path) -> dict[str, str]:
    """The facts of the ALKIS delivery (update_sources writes them): portion_date (ISO) and the counts read."""
    return dict(pd.read_csv(path, dtype=str, keep_default_na=False).itertuples(index=False, name=None))
