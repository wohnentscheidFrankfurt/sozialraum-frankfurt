"""Check of the land values of 2026 (land README, Checks). Pure module."""
from __future__ import annotations

from pipeline.shared.core.checks import FAIL, OK, WARN, Check
from pipeline.use_cases.land.model import Zone

AS_OF = "01.01.2026"  # the Stichtag as the WMS writes it
MAX_DROPPED = 0.02  # share of the zones of 2024 that may have no value of 2026


def check_values(zones: list[Zone], values: dict[str, tuple[float, str]]) -> Check:
    """Every value used has the Stichtag AS_OF; WARN if more than MAX_DROPPED of the zones have no value."""
    name = "Land values 2026: zones with a value"
    used = [values[z.number][1] for z in zones if z.number in values]
    other = sorted(set(used) - {AS_OF})
    if other:
        return Check(name, FAIL, f"Stichtag {', '.join(other)} instead of {AS_OF}")
    status = OK if len(zones) - len(used) <= MAX_DROPPED * len(zones) else WARN
    return Check(name, status, f"{len(used)} of {len(zones)} zones with a value of {AS_OF}")
