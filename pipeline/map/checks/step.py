"""Step checks: collects the check results of all steps, writes the check report and stops the build on FAIL."""
from __future__ import annotations

import datetime as dt

from pipeline.map.assembly.catalog import CATALOG
from pipeline.map.checks import model as m
from pipeline.shared.core.checks import FAIL, from_rows
from pipeline.engine.datasets import (CELLS_2022, CHECK_REPORT, CHECK_RESULTS, INDICATORS_DISTRICTS,
                                      INDICATORS_QUARTERS, OWNERSHIP_CELLS)
from pipeline.engine.steps import Context, Step
from pipeline.shared.zensus.cells import inner_cells

PLAUSIBILITY = [(k.id, k.title) for k in CATALOG if k.type == "number" and k.criterion and "district" in k.levels]


def run(ctx: Context) -> None:
    s = ctx.store
    checks = [check for dataset in CHECK_RESULTS for check in from_rows(s.read(dataset))]
    ownership, cells = s.read(OWNERSHIP_CELLS), inner_cells(s)
    sections = m.report_sections(ownership["dw_unassigned"].sum(), int(cells["dwellings"].sum()),
                                 ownership["dw_from_2011"].sum(), int((ownership["dw_from_2011"] > 0).sum()),
                                 s.read(INDICATORS_DISTRICTS), s.read(INDICATORS_QUARTERS), PLAUSIBILITY)
    s.write(CHECK_REPORT, m.report(checks, sections, dt.date.today().isoformat()))
    for x in checks:
        ctx.log(f"{x.status:8} {x.name}: {x.text}")
    failed = [x for x in checks if x.status == FAIL]
    if failed:
        raise SystemExit(f"{len(failed)} check(s) with FAIL, see {s.path(CHECK_REPORT)}")


STEP = Step("checks", run,
            needs=(*CHECK_RESULTS, OWNERSHIP_CELLS, CELLS_2022, INDICATORS_DISTRICTS, INDICATORS_QUARTERS),
            makes=(CHECK_REPORT,))
