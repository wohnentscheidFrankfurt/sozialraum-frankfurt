"""Steps zensus (grid 2022 with district and quarter per cell) and zensus_2011 (the 2011 grid of dwellings and of
buildings on the inner cells of 2022). Both read the Frankfurt extracts in sources/zensus/grid every time."""
from __future__ import annotations

from pipeline.shared.zensus.checks import grid_checks
from pipeline.shared.zensus.model import assemble_cells
from pipeline.shared.zensus.sources import (COUNT_COLUMNS, GRID_FILES, VALUE_COLUMNS, read_2011, read_2011_buildings,
                                            read_grid_csv)
from pipeline.engine.datasets import CELLS_2011_BUILDINGS, CELLS_2011_DWELLINGS, CELLS_2022, ZENSUS_CHECKS
from pipeline.shared.geography.sources import load_districts
from pipeline.shared.readers.reference import read_reference
from pipeline.engine.steps import Context, Step, write_checks


def run_zensus(ctx: Context) -> None:
    districts = load_districts(ctx.config.DISTRICTS_GML, ctx.config.MONITORING_CSV)
    cells: dict[str, dict] = {}
    for file, columns in GRID_FILES.items():
        for cell_id, values in read_grid_csv(ctx.config.GRID_EXTRACTS[file], columns).items():
            cells.setdefault(cell_id, {}).update(values)
        ctx.log(f"read {file}: {len(cells)} cells")
    df = assemble_cells(cells, districts, COUNT_COLUMNS, VALUE_COLUMNS)
    ctx.store.write(CELLS_2022, df)
    write_checks(ctx.store, ZENSUS_CHECKS, grid_checks(df, read_reference(ctx.config.CHECK_REFERENCE_CSV)))
    inner = df[df["edge"] == 0]
    ctx.log(f"{len(inner)} cells in Frankfurt with {inner['pop'].sum()} residents, {df['edge'].sum()} edge cells")


def run_zensus_2011(ctx: Context) -> None:
    cells = ctx.store.read(CELLS_2022)
    inner = set(cells.loc[cells["edge"] == 0, "cell_id"])
    extracts = ctx.config.GRID_EXTRACTS
    ctx.store.write(CELLS_2011_DWELLINGS, read_2011(extracts["zensus2011_dwellings.zip"], inner))
    ctx.store.write(CELLS_2011_BUILDINGS, read_2011_buildings(extracts["zensus2011_buildings.zip"], inner))


ZENSUS_STEP = Step("zensus", run_zensus, makes=(CELLS_2022, ZENSUS_CHECKS))
ZENSUS_2011_STEP = Step("zensus_2011", run_zensus_2011, needs=(CELLS_2022,),
                        makes=(CELLS_2011_DWELLINGS, CELLS_2011_BUILDINGS))
