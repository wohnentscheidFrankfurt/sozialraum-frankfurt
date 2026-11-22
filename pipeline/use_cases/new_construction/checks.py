"""Checks of the view „Neubau“ (README, Checks). Pure."""
from __future__ import annotations

import re

import pandas as pd

from pipeline.shared.core.checks import FAIL, OK, WARN, Check
from pipeline.shared.core.texts import Texts
from pipeline.use_cases.new_construction.catalog import (AVERAGE, BASE_EFFECTS, OUTFLOW_THIRD, RENT_FROM, RENT_MARGIN,
                                                         REPORT_GROWTHS, SURVEY_DATES, shown_month)


def _check(name: str, holds: bool, text: str, status: str = FAIL) -> Check:
    return Check(name, OK if holds else status, text)


def new_construction_checks(table: pd.DataFrame, f: dict, report_2024: tuple[int, int, int], fw1_confirm: int,
                            report_2024_all: tuple[int, int], report_2024_nonres: tuple[int, int], b483: dict[int, int],
                            texts: dict, phrases: dict[str, str], texts_of: Texts) -> list[Check]:
    """`report_2024*` are (year, value) of the report 2024: table 17 (year, buildings, dwellings), table 15 (all
    dwellings) and table 19 (new non-residential dwellings). `b483` holds the totals of B 483/2025 per year. The
    statements of one language: `texts` (TEXTS), `phrases` (PHRASES), `texts_of` (T, formats the numbers)."""
    t = table.set_index("year")
    n = texts_of.number
    info = texts["info"]
    span = phrases["provisional_span"]
    negative = [int(y) for y in t.index[t["conversions"] < 0]]
    all_2024, nonres_2024 = int(t.loc[2024, "all"]), int(t.loc[2024, "new_nonres"])
    gap = {y: (int(t.loc[y, "all"]), b483.get(y)) for y in (2019, 2020)}
    return [
        _check("heading fifth", 0.18 <= f["share_last"] < 0.2,
               f"„{phrases['fifth']}“: {f['last_year']} share {100 * f['share_last']:.1f} % (needs 18 % to under 20 %)"),
        _check("heading eighth", f["max_share_before"] <= 1 / 8,
               f"„{phrases['eighth']}“: highest share before {f['last_year']} is {100 * f['max_share_before']:.1f} % "
               f"({f['max_share_year']}, needs at most 12.5 %)"),
        _check("lead average", AVERAGE - 50 <= f["mean"] < AVERAGE + 50,
               f"„{phrases['lead_average']}“: mean of all "
               f"dwellings {f['first_year']}–{f['last_year']} {n(round(f['mean']), 0)} (needs "
               f"{n(AVERAGE - 50, 0)} to under {n(AVERAGE + 50, 0)})"),
        _check("conversions not negative", not negative,
               "conversions (all dwellings minus new construction) are negative in " + ", ".join(map(str, negative))
               if negative else "conversions are not negative in any year; the drawing cannot show a negative part"),
        _check("HSL report 2024", report_2024[0] == 2024 and report_2024[2] == int(t.loc[2024, "new_res"]),
               f"HSL report 2024, table 17: {report_2024}; Regionaldatenbank 2024: {int(t.loc[2024, 'new_res'])}",
               WARN),
        _check("HSL report 2024 tables 15 and 19",
               report_2024_all == (2024, all_2024) and report_2024_nonres == (2024, nonres_2024),
               f"HSL report 2024, table 15 (all dwellings) {report_2024_all} and table 19 (new non-residential) "
               f"{report_2024_nonres}; Regionaldatenbank 2024: {all_2024} and {nonres_2024}", WARN),
        _check("FW 1 of the last year", fw1_confirm == int(t.loc[f["last_year"], "fw1"]),
               f"F 158/2026 gives FW 1 {fw1_confirm}, F 9/2026 {int(t.loc[f['last_year'], 'fw1'])}", WARN),
        _check("texts of the ⓘ", span in info["rule"] and span in info["uncertainty"],
               f"rule and uncertainty name „{span}“"),
        _check("gap of 2019 and 2020", all(m is not None and a > m for a, m in gap.values()),
               "the ⓘ says the Magistrat names lower totals for 2019 and 2020 (table, B 483/2025): "
               + ", ".join(f"{y} {n(a, 0)} and {m if m is None else n(m, 0)}"
                           for y, (a, m) in gap.items())),
    ]


def _pct(share: float) -> str:
    return f"{100 * share:.2f} %"


