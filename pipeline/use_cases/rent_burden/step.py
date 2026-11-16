"""Step rent_burden: the view „Miete“ (S1: the warm rent of one flat against the net wage of three model persons;
S2: the warm rent against the household income of adult tenants per income group) with its checks."""
from __future__ import annotations

from pipeline.engine.datasets import (NEW_CONSTRUCTION_RENTS, RENT_BURDEN_CHECKS, RENT_BURDEN_GROUPS,
                                      RENT_BURDEN_VIEW, RENT_BURDEN_WAGE, SURVEY_CALC_EXAMPLES, SURVEY_CITY,
                                      SURVEY_RESPONDENTS)
from pipeline.engine.steps import Context, Step, write_checks
from pipeline.shared.readers.pdf import page_texts
from pipeline.use_cases.new_construction.catalog import RENT_FROM, RENT_TO, SURVEY_DATES
from pipeline.use_cases.rent_burden.catalog import FLAT_M2, LOW_INCOME_TEXTS, PERSONS, WAGE_TEXTS
from pipeline.use_cases.rent_burden.checks import low_income_checks, net_wage_checks, wage_checks
from pipeline.use_cases.rent_burden.model import bars_view, low_income_facts, wage_facts, wage_table, wage_view
from pipeline.use_cases.rent_burden.sources import (MIETSPIEGEL_COSTS, MINDESTLOHN, WAGE_RULES, read_bmf_reference,
                                                    read_est_reference, read_hessen_quantiles, read_median_wage,
                                                    read_mietspiegel_costs, read_mikrozensus_2018, read_nebenkosten)
from pipeline.use_cases.survey.model import BREAKDOWN_IDS

MEASURED_ID = "LIF_RENT_BURDEN_RATIO"  # the published median burden of all tenants in survey_city


def _measured(city: list[dict]) -> float:
    """The value of MEASURED_ID in survey_city. Stops if the row is not there exactly once."""
    values = [row["value"] for row in city if row["indicator"] == MEASURED_ID]
    if len(values) != 1:
        raise ValueError(f"survey_city: {len(values)} rows of {MEASURED_ID}, needs 1")
    return float(values[0])


def run(ctx: Context) -> None:
    c = ctx.config
    years = tuple(sorted(SURVEY_DATES))
    missing = [y for y in years if y not in c.BA_KDU_XLSX]
    if missing:
        raise ValueError(f"no Kosten der Unterkunft file (BA_KDU_XLSX) for the survey year(s) "
                         f"{', '.join(map(str, missing))}")
    # S1: the rents of new_construction (the store reads the key year as text), Nebenkosten of the BA (main case) and
    # of the Mietspiegel (sensitivity), the median wage on 31.12. of each survey year
    rents = ctx.store.read(NEW_CONSTRUCTION_RENTS).astype({"year": int})
    ba = {y: sum(read_nebenkosten(c.BA_KDU_XLSX[y], y).values()) for y in years}
    pages: dict[str, list[str]] = {}

    def pages_of(name: str) -> list[str]:
        if name not in pages:
            pages[name] = page_texts(getattr(c, name))
        return pages[name]

    mietspiegel = read_mietspiegel_costs(pages_of, MIETSPIEGEL_COSTS)
    # the wage of the first year stands in the yearly file of 31.12.2017, all later ones in the series
    wages = {y: read_median_wage(y, {RENT_FROM: c.BA_WAGES_2017_XLSM}, c.BA_WAGES_SERIES_XLSX) for y in years}
    table = wage_table(rents, ba, wages, WAGE_RULES, MINDESTLOHN, years, FLAT_M2)
    facts = wage_facts(table, wage_table(rents, mietspiegel, wages, WAGE_RULES, MINDESTLOHN, years, FLAT_M2),
                       RENT_TO)
    # S2: the respondents of both surveys, the Mikrozensus values of the Wohnungsmarktbericht for the ⓘ
    low = low_income_facts(ctx.store.read(SURVEY_RESPONDENTS))
    mikrozensus = read_mikrozensus_2018(page_texts(c.HOUSING_MARKET_REPORT_2019_2020_PDF))
    ctx.store.write(RENT_BURDEN_WAGE, table)
    ctx.store.write(RENT_BURDEN_GROUPS, low["main"].reset_index())
    example = ctx.store.read(SURVEY_CALC_EXAMPLES)["LIF_RENT_BURDEN_RATIO"]  # the sum of the map indicator
    ctx.store.write(RENT_BURDEN_VIEW, {"wage": wage_view(table, WAGE_TEXTS, RENT_TO, MINDESTLOHN[RENT_TO]),
                                       "low_income": bars_view(low, mikrozensus, LOW_INCOME_TEXTS, example)})
    last = table[table["year"] == RENT_TO].set_index(["person", "contract"])["share"]
    ctx.log(f"warm rent ÷ net wage {RENT_TO}, new / older contract: "
            + ", ".join(f"{p} {last[(p, 'new')]:.1f} / {last[(p, 'old')]:.1f} %" for p in PERSONS))
    lowest = low["main"].loc[BREAKDOWN_IDS[0]]
    ctx.log(f"tenants under the first income limit: {lowest['share']:.1f} % of the adult tenants (bounds "
            f"{low['bounds'][0]:.1f} to {low['bounds'][1]:.1f} %), median warm rent ÷ income {lowest['median']:.1f} %")
    grosses = {(int(r.year), r.person): float(r.gross) for r in table.itertuples()}  # the BMF rows must use them
    quantiles = read_hessen_quantiles(page_texts(c.HSL_WAGE_DISTRIBUTION_PDF))
    write_checks(ctx.store, RENT_BURDEN_CHECKS,
                 net_wage_checks(WAGE_RULES, read_bmf_reference(c.BMF_WAGE_TAX_CSV),
                                 read_est_reference(c.BMF_WAGE_TAX_CSV), grosses)
                 + wage_checks(facts, quantiles, WAGE_RULES[RENT_TO].ceiling_rv,
                               _measured(ctx.store.read(SURVEY_CITY)))
                 + low_income_checks(low))


STEP = Step("rent_burden", run,
            needs=(NEW_CONSTRUCTION_RENTS, SURVEY_RESPONDENTS, SURVEY_CITY, SURVEY_CALC_EXAMPLES),
            makes=(RENT_BURDEN_WAGE, RENT_BURDEN_GROUPS, RENT_BURDEN_VIEW, RENT_BURDEN_CHECKS))
