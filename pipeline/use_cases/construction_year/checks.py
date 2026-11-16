"""Check of the dwellings by year of construction against the Zensus table 4000W-1008. Pure module."""
from __future__ import annotations

from pipeline.shared.core.checks import Check, check_tolerance

# grid of 2011 against table 4000W-1008: secrecy loses small numbers in the grid (README)
CONSTRUCTION_TOLERANCE = {"pre1919": 0.06, "1949_1978": 0.02, "total": 0.01}
SHARE_CLASSES = ("pre1919", "1949_1978")  # the classes with a layer
# city share (class 2011 capped per cell ÷ dwellings 2022) against the table of 2022, in points: new dwellings in old
# buildings since 2011 are missing in the estimate (README)
CITY_SHARE_TOLERANCE = 2.0


def check_construction_year(grid: dict[str, int], table: dict[int, dict[str, int]],
                            city: dict[str, float]) -> list[Check]:
    """Dwellings by year of construction (README): the 2011 grid (inner cells, uncapped: it tests the reading of the
    grid) against table 4000W-1008 for 2011; the city shares (class 2011 capped per cell ÷ dwellings 2022) against
    the table shares of 2022. They hold the Abgleich the ⓘ named before (docs/data-rules.md, Checks)."""
    checks = [check_tolerance(f"Construction year: grid 2011 against 4000W-1008, {k}", grid[k], table[2011][k], rel=r)
              for k, r in CONSTRUCTION_TOLERANCE.items()]
    table_share = {k: 100 * table[2022][k] / table[2022]["total"] for k in SHARE_CLASSES}
    checks += [check_tolerance(f"Construction year: city share against 4000W-1008 (2022), {k}", city[k],
                               table_share[k], absolute=CITY_SHARE_TOLERANCE) for k in SHARE_CLASSES]
    return checks