def stock_checks(table: pd.DataFrame, f: dict, population_report: tuple[int, int], texts: dict,
                 phrases: dict[str, str]) -> list[Check]:
    """Checks of the stock of dwellings and the population in the block of rents: `table` from stock_series, `f` from
    stock_facts, `population_report` (year, population) of Frankfurt from the HSL report A I 2 of the last year. The
    statements of one language: `texts` (RENTS_TEXTS), `phrases` (PHRASES)."""
    t = table.set_index("year")
    uncertainty = texts["info"]["uncertainty"]
    report_year, report_population = population_report
    regional_population = int(t.loc[f["last_year"], "population"])
    negative = [int(y) for y in t.index[t["outflow"].fillna(0) < 0]]
    low_outflow = f["outflow_last"] is not None and f["outflow_last"] < OUTFLOW_THIRD * f["mean_outflow_other"]
    caveat = phrases["outflow_caveat"] in uncertainty
    return [
        _check("stock outflow", not negative,
               "outflow (completed minus change of the stock) is negative in " + ", ".join(map(str, negative))
               if negative else "the outflow is not negative in any year with one base on both ends", WARN),
        _check("stock outflow of the last year", not low_outflow or caveat,
               f"outflow {f['last_year']} {f['outflow_last']}, mean of the other years with one base on both ends "
               f"{f['mean_outflow_other']:.1f}; "
               + (f"below a third, so the ⓘ must name the HBO caveat of the HSL: "
                  f"{'named' if caveat else 'missing'}" if low_outflow else "not below a third, no caveat needed")),
        _check("population report of the last year",
               (report_year, report_population) == (f["last_year"], regional_population),
               f"HSL report A I 2, 31.12.{report_year}: {report_population}; Regionaldatenbank 31.12.{f['last_year']}: "
               f"{regional_population}", WARN),
    ]


def _month(month: tuple[int, int] | None) -> str:
    return "none" if month is None else f"{month[0]}-{month[1]:02d}"


def _index(value: float | None) -> str:
    return "none" if value is None else f"{value:.2f}"


def _named_in_order(text: str, parts: list[str]) -> bool:
    """Whether `text` holds the parts in this order, each as a whole number (not the end of a longer one: „17,8 %“)."""
    start = 0
    for part in parts:
        hit = re.compile(r"(?<![\d,.])" + re.escape(part)).search(text, start)
        if hit is None:
            return False
        start = hit.end()
    return True


PRICE_TOLERANCE = 0.05  # the price index of a survey year, recomputed from the VPI, may differ from the table by this


