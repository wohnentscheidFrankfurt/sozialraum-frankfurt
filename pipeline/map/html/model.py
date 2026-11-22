"""Map payload, HTML and exports (docs/architecture.md, The map file). The texts of the page, of the browser and of
the cover note stand in texts.<lang>.yaml next to this module."""
from __future__ import annotations

import html
import json
import math
import re

import numpy as np
import pandas as pd

from pipeline.shared.core.geometry import feature_collection
from pipeline.shared.core.texts import Texts, package_texts
from pipeline.use_cases.election.catalog import ELECTION_DATE
from pipeline.use_cases.land.catalog import BORIS_DATE, use_name
from pipeline.use_cases.new_construction.catalog import FIRST_YEAR, LAST_YEAR, RENT_FROM, RENT_TO
from pipeline.use_cases.ownership_shares.model import DWELLING_COLUMNS
from pipeline.use_cases.social_housing.catalog import SH_DATE

T: dict[str, Texts] = package_texts(__file__)

MAX_BYTES = 5 * 1024 * 1024
ESTIMATES = DWELLING_COLUMNS
BASE_PROPERTIES = ("id", "name", "quarter", "survey_area", "small", "POP")
# read by hand in web/js (03_profile.js), not through a catalog id; the candidates read OWN_PUBLIC_HIGH and OWN_COOP_HIGH
# through the templates
BROWSER_EXTRA_PROPERTIES = ("COV_OWN", "PROT_SOCIAL", "pending_plan_names", "social_preservation_names",
                            "social_preservation_pending_names", "townscape_names", "townscape_pending_names")
MARKERS = ["/*__LEAFLET_CSS__*/", "/*__FONTS__*/", "/*__MAP_CSS__*/", "/*__DATA__*/", "/*__LEAFLET_JS__*/", "/*__MAP_JS__*/"]
DATA_MARKER = "/*__DATA__*/"
# a static text of the template: {{key}} names the key under `html` of the language file; {{lang}} is the language tag
TEXT_MARKER = re.compile(r"\{\{([\w.]+)\}\}")
HTML_LANG = {"de": "de", "en": "en-GB"}


def clean_value(value):
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, (float, np.floating)):
        return None if math.isnan(value) else float(value)
    return value


def json_for_html(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"), allow_nan=False).replace("<", "\\u003c")


def fill_text_markers(template: str, t: Texts) -> str:
    """The template with every text marker replaced by its escaped text. The texts hold no markup; it stays in the
    template. An unknown marker or a key of `html` that no marker uses stops the build."""
    texts = {key[len("html."):]: t[key] for key in t.keys() if key.startswith("html.")}
    used = set(TEXT_MARKER.findall(template))
    if unknown := sorted(used - set(texts) - {"lang"}):
        raise ValueError(f"text markers without a text under html ({t.lang}): {unknown}")
    if unused := sorted(set(texts) - used):
        raise ValueError(f"texts under html that no marker of the template uses ({t.lang}): {unused}")
    values = {**texts, "lang": HTML_LANG[t.lang]}
    return TEXT_MARKER.sub(lambda m: html.escape(values[m.group(1)]), template)


def render_html(template: str, parts: dict[str, str], data: dict, texts: Texts) -> str:
    template = fill_text_markers(template, texts)
    for marker in MARKERS:
        if template.count(marker) != 1:
            raise ValueError(f"marker {marker} missing or repeated in the template")
    contents = parts | {DATA_MARKER: json_for_html(data)}
    for marker in MARKERS:
        before, after = template.split(marker)
        template = before + contents[marker] + after
    return template


def language_switch(t: Texts, languages: tuple[str, ...], names: dict[str, str], paths: dict[str, str]) -> dict | None:
    """The link to the other language for the payload (web/js APP.switchHref): the label is the text `switch` of this
    language file, written in the language of the target. None when there is no other language."""
    others = [lang for lang in languages if lang != t.lang]
    if not others:
        return None
    other = others[0]
    return {"lang": other, "label": t["switch"], "file": names[other], "path": paths[other]}


def with_alternates(page: str, languages: tuple[str, ...], paths: dict[str, str], site: str) -> str:
    """The page with one `<link rel="alternate" hreflang>` per language at the end of the head (absolute URLs)."""
    if page.count("</head>") != 1:
        raise ValueError("the page needs exactly one </head> for the hreflang links")
    tags = "".join(f'<link rel="alternate" hreflang="{lang}" href="{site}{paths[lang]}">\n' for lang in languages)
    return page.replace("</head>", tags + "</head>")


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


def cover_note(created: str, t: Texts) -> str:
    """Cover note as a comment at the top of the map (docs/architecture.md, The map file). Caveats as in the help
    section of the map. The years come from the catalog constants."""
    return t.fill("cover_note", social_housing_year=SH_DATE.year, first_year=FIRST_YEAR, last_year=LAST_YEAR,
                  rent_from=RENT_FROM, rent_to=RENT_TO, election_year=ELECTION_DATE.year,
                  land_value_year=BORIS_DATE.year, created=created)


def with_cover_note(page: str, created: str, t: Texts) -> str:
    """Puts the cover note as a comment right after the doctype, so the doctype stays the first line."""
    doctype = "<!doctype html>\n"
    if not page.startswith(doctype):
        raise ValueError("the template does not start with <!doctype html>")
    text = cover_note(created, t)
    if "--" in text:
        raise ValueError("the cover note contains --, which ends the HTML comment")
    return f"{doctype}<!--\n{text}-->\n{page[len(doctype):]}"


def with_shared_texts(indicators: pd.DataFrame, monitoring: pd.DataFrame) -> pd.DataFrame:
    """The districts with each text column `*_SHARED` (the districts that share a monitoring value) taken from the
    monitoring table of another language, matched by id. The area tables are joined once, in German
    (pipeline/map/assembly/step.py); every other column stays."""
    texts = monitoring.set_index("id")
    out = indicators.copy()
    for column in (c for c in indicators.columns if c.endswith("_SHARED")):
        out[column] = out["id"].map(texts[column])
    return out


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
