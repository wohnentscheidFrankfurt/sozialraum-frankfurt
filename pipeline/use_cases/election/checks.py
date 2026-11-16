"""Checks of the election step: the quarters add up to the city result, and the city result stands in the gazette.
Pure module."""
from __future__ import annotations

from pipeline.shared.core.checks import FAIL, OK, Check, de_thousands


def _election_fields(row: dict) -> dict[str, int]:
    return {"eligible": row["eligible"], "voters": row["voters"], "valid": row["valid"],
            **{f"votes {p}": v for p, v in row["votes"].items()}}


def check_election_sums(quarters: list[dict], city: dict) -> Check:
    name = "Election: sum of quarters"
    expected = _election_fields(city)
    wrong = [k for k, v in expected.items() if sum(_election_fields(q)[k] for q in quarters) != v]
    if wrong:
        return Check(name, FAIL, f"fields differ: {', '.join(wrong)}")
    return Check(name, OK, f"{len(expected)} fields match")


def check_gazette(city: dict, text: str | None, path=None) -> Check:
    name = "Election: numbers in the gazette"
    if text is None:
        return Check(name, FAIL, f"gazette missing: {path}")
    fields = _election_fields(city)
    missing = [k for k, v in fields.items() if v > 0 and de_thousands(v) not in text]
    if missing:
        return Check(name, FAIL, "not in the gazette: " + ", ".join(f"{k}={de_thousands(fields[k])}" for k in missing))
    return Check(name, OK, "all numbers found")
