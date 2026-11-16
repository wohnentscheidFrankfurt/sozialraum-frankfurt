"""votemanager results (CSV and JSON in cache/), party colors of the Statistikportal (reference/) and the text of the
official gazette."""
from __future__ import annotations

import csv
import re
from pathlib import Path

from pipeline.use_cases.election.model import color, valid_color
from pipeline.shared.readers.pdf import page_texts

_VOTES = re.compile(r"D\d+")


def read_rows(path: Path) -> list[dict[str, str]]:
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def result_row(raw: dict[str, str]) -> dict:
    """A votemanager row: A eligible, B voters, D valid votes, D1 … Dn votes per list position."""
    return {"name": raw["gebiet-name"].strip(), "eligible": int(raw["A"]), "voters": int(raw["B"]),
            "valid": int(raw["D"]), "votes": {int(k[1:]): int(v) for k, v in raw.items() if _VOTES.fullmatch(k)}}


def read_results(path: Path) -> list[dict]:
    return [result_row(r) for r in read_rows(path)]


def read_party_colors(path: Path) -> dict[str, str]:
    """Party colors of the Statistikportal, name -> #rrggbb; invalid values are dropped."""
    with open(path, encoding="utf-8", newline="") as f:
        return {r["name"]: c for r in csv.DictReader(f) if (c := valid_color(r["color"]))}


def lists(result: dict, party_colors: dict[str, str]) -> list[dict]:
    """Color per list: Statistikportal (exact name), else votemanager, else grey."""
    rows = result["Komponente"]["tabelle"]["zeilen"]
    names = [r["label"]["labelKurz"].replace(" - Summe Kandidaten-Stimmen", "").strip() for r in rows]
    return [{"position": i, "name": n, "color": valid_color(party_colors.get(n)) or color(r.get("color"))}
            for i, (n, r) in enumerate(zip(names, rows), 1)]


def read_gazette_text(path: Path) -> str | None:
    return "\n".join(page_texts(path)) if path.exists() else None
