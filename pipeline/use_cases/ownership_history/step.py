"""Step ownership_history: the view „Trend“ (Zensus 2011 against 2022) with its checks."""
from __future__ import annotations

from pipeline.engine.datasets import (COMPANY_BUILDINGS_BY_DECADE, OWNERSHIP_BY_SIZE, OWNERSHIP_HISTORY,
                                      OWNERSHIP_HISTORY_CHECKS, OWNERSHIP_HISTORY_VIEW, in_language, languages)
from pipeline.shared.core.texts import LANGUAGES
from pipeline.use_cases.ownership_history.catalog import EXAMPLES, GROUP_TEXTS, PHRASES, T
from pipeline.use_cases.ownership_history.checks import check_condo_rented, history_checks
from pipeline.use_cases.ownership_history.model import (by_size, company_buildings_by_decade, history_data,
                                                        history_facts, history_groups)
from pipeline.shared.readers.html import example_texts
from pipeline.engine.steps import Context, Step, write_checks
from pipeline.shared.zensus.tables import (read_4000w, read_buildings_by_decade, read_buildings_by_size, read_condo_use,
                                           read_dwellings_by_size, read_dwellings_history)


def run(ctx: Context) -> None:
    c = ctx.config
    buildings = read_buildings_by_size(c.ZENSUS_3000G_2007.read_text(encoding="utf-8"))
    dwellings = read_dwellings_by_size(c.ZENSUS_4000W_2013.read_text(encoding="utf-8"))
    history = read_dwellings_history(c.ZENSUS_4000W_1011.read_text(encoding="utf-8"))
    decade_classes, by_decade = read_buildings_by_decade(c.ZENSUS_3000G_2001.read_text(encoding="utf-8"))
    groups, sizes = history_groups(history, buildings), by_size(buildings, dwellings)
    decades = company_buildings_by_decade(decade_classes, by_decade)
    ctx.store.write(OWNERSHIP_HISTORY, groups)
    ctx.store.write(OWNERSHIP_BY_SIZE, sizes)
    ctx.store.write(COMPANY_BUILDINGS_BY_DECADE, decades)
    ctx.log(groups.pivot(index="group", columns="year", values=["buildings", "dwellings"]).to_string())
    f = history_facts(groups, decades, sizes)
    ctx.log(f"companies 2022/2011: dwellings {f['company_factor']:.2f}, buildings {f['company_building_factor']:.2f}; "
            f"share 2022: buildings {100 * f['company_building_share_2022']:.1f} %, "
            f"dwellings {100 * f['company_share_2022']:.1f} %")
    ctx.log(f"companies in buildings with 13 or more dwellings: {100 * f['company_large_share_2011']:.1f} % (2011), "
            f"{100 * f['company_large_share_2022']:.1f} % (2022); {f['company_large_growth']} of "
            f"{f['company_dwelling_growth']} additional dwellings ({100 * f['large_growth_share']:.0f} %); "
            f"company buildings built before 2010: {100 * f['share_before_2010']:.0f} % of the growth")
    for lang in LANGUAGES:
        ctx.store.write(in_language(OWNERSHIP_HISTORY_VIEW, lang), history_data(groups, sizes, decades, T[lang]))
    text_4000w = c.ZENSUS_4000W.read_text(encoding="utf-8-sig")
    table = read_4000w(text_4000w)
    condo_use = read_condo_use(text_4000w)
    write_checks(ctx.store, OWNERSHIP_HISTORY_CHECKS, history_checks(history, by_decade, buildings, dwellings, table, f,
                                                                     example_texts(c, EXAMPLES), EXAMPLES)
                 + [check_condo_rented(condo_use, GROUP_TEXTS[lang]["condo"]["about"], PHRASES[lang]["condo_rented"])
                    for lang in LANGUAGES])


STEP = Step("ownership_history", run, makes=(OWNERSHIP_HISTORY, OWNERSHIP_BY_SIZE, COMPANY_BUILDINGS_BY_DECADE,
                                             *languages(OWNERSHIP_HISTORY_VIEW), OWNERSHIP_HISTORY_CHECKS))
