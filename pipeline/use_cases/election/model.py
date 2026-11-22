"""Election of the city council on 15.3.2026 per quarter: shares per list, list keys, colors."""
from __future__ import annotations

import re
import unicodedata

import pandas as pd

from pipeline.shared.core.stats import STORED_DECIMALS

THRESHOLD = 2.0  # lists under this share in the city go into the group of the small lists (ELEC_OTHER)
OTHER_KEY = "ELEC_OTHER"
OTHER_COLOR = "#9e9e9e"
_COLOR = re.compile(r"#[0-9a-fA-F]{6}")


def valid_color(value) -> str | None:
    """Lower-case #rrggbb or None."""
    return value.lower() if isinstance(value, str) and _COLOR.fullmatch(value) else None


def color(value) -> str:
    return valid_color(value) or OTHER_COLOR


def list_key(name: str) -> str:
    s = name.upper().replace("Ä", "AE").replace("Ö", "OE").replace("Ü", "UE").replace("ß", "SS")
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return "ELEC_" + re.sub(r"[^A-Z0-9]", "", s)


def shares(areas: list[dict], city: dict, lists: list[dict], other_name: str) -> tuple[pd.DataFrame, list[dict]]:
    """Share of each list per quarter; lists under THRESHOLD % in the city go into the group OTHER_KEY, named
    `other_name` (a text of the source language; the map of a language renames it, catalog.shown_lists)."""
    city_shares = {l["name"]: 100 * city["votes"][l["position"]] / city["valid"] for l in lists}
    shown = [l | {"key": list_key(l["name"]), "city_share": round(city_shares[l["name"]], STORED_DECIMALS)}
             for l in lists if city_shares[l["name"]] >= THRESHOLD]
    rows = []
    for area in areas:
        valid = area["valid"]
        votes = {l["name"]: area["votes"][l["position"]] for l in lists}
        row = {"quarter": area["name"], "ELEC_ELIGIBLE": area["eligible"], "ELEC_VOTERS": area["voters"],
               "ELEC_VALID_VOTES": valid, "ELEC_TURNOUT": round(100 * area["voters"] / area["eligible"], STORED_DECIMALS),
               "ELEC_STRONGEST": max(votes, key=votes.get)}
        for l in shown:
            row[l["key"]] = round(100 * votes[l["name"]] / valid, STORED_DECIMALS)
        row[OTHER_KEY] = round(100 - sum(row[l["key"]] for l in shown), STORED_DECIMALS)
        rows.append(row)
    other = {"position": 0, "name": other_name, "color": OTHER_COLOR, "key": OTHER_KEY,
             "city_share": round(100 - sum(l["city_share"] for l in shown), STORED_DECIMALS)}
    return pd.DataFrame(rows), shown + [other]
