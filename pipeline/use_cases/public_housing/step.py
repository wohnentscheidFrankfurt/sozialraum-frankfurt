"""Step public_housing: ABG and Nassauische Heimstätte per Stadtteil, the area table and the checks."""
from __future__ import annotations

from pipeline.engine.datasets import (CELLS_2011_BUILDINGS, CELLS_2011_DWELLINGS, CELLS_2022,
                                      PUBLIC_HOUSING_CHECKS, PUBLIC_HOUSING_QUARTERS)
from pipeline.shared.readers.reference import read_reference
from pipeline.use_cases.public_housing.checks import public_checks
from pipeline.use_cases.public_housing.model import (estimate_by_size, new_research_sites,
                                                     public_housing, public_range, research_cells, size_tables)
from pipeline.use_cases.public_housing.sources import read_research_sites
from pipeline.engine.steps import Context, Step, write_checks
from pipeline.shared.zensus.cells import inner_cells
from pipeline.shared.zensus.model import CLASSES, SIZES
from pipeline.shared.zensus.tables import (read_4000w, read_buildings_by_size, read_dwellings_by_size,
                                           read_dwellings_history)


def run(ctx: Context) -> None:
    """ABG and Nassauische Heimstätte per Stadtteil: count of 2011 × change up to 2022 (README)."""
    c = ctx.config
    inner = inner_cells(ctx.store)
    cells = (inner.set_index("cell_id")
             .join(ctx.store.read(CELLS_2011_DWELLINGS).set_index("cell_id"), how="left")
             .join(ctx.store.read(CELLS_2011_BUILDINGS).set_index("cell_id"), how="left"))
    cols_2011 = [x for x in cells.columns if x.endswith("_2011")]
    cells[cols_2011] = cells[cols_2011].fillna(0)
    buildings = read_buildings_by_size(c.ZENSUS_3000G_2007.read_text(encoding="utf-8"))
    dwellings = read_dwellings_by_size(c.ZENSUS_4000W_2013.read_text(encoding="utf-8"))
    est = {}
    for year, suffix, total in ((2011, "_2011", cells["dw_total_2011"]), (2022, "", cells["dwellings"])):
        seed, mean = size_tables(buildings[year], dwellings[year])
        b_owner = cells[[f"bld_{k}{suffix}" for k in CLASSES]].set_axis(list(CLASSES), axis=1)
        b_size = cells[[f"bld_size_{x}{suffix}" for x in SIZES]].set_axis(SIZES, axis=1)
        est[year] = estimate_by_size(b_owner, b_size, total, seed, mean)
    sites = new_research_sites(read_research_sites(c.ABG_SITES_GEOJSON.read_text(encoding="utf-8")))
    q = public_housing(cells, est[2011], est[2022], research_cells(sites, cells[["x25832", "y25832"]]))
    history = read_dwellings_history(c.ZENSUS_4000W_1011.read_text(encoding="utf-8"))[2011]
    gap_municipal = history["municipal"] - cells["dw_municipal_2011"].sum()
    gap_public = gap_municipal + history["state"] - cells["dw_state_2011"].sum()
    q = public_range(q, gap_public, gap_municipal)
    stored = q.reset_index()
    ctx.store.write(PUBLIC_HOUSING_QUARTERS, stored)
    table = read_4000w(c.ZENSUS_4000W.read_text(encoding="utf-8-sig"))
    write_checks(ctx.store, PUBLIC_HOUSING_CHECKS,
                 public_checks(stored, table["municipal"], read_reference(c.CHECK_REFERENCE_CSV), gap_municipal))
    gallus = f", Gallus {q.loc['Gallus', 'abg_value']:,.0f}" if "Gallus" in q.index else ""
    ctx.log(f"Frankfurt: {q['public_value'].sum():,.0f} public dwellings (ABG part {q['abg_value'].sum():,.0f}"
            f"{gallus}); secrecy gap 2011 {gap_public:,.0f}, filled "
            f"{q['fill_2011'].sum():,.0f}; new ABG from the research {q['research_new'].sum():,.0f} "
            f"({len(sites)} sites)")


STEP = Step("public_housing", run, needs=(CELLS_2022, CELLS_2011_DWELLINGS, CELLS_2011_BUILDINGS),
            makes=(PUBLIC_HOUSING_QUARTERS, PUBLIC_HOUSING_CHECKS))
