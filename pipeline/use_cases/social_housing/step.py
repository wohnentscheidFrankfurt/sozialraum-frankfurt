"""Step social_housing: social housing per quarter from the annual report."""
from __future__ import annotations

from pipeline.shared.core.indicator import year_of
from pipeline.shared.core.stats import STORED_DECIMALS
from pipeline.shared.core.texts import LANGUAGES
from pipeline.engine.datasets import (SOCIAL_HOUSING_BY_QUARTER, SOCIAL_HOUSING_CALC_EXAMPLES, SOCIAL_HOUSING_CHECKS,
                                      SOCIAL_HOUSING_CITY, in_language, languages)
from pipeline.shared.core.calc_example import example_payload, require_example_quarters
from pipeline.shared.geography.sources import load_quarters
from pipeline.shared.readers.pdf import page_texts
from pipeline.shared.readers.reference import read_reference
from pipeline.use_cases.social_housing.catalog import (CALC_EXAMPLE_QUARTERS, SH_AS_OF, T,
                                                       social_housing_calc_example)
from pipeline.use_cases.social_housing.checks import (check_social_housing, check_social_housing_monitoring,
                                                      check_social_housing_protocol, check_social_housing_totals)
from pipeline.use_cases.social_housing.model import (city_totals, city_values_rows, indicators, merge_quarters,
                                                     stock_on_quarters)
from pipeline.use_cases.social_housing.sources import (HEADING_STOCK, STOCK_AIRPORT_ROW, check_report_year,
                                                       read_dwelling_stock, read_table)
from pipeline.engine.steps import Context, Step, write_checks


def run(ctx: Context) -> None:
    pages = page_texts(ctx.config.ANNUAL_REPORT_PDF)
    check_report_year(pages, year_of(SH_AS_OF))
    quarters = {q.id for q in load_quarters(ctx.config.QUARTERS_GML)}
    table_stock = read_table(pages, HEADING_STOCK, 3)
    stock, outside_stock = merge_quarters(table_stock, quarters)
    # base of the share: the city's count on the same day as the report (dormitories included), not the Zensus 2022
    year = int(year_of(SH_AS_OF))
    dwellings = stock_on_quarters(read_dwelling_stock(ctx.config.DWELLING_STOCK_XLSX, year), quarters, STOCK_AIRPORT_ROW)
    by_quarter = indicators(stock, dwellings)
    ctx.store.write(SOCIAL_HOUSING_BY_QUARTER, by_quarter.round(STORED_DECIMALS).rename(columns={"quarter": "id"}))
    for lang in LANGUAGES:
        ctx.store.write(in_language(SOCIAL_HOUSING_CALC_EXAMPLES, lang), calc_examples(stock, dwellings, by_quarter, lang))
    info = city_totals(stock, dwellings) | {"total_stock": table_stock["Gesamt"],
                                            "outside_stock": outside_stock,
                                            "dwellings_total": int(sum(dwellings.values())),
                                            "report_text": "\n".join(pages)}
    ctx.store.write(SOCIAL_HOUSING_CITY, city_values_rows(info))
    c = ctx.config
    write_checks(ctx.store, SOCIAL_HOUSING_CHECKS,
                 [check_social_housing(info), *check_social_housing_totals(info, read_reference(c.CHECK_REFERENCE_CSV)),
                  check_social_housing_protocol(info),
                  check_social_housing_monitoring(info["SH_SHARE"],
                                                  read_reference(c.MONITORING_CITY_VALUES_CSV, "indicator")["SH_SHARE_MONITORING"])])
    ctx.log(f"social housing {info['SH_COUNT']} ({info['SH_SHARE']:.2f} %)")


def calc_examples(stock: dict[str, list[int]], dwellings: dict[str, float], by_quarter, lang: str) -> dict:
    """The worked example of the share in one language, in the Stadtteil named in CALC_EXAMPLE_QUARTERS. The numbers
    are those of `indicators`."""
    require_example_quarters(stock, CALC_EXAMPLE_QUARTERS)
    values = by_quarter.set_index("quarter")
    return {kid: example_payload(social_housing_calc_example(area, stock[area][0], dwellings[area],
                                                             values.loc[area, kid], T[lang]))
            for kid, area in CALC_EXAMPLE_QUARTERS.items()}


STEP = Step("social_housing", run, makes=(SOCIAL_HOUSING_BY_QUARTER, SOCIAL_HOUSING_CITY,
                                          *languages(SOCIAL_HOUSING_CALC_EXAMPLES), SOCIAL_HOUSING_CHECKS))
