"""Map payload, HTML and exports (docs/architecture.md, The map file). German texts here are visible in the map."""
from __future__ import annotations

import json
import math

import numpy as np
import pandas as pd

from pipeline.shared.core.geometry import feature_collection
from pipeline.shared.core.texts import Texts
from pipeline.use_cases.election.catalog import ELECTION_DAY
from pipeline.use_cases.land.catalog import BORIS_AS_OF, use_name
from pipeline.use_cases.new_construction.catalog import FIRST_YEAR, LAST_YEAR, RENT_FROM, RENT_TO
from pipeline.use_cases.ownership_shares.model import DWELLING_COLUMNS
from pipeline.use_cases.social_housing.catalog import SH_AS_OF

MAX_BYTES = 5 * 1024 * 1024
ESTIMATES = DWELLING_COLUMNS
BASE_PROPERTIES = ("id", "name", "quarter", "survey_area", "small", "POP")
# read by hand in web/js (03_profile.js), not through a catalog id; the candidates read OWN_PUBLIC_HIGH and OWN_COOP_HIGH
# through the templates
BROWSER_EXTRA_PROPERTIES = ("COV_OWN", "PROT_SOCIAL", "pending_plan_names", "social_preservation_names",
                            "social_preservation_pending_names", "townscape_names", "townscape_pending_names")
MARKERS = ["/*__LEAFLET_CSS__*/", "/*__FONTS__*/", "/*__MAP_CSS__*/", "/*__DATA__*/", "/*__LEAFLET_JS__*/", "/*__MAP_JS__*/"]
DATA_MARKER = "/*__DATA__*/"


def clean_value(value):
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, (float, np.floating)):
        return None if math.isnan(value) else float(value)
    return value


def json_for_html(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"), allow_nan=False).replace("<", "\\u003c")


def render_html(template: str, parts: dict[str, str], data: dict) -> str:
    for marker in MARKERS:
        if template.count(marker) != 1:
            raise ValueError(f"marker {marker} missing or repeated in the template")
    contents = parts | {DATA_MARKER: json_for_html(data)}
    for marker in MARKERS:
        before, after = template.split(marker)
        template = before + contents[marker] + after
    return template


def browser_properties(catalog: list[dict], templates: list[dict], lists: list[dict]) -> set[str]:
    """Names of the area properties the browser reads; the payload holds no others (tests scan web/js for them).

    `catalog` is the list of dicts of map_catalog.json. Some names the code reads by hand, not through the catalog."""
    keep = set(BASE_PROPERTIES) | set(BROWSER_EXTRA_PROPERTIES)
    for entry in catalog:
        keep.add(entry["id"])
        if entry.get("count_total"):
            keep.add(entry["count_total"])  # the total a count is shown against (tooltip: „1.343 von 2.871“)
        if entry["type"] == "classes":
            keep.add(entry["id"] + "_LOWER")
        if entry["type"] == "number":
            keep.add(entry["id"] + "_SHARED")  # monitoring: the districts that share the value (tooltip, profile)
    keep |= {k for k in DWELLING_COLUMNS if not k.endswith("_LOW")}
    keep |= {c["indicator"] for t in templates for c in t["criteria"]}
    return keep | {entry["key"] for entry in lists}


def area_properties(df: pd.DataFrame, keep: set[str] | None = None) -> dict[str, dict]:
    """Properties per area id; only the columns in `keep` (all columns when it is None)."""
    return {str(r["id"]): {k: clean_value(v) for k, v in r.items() if keep is None or k in keep}
            for r in df.to_dict("records")}


def area_collection(areas, df: pd.DataFrame, keep: set[str] | None = None) -> dict:
    props = area_properties(df, keep)
    return feature_collection((props[a.id], a.geom, 5.0) for a in areas)


def with_use_names(zones: dict, t: Texts) -> dict:
    """The land value zones for the payload: use code and building type of the source become one name for the
    tooltip („Mischgebiet, Mehrfamilienhäuser“), in the language of t (the texts of land)."""
    def props(p: dict) -> dict:
        rest = {k: v for k, v in p.items() if k != "building"}
        return {**rest, "use": use_name(p["use"], p.get("building", ""), t)}
    return {**zones, "features": [{**f, "properties": props(f["properties"])} for f in zones["features"]]}


def cover_note(created: str) -> str:
    """Cover note as a comment at the top of the map (docs/architecture.md, The map file). Caveats as in the help section „Hilfe“."""
    return f"""Sozialraum Frankfurt
====================

Die Karte zeigt Eigentum, soziale Lage, Miete, Wohnungsbestand, Boden, Planung und Wahl in Frankfurt am Main.
Alles steckt in dieser einen Datei. Nur der graue Hintergrund (basemap.de) braucht Internet.

VORBEHALTE
- Die Karte beschreibt Gebiete, nicht Menschen.
- Eigentum ist geschätzt, ebenso die Aufteilung zwischen ABG und Nassauischer Heimstätte.
- Die Daten haben verschiedene Stände. Eigentum stammt aus dem Zensus 2022. Wo dort die Eigentumsform fehlt, nutzt die Karte den Zensus 2011. Das Baujahr stammt aus dem Zensus 2011. Dazu kommen Monitoring 2022, Wohnungsamt {SH_AS_OF[-4:]}, Neubau {FIRST_YEAR}–{LAST_YEAR}, Miete {RENT_FROM}–{RENT_TO}, Umfrage 2024 und 2025, Wahl {ELECTION_DAY[-4:]}, Bodenrichtwerte {BORIS_AS_OF[-4:]} und 3D-Gebäudemodell 2026.
- Mehr dazu im Reiter „Hilfe“ der Karte.

QUELLEN
Das ⓘ neben jeder Kennzahl nennt Quelle, Stand und Rechnung.

Erstellt am {created}
"""


def with_cover_note(html: str, created: str) -> str:
    """Puts the cover note as a comment right after the doctype, so the doctype stays the first line."""
    doctype = "<!doctype html>\n"
    if not html.startswith(doctype):
        raise ValueError("the template does not start with <!doctype html>")
    text = cover_note(created)
    if "--" in text:
        raise ValueError("the cover note contains --, which ends the HTML comment")
    return f"{doctype}<!--\n{text}-->\n{html[len(doctype):]}"


def round_to_50(x):
    """Half up to the nearest 50; empty stays empty."""
    if x is None or pd.isna(x):
        return None
    return int(50 * math.floor(float(x) / 50 + 0.5))


def round_estimates(row_or_df):
    """Copy with the dwelling counts of the six owner groups rounded to 50 (exports: the estimate is not exact to the dwelling)."""
    if isinstance(row_or_df, pd.DataFrame):
        df = row_or_df.copy()
        for k in ESTIMATES:
            if k in df.columns:
                df[k] = pd.Series([round_to_50(x) for x in df[k]], index=df.index, dtype="Int64")
        return df
    row = dict(row_or_df)
    for k in ESTIMATES:
        if row.get(k) is not None:
            row[k] = round_to_50(row[k])
    return row


def rounded_geojson(fc: dict) -> dict:
    """GeoJSON copy with rounded estimates in the properties; the input stays unchanged."""
    return {**fc, "features": [{**f, "properties": round_estimates(f["properties"])} for f in fc["features"]]}
