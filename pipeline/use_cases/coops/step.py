"""Step coops: Genossenschaften per Stadtteil and their checks."""
from __future__ import annotations

from pipeline.use_cases.coops.checks import coop_checks
from pipeline.use_cases.coops.model import coop_cells, coops_by_quarter
from pipeline.engine.datasets import CELLS_2011_DWELLINGS, CELLS_2022, COOPS_CHECKS, COOPS_QUARTERS, OWNERSHIP_CELLS
from pipeline.engine.steps import Context, Step, write_checks
from pipeline.shared.zensus.cells import inner_cells
from pipeline.shared.zensus.tables import read_4000w


def run(ctx: Context) -> None:
    c, s = ctx.config, ctx.store
    inner = inner_cells(s)
    cells = (inner.merge(s.read(OWNERSHIP_CELLS)[["cell_id", "dw_coop"]], on="cell_id", how="left")
             .merge(s.read(CELLS_2011_DWELLINGS), on="cell_id", how="left"))
    cols_2011 = [x for x in cells.columns if x.endswith("_2011")]
    cells[cols_2011] = cells[cols_2011].fillna(0)
    cells["dw_coop"] = cells["dw_coop"].fillna(0.0)
    q = coops_by_quarter(coop_cells(cells))
    s.write(COOPS_QUARTERS, q)
    table = read_4000w(c.ZENSUS_4000W.read_text(encoding="utf-8-sig"))
    write_checks(s, COOPS_CHECKS, coop_checks(q, table["coop"]))
    ctx.log(f"Frankfurt: {q['coop_value'].sum():,.0f} coop dwellings (counted 2011 {q['counted_2011'].sum():,.0f}, "
            f"gap 2011 {q['gap_2011'].sum():,.0f}, estimate 2022 {q['estimate_2022'].sum():,.0f})")


STEP = Step("coops", run, needs=(CELLS_2022, CELLS_2011_DWELLINGS, OWNERSHIP_CELLS),
            makes=(COOPS_QUARTERS, COOPS_CHECKS))
