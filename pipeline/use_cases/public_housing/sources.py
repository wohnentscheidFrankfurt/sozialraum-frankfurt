"""Own research of the ABG sites."""
from __future__ import annotations

import json
import re

import pandas as pd


# Own research of the ABG sites (sources/other/ABG-Holding-Karte.geojson, as of 8.10.2026)
RESEARCH_CITY = "Frankfurt am Main"
RESEARCH_LEVELS = ("bestand", "neubau")  # existing estates, finished new buildings


def read_research_sites(text: str) -> pd.DataFrame:
    """Sites in Frankfurt with a number of dwellings: id, level, dwellings, precision (A address, Q quarter, O only the
    Stadtteil), year (the latest year named in "stand", empty without one), lon, lat."""
    rows = []
    for f in json.loads(text)["features"]:
        p = f["properties"]
        if p["gebiet"] != RESEARCH_CITY or p["ebene"] not in RESEARCH_LEVELS or not p["wohnungen"]:
            continue
        years = [int(y) for y in re.findall(r"(?<!\d)(19\d\d|20\d\d)(?!\d)", str(p["stand"]))]
        lon, lat = f["geometry"]["coordinates"]
        rows.append({"id": p["id"], "level": p["ebene"], "dwellings": int(p["wohnungen"]),
                     "precision": p["lage_genauigkeit"], "year": max(years) if years else None, "lon": lon, "lat": lat})
    df = pd.DataFrame(rows, columns=["id", "level", "dwellings", "precision", "year", "lon", "lat"])
    df["year"] = df["year"].astype("Int64")
    return df
