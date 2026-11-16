"""Checks of the protection step: the areas under No. 2 against the list of 6.10.2026. The WFS answers are checked
with check_wfs (pipeline.shared.core.checks)."""
from __future__ import annotations

from pipeline.shared.core.checks import OK, WARN, Check


def check_social_preservation(current: set[str], expected: set[str]) -> Check:
    name = "Social preservation: areas under No. 2"
    new, gone = sorted(current - expected), sorted(expected - current)
    if new or gone:
        return Check(name, WARN, f"new: {new or '–'}; missing: {gone or '–'}")
    return Check(name, OK, f"{len(current)} areas as on 6.10.2026")
