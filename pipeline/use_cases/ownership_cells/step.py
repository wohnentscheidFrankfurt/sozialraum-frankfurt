"""Step ownership_cells: dwellings per ownership type and cell, the overlay rows and their checks."""
from __future__ import annotations

import pandas as pd

from pipeline.engine.datasets import (CELLS_2011_DWELLINGS, CELLS_2022, OWNERSHIP_CELLS, OWNERSHIP_CELLS_CHECKS,
                                      OWNERSHIP_GRID_CELLS)
from pipeline.use_cases.ownership_cells.checks import check_assigned_total, check_unassigned
from pipeline.use_cases.ownership_cells.model import (GRID_GROUPS, GRID_SCALE, estimate, fill_from_2011, grid_factors,
                                                      grid_rows)
from pipeline.engine.steps import Context, Step, write_checks
from pipeline.shared.zensus.cells import inner_cells
from pipeline.shared.zensus.model import CLASSES
from pipeline.shared.zensus.tables import read_4000w


def run(ctx: Context) -> None:
    c = ctx.config
    cells = inner_cells(ctx.store)
    dwellings = read_4000w(c.ZENSUS_4000W.read_text(encoding="utf-8-sig"))
    buildings = {k: int(cells[f"bld_{k}"].sum()) for k in CLASSES}
    f = grid_factors(cells, dwellings)
    cells_2011 = ctx.store.read(CELLS_2011_DWELLINGS)
    ownership = fill_from_2011(estimate(cells, f), cells, cells_2011)
    ctx.store.write(OWNERSHIP_CELLS, ownership)
    table = pd.DataFrame([{"class": k, "dwellings_4000w": dwellings[k], "buildings_grid": buildings[k],
                           "factor": round(f[k], 4)} for k in CLASSES])
    rows = grid_rows(cells.merge(ownership, on="cell_id").merge(cells_2011, on="cell_id", how="left"))
    ctx.store.write(OWNERSHIP_GRID_CELLS, {"groups": GRID_GROUPS, "scale": GRID_SCALE, "rows": rows})
    total = cells["dwellings"].sum()
    write_checks(ctx.store, OWNERSHIP_CELLS_CHECKS, [check_assigned_total(ownership, total),
                                                     check_unassigned(ownership["dw_unassigned"].sum(), total)])
    ctx.log(table.to_string(index=False))
    filled = ownership["dw_from_2011"]
    ctx.log(f"filled from Zensus 2011: {filled.sum():,.0f} dwellings in {int((filled > 0).sum())} cells; "
            f"{ownership['dw_unassigned'].sum():,.0f} dwellings stay without ownership type")


STEP = Step("ownership_cells", run, needs=(CELLS_2022, CELLS_2011_DWELLINGS),
            makes=(OWNERSHIP_CELLS, OWNERSHIP_GRID_CELLS, OWNERSHIP_CELLS_CHECKS))
