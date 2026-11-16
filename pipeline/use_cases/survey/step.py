"""Step survey: the printed class of each survey area on its districts, the rent burden per income group from the
microdata of both survey years, the printed and own city values and the checks against the reports."""
from __future__ import annotations

import pandas as pd

from pipeline.engine.datasets import (SURVEY_BY_DISTRICT, SURVEY_CALC_EXAMPLES, SURVEY_CHECKS, SURVEY_CITY,
                                      SURVEY_HALF_WIDTHS, SURVEY_RESPONDENTS)
from pipeline.shared.core.calc_example import example_payload
from pipeline.shared.geography.sources import load_districts
from pipeline.engine.steps import Context, Step, write_checks
from pipeline.shared.readers.pdf import page_texts
from pipeline.use_cases.survey.catalog import survey_calc_example
from pipeline.use_cases.survey.checks import (check_area_codes, check_own_against_printed, check_printed_city_sentence,
                                              check_printed_extremes)
from pipeline.use_cases.survey.model import (area_weight_shares, breakdown_half_widths, burden_ratios,
                                             example_household, income_breakdown, survey_by_district, survey_city,
                                             survey_table, tenant_medians)
from pipeline.use_cases.survey.sources import (FIGURES, PRINTED_CITY_BURDEN, PRINTED_EXTREMES, SURVEY_AREAS,
                                               read_microdata)


def run(ctx: Context) -> None:
    c = ctx.config
    names = list(SURVEY_AREAS.values())
    respondents = {year: read_microdata(path, year) for year, path in c.SURVEY_MICRODATA.items()}
    pooled = pd.concat(respondents.values(), ignore_index=True)  # both years pooled (README)
    ratios = burden_ratios(pooled)
    survey = survey_table(FIGURES, names).merge(income_breakdown(ratios, names), on="survey_area", how="left")
    areas = pd.DataFrame([{"id": d.id, "survey_area": d.survey_area}
                          for d in load_districts(c.DISTRICTS_GML, c.MONITORING_CSV)])
    ctx.store.write(SURVEY_BY_DISTRICT, survey_by_district(survey, areas))
    ctx.store.write(SURVEY_CITY, survey_city(survey))
    ctx.store.write(SURVEY_RESPONDENTS, pooled)
    ctx.store.write(SURVEY_HALF_WIDTHS, breakdown_half_widths(ratios, names))
    ctx.store.write(SURVEY_CALC_EXAMPLES,
                    {"LIF_RENT_BURDEN_RATIO": example_payload(survey_calc_example(example_household(ratios)))})
    pages = {2025: page_texts(c.SURVEY_REPORT_PDF), 2024: page_texts(c.SURVEY_REPORT_2024_PDF)}
    own = {year: tenant_medians(ratios[ratios["year"] == year]) for year in PRINTED_CITY_BURDEN}
    write_checks(ctx.store, SURVEY_CHECKS, [
        check_printed_extremes(pages[2025], FIGURES, PRINTED_EXTREMES),
        check_printed_city_sentence(pages, PRINTED_CITY_BURDEN),
        check_own_against_printed(own, FIGURES["LIF_RENT_BURDEN_RATIO"]["classes"], PRINTED_CITY_BURDEN),
        check_area_codes({year: area_weight_shares(r) for year, r in respondents.items()})])
    ctx.log(survey.to_string(index=False))


STEP = Step("survey", run, makes=(SURVEY_BY_DISTRICT, SURVEY_CITY, SURVEY_RESPONDENTS, SURVEY_HALF_WIDTHS,
                         SURVEY_CALC_EXAMPLES, SURVEY_CHECKS))
