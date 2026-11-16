"""Step ownership_shares: shares of the ownership groups per district, Stadtteil and Frankfurt."""
from __future__ import annotations

import pandas as pd

from pipeline.shared.core.areas import city_rows, per_area
from pipeline.engine.datasets import (CELLS_2022, COOPS_QUARTERS, OWNERSHIP_CALC_EXAMPLES, OWNERSHIP_CELLS, OWNERSHIP_RANGES,
                                      OWNERSHIP_SHARES_BY_DISTRICT, OWNERSHIP_SHARES_BY_QUARTER,
                                      OWNERSHIP_SHARES_CHECKS, OWNERSHIP_SHARES_CITY, PUBLIC_HOUSING_QUARTERS)
from pipeline.shared.geography.sources import load_quarters
from pipeline.shared.core.calc_example import example_payload
from pipeline.use_cases.coops.catalog import coop_calc_example
from pipeline.use_cases.ownership_cells.model import grid_factors
from pipeline.use_cases.ownership_shares.catalog import (CALC_EXAMPLE_QUARTERS, EXAMPLES, INDICATORS,
                                                         other_calc_example)
from pipeline.use_cases.public_housing.catalog import public_calc_example
from pipeline.use_cases.ownership_shares.checks import (check_city_shares, check_city_within_range, check_dwellings,
                                                        check_dwellings_total,
                                                        check_examples, check_ownership_shares, check_ranges,
                                                        check_rest)
from pipeline.shared.core.calc_example import require_example_quarters
from pipeline.shared.readers.html import example_texts
from pipeline.use_cases.ownership_shares.model import (DWELLING_COLUMNS, all_dwellings, building_counts,
                                                       by_quarter, city_total, half_points, other_numbers,
                                                       quarter_values, range_rows,
                                                       require_quarters, rest_dwellings)
from pipeline.engine.steps import Context, Step, write_checks
from pipeline.shared.zensus.cells import inner_cells
from pipeline.shared.zensus.tables import read_4000w


def run(ctx: Context) -> None:
    s, c = ctx.store, ctx.config
    cells = inner_cells(s).merge(s.read(OWNERSHIP_CELLS), on="cell_id", how="left")
    public_table, coop_table = s.read(PUBLIC_HOUSING_QUARTERS), s.read(COOPS_QUARTERS)
    public = by_quarter(public_table, "public_value", "public_half")
    coop = by_quarter(coop_table, "coop_value", "coop_half")
    require_quarters(cells["quarter"].dropna(), public, "ABG and NH", "public_housing")
    require_quarters(cells["quarter"].dropna(), coop, "Genossenschaften", "coops")
    by_district = per_area(cells, "district", lambda key, g: building_counts(g))
    by_quarter_ = per_area(cells, "quarter", lambda key, g: quarter_values(g, public[key], coop[key]))
    rest = per_area(cells, "quarter", lambda key, g: {"rest": rest_dwellings(g, public[key]["value"],
                                                                             coop[key]["value"])})
    totals = per_area(cells, "quarter", lambda key, g: {"total": all_dwellings(g)})
    halves = per_area(cells, "quarter", lambda key, g: half_points(public[key], coop[key],
                                                                         all_dwellings(g)))
    public_city, coop_city = city_total(public_table, "public_value"), city_total(coop_table, "coop_value")
    city = quarter_values(cells, public_city, coop_city)
    # Frankfurt shows no range; for the check the half ranges of the Stadtteile add up
    city_halves = half_points(public_city | {"half": public_table["public_half"].sum()},
                              coop_city | {"half": coop_table["coop_half"].sum()},
                              all_dwellings(cells))
    s.write(OWNERSHIP_SHARES_BY_DISTRICT, by_district)
    s.write(OWNERSHIP_SHARES_BY_QUARTER, by_quarter_)
    s.write(OWNERSHIP_SHARES_CITY, city_rows(city, without=frozenset(DWELLING_COLUMNS)))
    s.write(OWNERSHIP_RANGES, range_rows(halves))
    names = pd.DataFrame([{"id": q.id, "name": q.name} for q in load_quarters(c.QUARTERS_GML)])
    table = read_4000w(c.ZENSUS_4000W.read_text(encoding="utf-8-sig"))
    s.write(OWNERSHIP_CALC_EXAMPLES, calc_examples(cells, by_quarter_, table, public_table, coop_table))
    write_checks(s, OWNERSHIP_SHARES_CHECKS,
                 [check_ownership_shares(by_quarter_.merge(names, on="id")), check_rest(rest.merge(names, on="id")),
                  check_ranges(by_quarter_.merge(names, on="id"), halves),
                  check_dwellings(by_quarter_.merge(names, on="id")),
                  check_dwellings_total(by_quarter_.merge(names, on="id"), totals),
                  *check_city_shares(city, table), check_city_within_range(city, city_halves, table),
                  check_examples(example_texts(c, EXAMPLES))])
    shares = (k for k in city if k.startswith("OWN_") and not k.endswith(("_LOW", "_HIGH", "_DWELLINGS")))
    ctx.log("Frankfurt: " + ", ".join(f"{k} {city[k]:.1f} %" for k in shares))


def calc_examples(cells: pd.DataFrame, by_quarter_: pd.DataFrame, table: dict, public_table: pd.DataFrame,
                  coop_table: pd.DataFrame) -> dict:
    """The worked example of each group, in the Stadtteil named in CALC_EXAMPLE_QUARTERS (the id is the name)."""
    require_example_quarters(cells["quarter"].dropna(), CALC_EXAMPLE_QUARTERS)
    factors = grid_factors(cells, table)
    values = by_quarter_.set_index("id")
    out = {}
    for group, area in CALC_EXAMPLE_QUARTERS.items():
        g, row = cells[cells["quarter"] == area], values.loc[area]
        total = all_dwellings(g)
        if group == "OWN_PUBLIC":
            example = public_calc_example(area, public_table.set_index("quarter").loc[area], total, row[group])
        elif group == "OWN_COOP":
            example = coop_calc_example(area, coop_table.set_index("quarter").loc[area], total, row[group])
        else:
            n = other_numbers(g, group, factors, row[f"{group}_DWELLINGS"])
            example = other_calc_example(group, area, n, row[group])
        out[group] = example_payload(example)
    return out


STEP = Step("ownership_shares", run, needs=(CELLS_2022, OWNERSHIP_CELLS, PUBLIC_HOUSING_QUARTERS, COOPS_QUARTERS),
            makes=(OWNERSHIP_SHARES_BY_DISTRICT, OWNERSHIP_SHARES_BY_QUARTER, OWNERSHIP_SHARES_CITY,
                   OWNERSHIP_RANGES, OWNERSHIP_CALC_EXAMPLES, OWNERSHIP_SHARES_CHECKS))
