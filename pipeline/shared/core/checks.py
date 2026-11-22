"""Check results of the build and the helpers every check uses (docs/architecture.md, Checks). Pure module."""
from __future__ import annotations

import re
from dataclasses import dataclass

from pipeline.shared.core.texts import SOURCE_LANGUAGE

OK, WARN, FAIL = "OK", "WARN", "FAIL"
RANK = {FAIL: 0, WARN: 1, OK: 2}


@dataclass
class Check:
    name: str
    status: str
    text: str


def for_language(checks: list[Check], statements: set[str], lang: str) -> list[Check]:
    """The checks of the texts of one language. The source language keeps every check. Any other language keeps the
    statement checks (`statements`: names of the checks that read the texts) and adds its code to their names, so
    the names stay unique; the numeric checks run once. A name in `statements` without a check raises, so a typo
    cannot drop a check silently."""
    missing = statements - {c.name for c in checks}
    if missing:
        raise ValueError(f"statement checks without a check: {sorted(missing)}")
    if lang == SOURCE_LANGUAGE:
        return checks
    return [Check(f"{c.name} ({lang})", c.status, c.text) for c in checks if c.name in statements]


def number(x: float, decimals: int = 2) -> str:
    return f"{x:,.{decimals}f}"


def thousands(n: int) -> str:
    return f"{n:,}"


def de_thousands(n: int) -> str:
    """The gazette prints German thousands separators, for example 5.574.438."""
    return f"{n:,}".replace(",", ".")


def check_tolerance(name: str, found: float, expected: float, rel: float | None = None, absolute: float | None = None,
                    on_failure: str = FAIL) -> Check:
    limit = rel * expected if rel is not None else absolute
    status = OK if abs(found - expected) <= limit else on_failure
    return Check(name, status, f"is {number(found)}, expected {number(expected)}, allowed ± {number(limit)}")


def check_examples(name: str, texts: dict[str, str], examples: list[dict]) -> Check:
    """Named examples: every phrase stands in its source. texts: source key -> text; examples: name, source, phrases."""
    missing = []
    for e in examples:
        text = re.sub(r"\s+", " ", texts.get(e["source"], ""))
        missing += [f"{e['name']}: „{p}“" for p in e["phrases"] if p not in text]
    names = ", ".join(dict.fromkeys(e["name"] for e in examples))  # a name with two sources stands once
    return Check(name, FAIL if missing else OK, "not found: " + "; ".join(missing) if missing else names)

# agreed with the user (research/2026-10-10-abg-estimate-accuracy.md): a value is shown as a number if in 9 of 10
# areas with at least AGREED_MIN dwellings of the group the half range is at most AGREED_TOLERANCE of the value
# (docs/data-rules.md, Checks). The check names and the report text keep the date of the agreement.
AGREED_TOLERANCE, AGREED_MIN, AGREED_AREAS = 0.15, 200, 0.9


def check_agreed_tolerance(name: str, values: list[float], halves: list[float],
                           accepted: tuple[int, int] | None = None) -> Check:
    """Stadtteile with at least AGREED_MIN dwellings whose half range is at most AGREED_TOLERANCE of the value; WARN
    below 9 of 10. accepted: the share the user accepted all the same, as (passing, areas); OK down to that share
    (ABG and NH)."""
    big = [(v, h) for v, h in zip(values, halves) if v >= AGREED_MIN]
    passing = sum(h <= AGREED_TOLERANCE * v for v, h in big)
    ok = passing >= AGREED_AREAS * len(big) or (accepted is not None
                                                and passing * accepted[1] >= accepted[0] * len(big))
    note = f"accepted on 11.10.2026: {accepted[0]} of {accepted[1]}; " if accepted is not None else ""
    return Check(name, OK if ok else WARN,
                 f"{passing} of {len(big)} Stadtteile with at least {AGREED_MIN} dwellings within ± "
                 f"{AGREED_TOLERANCE:.0%} (agreed: 9 of 10; {note}the clause „at most 3 share points“ is not "
                 f"checked)".replace("%", " %"))


def check_same_values(name: str, values: dict[str, int], reference: dict[str, int]) -> Check:
    """Two Zensus tables must agree class by class."""
    diffs = [f"{k}: {values.get(k)} against {v}" for k, v in reference.items() if values.get(k) != v]
    return Check(name, FAIL if diffs else OK, "; ".join(diffs) or "all classes equal")


def check_wfs(file_name: str, features: int | None) -> Check:
    """An empty WFS response (for example an exception report) must not silently become "no protection"."""
    name = f"WFS: {file_name}"
    if features is None:
        return Check(name, FAIL, "file missing")
    if features == 0:
        return Check(name, FAIL, "no features with an area (empty response or error message of the service)")
    return Check(name, OK, f"{features} features with an area")


def as_rows(checks: list[Check]) -> list[dict]:
    return [{"name": c.name, "status": c.status, "text": c.text} for c in checks]


def from_rows(rows: list[dict]) -> list[Check]:
    return [Check(r["name"], r["status"], r["text"]) for r in rows]
