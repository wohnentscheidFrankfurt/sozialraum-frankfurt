"""Step construction_year: dwellings before 1919 and from 1949 to 1978 per area, and the check against 4000W-1008."""
from __future__ import annotations

import pandas as pd

from pipeline.use_cases.construction_year.catalog import CALC_EXAMPLE_QUARTERS, COUNTS, construction_calc_example
from pipeline.use_cases.construction_year.checks import check_construction_year
from pipeline.use_cases.construction_year.model import CLASSES_2011, capped_class_2011, construction_parts, construction_values
from pipeline.shared.core.areas import city_rows, per_area
from pipeline.shared.core.calc_example import example_payload, require_example_quarters
from pipeline.engine.datasets import (CELLS_2011_DWELLINGS, CELLS_2022, CONSTRUCTION_YEAR_BY_DISTRICT,
                                      CONSTRUCTION_YEAR_BY_QUARTER, CONSTRUCTION_YEAR_CALC_EXAMPLES,
                                      CONSTRUCTION_YEAR_CHECKS, CONSTRUCTION_YEAR_CITY)
from pipeline.engine.steps import Context, Step, write_checks
from pipeline.shared.zensus.cells import inner_cells
from pipeline.shared.zensus.tables import read_dwellings_by_construction_year


def run(ctx: Context) -> None:
    s, c = ctx.store, ctx.config
    inner = inner_cells(s)
    cells = inner.merge(s.read(CELLS_2011_DWELLINGS), on="cell_id", how="left")
    s.write(CONSTRUCTION_YEAR_BY_DISTRICT, per_area(cells, "district", lambda key, g: construction_values(g)))
    by_quarter = per_area(cells, "quarter", lambda key, g: construction_values(g))
    s.write(CONSTRUCTION_YEAR_BY_QUARTER, by_quarter)
    s.write(CONSTRUCTION_YEAR_CALC_EXAMPLES, calc_examples(cells, by_quarter))
    s.write(CONSTRUCTION_YEAR_CITY, city_rows(construction_values(cells), without=COUNTS))
    grid_2011 = {k: int(cells[f"dw_{k}_2011"].fillna(0).sum()) for k in ("pre1919", "1949_1978", "total")}
    table = read_dwellings_by_construction_year(c.ZENSUS_4000W_1008.read_text(encoding="utf-8"))
    # city shares unrounded: class 2011 capped per cell ÷ dwellings 2022 of the inner cells
    # (the grid checks above stay uncapped)
    shares = {k: 100 * capped_class_2011(cells, f"dw_{k}_2011").sum() / inner["dwellings"].sum()
              for k in ("pre1919", "1949_1978")}
    write_checks(s, CONSTRUCTION_YEAR_CHECKS, check_construction_year(grid_2011, table, shares))


def calc_examples(cells: pd.DataFrame, by_quarter: pd.DataFrame) -> dict:
    """The worked example of each class, in the Stadtteil named in CALC_EXAMPLE_QUARTERS (the id is the name).
    cells: the inner cells with the 2011 counts, the same as for by_quarter."""
    require_example_quarters(cells["quarter"].dropna(), CALC_EXAMPLE_QUARTERS)
    values = by_quarter.set_index("id")
    columns = dict(CLASSES_2011)
    return {kid: example_payload(construction_calc_example(kid, area, *construction_parts(
        cells[cells["quarter"] == area], columns[kid]), values.loc[area, kid]))
        for kid, area in CALC_EXAMPLE_QUARTERS.items()}


STEP = Step("construction_year", run, needs=(CELLS_2022, CELLS_2011_DWELLINGS),
            makes=(CONSTRUCTION_YEAR_BY_DISTRICT, CONSTRUCTION_YEAR_BY_QUARTER, CONSTRUCTION_YEAR_CITY,
                   CONSTRUCTION_YEAR_CALC_EXAMPLES, CONSTRUCTION_YEAR_CHECKS))
