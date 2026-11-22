"""Step new_construction: the view „Neubau“ (all dwellings per year as new construction and conversions, the
subsidised part; the block of the stock of dwellings, the population, the rents of the Mietspiegel, the prices and the
wages as an index) with its checks."""
from __future__ import annotations

from pipeline.engine.datasets import (NEW_CONSTRUCTION, NEW_CONSTRUCTION_CHECKS, NEW_CONSTRUCTION_RENTS,
                                      NEW_CONSTRUCTION_STOCK, NEW_CONSTRUCTION_VIEW, in_language, languages)
from pipeline.engine.steps import Context, Step, write_checks
from pipeline.shared.core.texts import LANGUAGES
from pipeline.shared.readers.pdf import page_texts
from pipeline.use_cases.new_construction.catalog import (CONFIRM_FW1_LAST, FIRST_YEAR, LAST_YEAR, NEW_BASE, OLD_BASE,
                                                         PHRASES, PRICE_MONTH, PROVISIONAL_FROM, RENT_AXES,
                                                         RENT_FROM, RENT_SOURCES, RENT_TO, RENTS_TEXTS,
                                                         REPORT_GROWTHS, STOCK_BREAKS, SUBSIDISED_SOURCES, T, TEXTS,
                                                         WAGE_QUARTERS, YEARS)
from pipeline.use_cases.new_construction.checks import new_construction_checks, rents_checks, stock_checks
from pipeline.use_cases.new_construction.model import (SERIES, add_report_year, facts, rents_facts, rents_table,
                                                       rents_view, series, stock_facts, stock_series, up_to_last_year,
                                                       up_to_year, view, year_prices, year_wages)
from pipeline.use_cases.new_construction.sources import (read_answer, read_b12, read_b483_totals,
                                                         read_household_size, read_population_report,
                                                         read_price_index, read_regional_all,
                                                         read_regional_new_nonres, read_regional_population,
                                                         read_regional_series, read_regional_stock,
                                                         read_rent_surveys, read_report_growths, read_table_4,
                                                         read_table_15, read_table_17, read_table_19,
                                                         read_wage_index)