def rents_checks(table: pd.DataFrame, facts: dict, view: dict, growths: dict[int, dict], surveys: dict[int, dict],
                 prices: dict[tuple[int, int], float], texts: dict, phrases: dict[str, str],
                 texts_of: Texts) -> list[Check]:
    """Checks of the block of rents, prices and wages: `table` from rents_table, `facts` from rents_facts, `view` from
    rents_view, `growths` (percent as the reports print them, per survey year) from read_report_growths, `surveys`
    (rents and survey month per survey year) from read_rent_surveys and `prices` (VPI per (year, month)) from
    read_price_index. The statements of one language: `texts` (RENTS_TEXTS), `phrases` (PHRASES), `texts_of` (T,
    formats the numbers)."""
    t = table.set_index("year")
    n = texts_of.number
    last = int(t.index.max())
    span = f"{RENT_FROM}–{last}"
    title, lead, info = texts["title"], texts["lead"], texts["info"]

    stock = (facts["stock_growth"], facts["stock_growth_chained"])
    population = (facts["population_growth"], facts["population_growth_chained"])
    # the heading compares the rents of new contracts in Euro only, by more than the sampling error (RENT_MARGIN):
    # without inflation the gap to the chained growth of the dwellings lies within it (docs/data-rules.md, Uncertainty)
    new, new_real = facts["new_growth"], facts["new_growth_real"]
    since = phrases["since"]
    named_since = title.startswith(since + " ")
    heading = (named_since and all(d > p for d, p in zip(stock, population))
               and all(new - d > RENT_MARGIN for d in stock))

    # the ⓘ names the lowest and the highest size of a household of all years, not two years (docs/data-rules.md)
    low, high = n(facts["household_low"], 2), n(facts["household_high"], 2)
    household_range = phrases["household_range"].format(low=low, high=high)
    households = phrases["household_sentence"].format(low=low, high=high) in info["rule"]

    end = {chart["id"]: {s["id"]: s["values"][-1] for s in chart["series"]} for chart in view["charts"]}
    nominal, real = end["nominal"], end["real"]
    older = nominal["old"] < nominal["prices"] and nominal["old"] < nominal["wages"] and real["old"] < 100
    older_said = phrases["older_less"] in lead

    # the growth the report prints for a group, one decimal, against the growth of the rents read
    rates = []  # (year, base, group, printed, read)
    for g in REPORT_GROWTHS:
        for group in ("new", "old"):
            printed = growths.get(g["year"], {}).get(group)
            rents = (surveys.get(g["year"], {}).get(group), surveys.get(g["base"], {}).get(group))
            read = None if None in rents else 100 * (rents[0] / rents[1] - 1)
            rates.append((g["year"], g["base"], group, printed, read))
    rates_hold = all(p is not None and r is not None and abs(round(r, 1) - p) < 1e-9 for _, _, _, p, r in rates)

    # the survey dates read against the dates of the tooltips, then the VPI month of each survey against the table
    dates = []  # (year, month read, text shown, month shown)
    for year in sorted(set(surveys) | set(SURVEY_DATES)):
        shown = SURVEY_DATES.get(year)
        dates.append((year, surveys.get(year, {}).get("month"), shown, None if shown is None else shown_month(shown)))
    dates_hold = all(read is not None and read == month for _, read, _, month in dates)
    base_value = prices.get(surveys.get(RENT_FROM, {}).get("month"))
    vpi = []  # (year, month, VPI, index from the VPI, index of the table)
    for year in sorted(surveys):
        month = surveys[year]["month"]
        value = prices.get(month)
        index = None if value is None or base_value is None else 100 * value / base_value
        vpi.append((year, month, value, index, t["prices_index"].get(year)))
    vpi_hold = all(i is not None and g is not None and abs(i - g) <= PRICE_TOLERANCE for _, _, _, i, g in vpi)

    effects = (-facts["population_base_effect"], -facts["stock_base_effect"])
    effects_named = all(n(e, 0) in info["uncertainty"] for e in BASE_EFFECTS)

    # the ⓘ names both calculations of the growth since RENT_FROM (docs/data-rules.md, Uncertainty), in the order of
    # the text: chained, dwellings then population, then as published (the index of the last year minus 100)
    both = [100 * facts["stock_growth_chained"], 100 * facts["population_growth_chained"],
            t.loc[last, "stock_index"] - 100, t.loc[last, "population_index"] - 100]
    both_shown = [n(g, 1, "%") for g in both]
    both_named = _named_in_order(info["uncertainty"], both_shown)
    return [
        _check("rents heading", heading,
               f"„{since} … schneller als die Bevölkerung, die Mieten neuer Verträge noch schneller“: growth {span} of "
               f"the dwellings published {_pct(stock[0])}, chained {_pct(stock[1])}, of the population published "
               f"{_pct(population[0])}, chained {_pct(population[1])}; rents of new contracts {_pct(new)} in Euro (the "
               f"dwellings must grow faster than the population, and the new rents in Euro faster than the dwellings "
               f"by more than {100 * RENT_MARGIN:.0f} points, published and chained); without inflation "
               f"{_pct(new_real)}, not checked: the gap to the chained growth of the dwellings lies within the "
               f"sampling error; the title {'starts' if named_since else 'does not start'} with „{since}“"),
        _check("rents households", households,
               f"persons per household {RENT_FROM}–{last}: lowest {facts['household_low']:.4f}, highest "
               f"{facts['household_high']:.4f}; the rule of the ⓘ {'names' if households else 'does not name'} "
               f"„{household_range}“"),
        _check("rents lead older contracts", older and older_said,
               f"„Die Mieten älterer Verträge stiegen {phrases['older_less']}“: index {last} (in Euro) older "
               f"contracts {nominal['old']:.2f}, prices {nominal['prices']:.2f}, wages {nominal['wages']:.2f}; without "
               f"inflation older contracts {real['old']:.2f} (needs under 100); the lead "
               f"{'says' if older_said else 'does not say'} „{phrases['older_less']}“"),
        _check("rents growth rates of the reports", rates_hold,
               "growth against the survey before, printed in the report and read from the rents: "
               + "; ".join(f"{year} against {base}, {'new' if group == 'new' else 'older'} contracts printed "
                           f"{'none' if p is None else f'{p:.1f}'} %, read {'none' if r is None else f'{r:.2f}'} %"
                           + ("" if p is not None and r is not None and abs(round(r, 1) - p) < 1e-9 else " (differs)")
                           for year, base, group, p, r in rates)),
        _check("rents survey dates", dates_hold and vpi_hold,
               "survey month read against the date of the tooltips: "
               + "; ".join(f"{year} read {_month(read)}, shown „{shown}“ ({_month(month)})"
                           + ("" if read is not None and read == month else " (differs)")
                           for year, read, shown, month in dates)
               + f"; VPI of the survey month, as index {RENT_FROM} = 100, against the table: "
               + "; ".join(f"{year} VPI {value} ({_month(month)}) index {_index(index)}, table {_index(got)}"
                           + ("" if index is not None and got is not None and abs(index - got) <= PRICE_TOLERANCE
                              else " (differs)")
                           for year, month, value, index, got in vpi)),
        _check("rents uncertainty", effects == BASE_EFFECTS and effects_named and both_named,
               f"the ⓘ names the base effects {n(BASE_EFFECTS[0], 0)} (population) and "
               f"{n(BASE_EFFECTS[1], 0)} (dwellings): {'named' if effects_named else 'missing'}; data: "
               f"31.12.{facts['break_year']} population {n(effects[0], 0)} and dwellings "
               f"{n(effects[1], 0)} below the old base ({n(facts['population_bridge'], 0)} and "
               f"{n(facts['stock_bridge'], 0)}); the ⓘ names the growth {RENT_FROM}–{last} chained, dwellings "
               f"{both_shown[0]} and population {both_shown[1]}, then as published {both_shown[2]} and "
               f"{both_shown[3]}: {'named in this order' if both_named else 'missing or in another order'}"),
    ]
