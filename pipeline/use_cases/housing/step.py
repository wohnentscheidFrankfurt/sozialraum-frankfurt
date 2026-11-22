"""Step housing: means of the Zensus grid per district, Stadtteil and Frankfurt, and the checks against the Zensus tables."""
from __future__ import annotations

import pandas as pd

from pipeline.shared.core.areas import city_rows, per_area
from pipeline.shared.core.calc_example import example_payload, require_example_quarters
from pipeline.engine.datasets import (CELLS_2022, HOUSING_BY_DISTRICT, HOUSING_BY_QUARTER, HOUSING_CALC_EXAMPLES,
                                      HOUSING_CHECKS, HOUSING_CITY, in_language, languages)
from pipeline.shared.core.texts import LANGUAGES
from pipeline.use_cases.housing.checks import (check_city_tables, check_vacancy_4000w, check_vacancy_city,
                                                 check_vacancy_count, check_vacancy_km)
from pipeline.use_cases.housing.catalog import (CALC_EXAMPLE_QUARTERS, COUNTS, T, renters_calc_example,
                                                vacancy_calc_example)
from pipeline.use_cases.housing.model import fill_rate, housing_coverage, housing_values, renter_parts, vacancy_parts
from pipeline.shared.readers.reference import read_reference
from pipeline.engine.steps import Context, Step, write_checks
from pipeline.shared.zensus.sources import GRID_KM_COLUMNS, read_km_rates
from pipeline.shared.zensus.tables import OWNER_RATE, RENT_SQM, VACANCY_RATE, read_city_value, read_vacancy_4000w

# (rate column, dash column, 1 km extract) of the two vacancy rates
VACANCY_RATES = (("vacancy_rate", "vacancy_rate_dash", "zensus_vacancy.zip"),
                 ("vacancy_rate_market", "vacancy_rate_market_dash", "zensus_vacancy_market.zip"))
# (rate column, dash column) of each vacancy share with a worked example
VACANCY_COLUMNS = {"HOU_VACANT_ALL": VACANCY_RATES[0][:2], "HOU_VACANT_MARKET": VACANCY_RATES[1][:2]}


def _area_values(key: str, g) -> dict:
    return {**housing_values(g), **housing_coverage(g)}


def run(ctx: Context) -> None:
    s, c = ctx.store, ctx.config
    cells = s.read(CELLS_2022)
    for rate, dash, name in VACANCY_RATES:  # balance each 1 km cell over inner and edge cells, then keep the inner ones
        km_rates = read_km_rates(c.GRID_KM_EXTRACTS[name], GRID_KM_COLUMNS[name])
        cells[rate] = fill_rate(cells, rate, dash, km_rates)
    cells = cells[cells["edge"] == 0].reset_index(drop=True)
    s.write(HOUSING_BY_DISTRICT, per_area(cells, "district", _area_values))
    by_quarter = per_area(cells, "quarter", _area_values)
    s.write(HOUSING_BY_QUARTER, by_quarter)
    for lang in LANGUAGES:
        s.write(in_language(HOUSING_CALC_EXAMPLES, lang), calc_examples(cells, by_quarter, lang))
    city = housing_values(cells)
    s.write(HOUSING_CITY, city_rows(city, without=COUNTS))
    table = read_vacancy_4000w(c.ZENSUS_4000W.read_text(encoding="utf-8-sig"))
    table_0001 = c.ZENSUS_4000W_0001.read_text(encoding="utf-8")
    owner_rate = read_city_value(table_0001, OWNER_RATE)
    rent = read_city_value(c.ZENSUS_4000W_0004.read_text(encoding="utf-8"), RENT_SQM)
    write_checks(s, HOUSING_CHECKS, [check_vacancy_4000w(city["HOU_VACANT_ALL"], table),
                                     check_vacancy_count(city["HOU_VACANT_ALL_DWELLINGS"], table),
                                     check_vacancy_city(city["HOU_VACANT_ALL"],
                                                        read_city_value(table_0001, VACANCY_RATE)),
                                     check_vacancy_km(city, read_reference(c.CHECK_REFERENCE_CSV)),
                                     *check_city_tables(city, owner_rate, rent)])
    ctx.log(", ".join(f"{k} {v:.2f}" for k, v in city.items()))


def calc_examples(cells: pd.DataFrame, by_quarter: pd.DataFrame, lang: str) -> dict:
    """The worked example of each indicator in one language, in the Stadtteil named in CALC_EXAMPLE_QUARTERS (the id
    is the name).
    cells: the inner cells with the filled rates, the same as for by_quarter."""
    require_example_quarters(cells["quarter"].dropna(), CALC_EXAMPLE_QUARTERS)
    values = by_quarter.set_index("id")
    out = {}
    for kid, area in CALC_EXAMPLE_QUARTERS.items():
        g, share = cells[cells["quarter"] == area], values.loc[area, kid]
        if kid == "HOU_RENTERS":
            example = renters_calc_example(area, *renter_parts(g), share, T[lang])
        else:
            example = vacancy_calc_example(kid, area, *vacancy_parts(g, *VACANCY_COLUMNS[kid]), share, T[lang])
        out[kid] = example_payload(example)
    return out


STEP = Step("housing", run, needs=(CELLS_2022,),
            makes=(HOUSING_BY_DISTRICT, HOUSING_BY_QUARTER, *languages(HOUSING_CALC_EXAMPLES), HOUSING_CITY, HOUSING_CHECKS))