def run(ctx: Context) -> None:
    c = ctx.config
    report = page_texts(c.HSL_COMPLETIONS_2025_PDF)
    new_res = read_regional_series(c.REGIONAL_COMPLETIONS_CSV.read_text(encoding="utf-8"))
    new_nonres = read_regional_new_nonres(c.REGIONAL_NEW_NONRES_CSV.read_text(encoding="utf-8"))
    all_dwellings = read_regional_all(c.REGIONAL_ALL_DWELLINGS_CSV.read_text(encoding="utf-8"))
    year, _, dwellings = read_table_17(report)
    new_res = add_report_year(new_res, year, dwellings, LAST_YEAR)
    year, dwellings = read_table_19(report)
    new_nonres = add_report_year(new_nonres, year, dwellings, LAST_YEAR)
    year, dwellings = read_table_15(report)
    all_dwellings = add_report_year(all_dwellings, year, dwellings, LAST_YEAR)
    subsidised = {y: v for y, v in read_b12(page_texts(c.SUBSIDISED_B12_PDF)).items() if y < PROVISIONAL_FROM}
    answers = {}
    for s in SUBSIDISED_SOURCES:
        answers[(s["year"], s["programme"])] = read_answer(page_texts(getattr(c, s["config"])), s["pattern"],
                                                           s["group"])
    for y in range(PROVISIONAL_FROM, LAST_YEAR + 1):
        subsidised[y] = (answers[(y, "fw1")], answers[(y, "fw2")])
    table = series(new_res, new_nonres, all_dwellings, subsidised, FIRST_YEAR, LAST_YEAR, PROVISIONAL_FROM)
    f = facts(table, YEARS)
    stock = read_regional_stock(c.REGIONAL_STOCK_CSV.read_text(encoding="utf-8"))
    year, dwellings = read_table_4(page_texts(c.HSL_STOCK_2025_PDF), NEW_BASE)
    stock = add_report_year(stock, year, dwellings, LAST_YEAR)
    # the population of the last year comes from the Regionaldatenbank; the report A I 2 of the last year only
    # checks it (stock_checks)
    population = up_to_last_year(read_regional_population(c.REGIONAL_POPULATION_CSV.read_text(encoding="utf-8")),
                                 LAST_YEAR, "population")
    stock_year, stock_old = read_table_4(page_texts(c.HSL_STOCK_2022_OLD_BASE_PDF), OLD_BASE)
    population_year, population_old = read_population_report(page_texts(c.HSL_POPULATION_2022_OLD_BASE_PDF),
                                                             OLD_BASE)
    bridge = {"stock": {stock_year: stock_old}, "population": {population_year: population_old}}
    population_report = read_population_report(page_texts(c.HSL_POPULATION_2025_PDF), NEW_BASE)
    stock_table = stock_series(stock, population, all_dwellings, FIRST_YEAR, LAST_YEAR, STOCK_BREAKS)
    # the stock checks and the log look at the last year of the stock (LAST_YEAR); the rents block ends at RENT_TO
    sf = stock_facts(stock_table, RENT_FROM, STOCK_BREAKS, bridge)
    rent_stock = up_to_year(stock_table, RENT_TO)
    rent_sf = stock_facts(rent_stock, RENT_FROM, STOCK_BREAKS, bridge)
    # the rents, the prices and the wages; each PDF is read once (the reports of a Mietspiegel serve values and growths)
    pages: dict[str, list[str]] = {}

    def pages_of(name: str) -> list[str]:
        if name not in pages:
            pages[name] = page_texts(getattr(c, name))
        return pages[name]

    surveys = read_rent_surveys(pages_of, RENT_SOURCES)
    growths = read_report_growths(pages_of, REPORT_GROWTHS)
    prices = read_price_index(pages_of("HSL_PRICES_PDF"))
    wages = read_wage_index(c.HSL_WAGES_XLSX)
    households = read_household_size(c.HOUSEHOLDS_CSV.read_text(encoding="utf-8"))
    months = {y: survey["month"][1] for y, survey in surveys.items()}  # a year without survey takes PRICE_MONTH
    rent_table = rents_table(rent_stock, surveys, year_prices(prices, months, RENT_FROM, RENT_TO, PRICE_MONTH),
                             year_wages(wages, WAGE_QUARTERS, RENT_FROM, RENT_TO), RENT_FROM, RENT_TO)
    rf = rents_facts(rent_table, rent_sf, households, RENT_FROM, RENT_TO)
    rents = {lang: rents_view(rent_table, rf, RENTS_TEXTS[lang], bridge, STOCK_BREAKS, RENT_AXES, T[lang])
             for lang in LANGUAGES}
    ctx.store.write(NEW_CONSTRUCTION, table)
    ctx.store.write(NEW_CONSTRUCTION_STOCK, stock_table)
    ctx.store.write(NEW_CONSTRUCTION_RENTS, rent_table)
    for lang in LANGUAGES:
        ctx.store.write(in_language(NEW_CONSTRUCTION_VIEW, lang),
                        {**view(table, TEXTS[lang], T[lang]), "rents": rents[lang]})
    ctx.log(f"dwellings {FIRST_YEAR}–{LAST_YEAR}: all {table['all'].sum()}, new {table['new'].sum()}, conversions "
            f"{table['conversions'].sum()}, subsidised {table['subsidised'].sum()}; share {LAST_YEAR}: "
            f"{100 * f['share_last']:.1f} %")
    for name in SERIES:
        ctx.log(f"{name} 31.12.{LAST_YEAR}: {int(stock_table[name].iloc[-1])}; growth {sf['from_year']}–{LAST_YEAR} "
                f"published {100 * sf[name + '_growth']:.2f} %, chained {100 * sf[name + '_growth_chained']:.2f} %; "
                f"base effect 31.12.{sf['break_year']}: {sf[name + '_base_effect']}")
    now = rent_table.set_index("year").loc[RENT_TO]
    ctx.log(f"rents index {RENT_TO} ({RENT_FROM} = 100): new {now['new_index']:.1f}, old {now['old_index']:.1f}, "
            f"prices {now['prices_index']:.1f}, wages {now['wages_index']:.1f}, dwellings {now['stock_index']:.1f}, "
            f"population {now['population_index']:.1f}; without inflation: new {now['new_real']:.1f}, old "
            f"{now['old_real']:.1f}, wages {now['wages_real']:.1f}")
    confirm = read_answer(page_texts(getattr(c, CONFIRM_FW1_LAST["config"])), CONFIRM_FW1_LAST["pattern"],
                          CONFIRM_FW1_LAST["group"])
    report_2024 = page_texts(c.HSL_COMPLETIONS_2024_PDF)
    b483 = read_b483_totals(page_texts(c.ANSWER_B_483_2025_PDF))
    checks = []
    for lang in LANGUAGES:  # the statements in the texts of each language
        checks += (new_construction_checks(table, f, read_table_17(report_2024), confirm, read_table_15(report_2024),
                                           read_table_19(report_2024), b483, TEXTS[lang], PHRASES[lang], T[lang])
                   + stock_checks(stock_table, sf, population_report, RENTS_TEXTS[lang], PHRASES[lang], lang)
                   + rents_checks(rent_table, rf, rents[lang], growths, surveys, prices, RENTS_TEXTS[lang],
                                  PHRASES[lang], T[lang]))
    write_checks(ctx.store, NEW_CONSTRUCTION_CHECKS, checks)


STEP = Step("new_construction", run, makes=(NEW_CONSTRUCTION, NEW_CONSTRUCTION_STOCK, NEW_CONSTRUCTION_RENTS,
                                            *languages(NEW_CONSTRUCTION_VIEW), NEW_CONSTRUCTION_CHECKS))
