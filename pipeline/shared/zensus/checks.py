"""Checks of the 2022 grid against the Zensus totals of Frankfurt. Pure module."""
from __future__ import annotations

import pandas as pd

from pipeline.shared.core.checks import Check, check_tolerance


def grid_checks(cells: pd.DataFrame, reference: dict[str, float]) -> list[Check]:
    inner, edge = cells[cells["edge"] == 0], cells[cells["edge"] == 1]
    return [check_tolerance("Grid: population", inner["pop"].sum(), reference["pop_zensus_2022"], rel=0.01),
            check_tolerance("Grid: population in edge cells", edge["pop"].sum(), 0,
                            absolute=0.005 * inner["pop"].sum()),
            check_tolerance("Grid: dwellings", inner["dwellings"].sum(), reference["dwellings_zensus_2022"],
                            rel=0.035)]  # the 3 % gap to the table is accepted (docs/data-rules.md, Traps of the Zensus grid)
