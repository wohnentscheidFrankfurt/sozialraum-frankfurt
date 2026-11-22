"""Checks of the view „Miete“ (README, Checks). Pure."""
from __future__ import annotations

from pipeline.shared.core.checks import FAIL, OK, Check
from pipeline.shared.core.texts import Texts
from pipeline.use_cases.rent_burden.catalog import (ABOUT_HALF, ABOUT_SHARE, ALMOST_QUARTER, CEILING_ABOVE,
                                                    FACTOR_RANGE, MEASURED, PERSONS, SENSITIVITY_POINTS)
from pipeline.use_cases.rent_burden.model import WageRules, income_tax, soli_of, tariff
from pipeline.use_cases.survey.model import BREAKDOWN_IDS, round_half_up

TOLERANCE = 0.01  # € per month: the own calculation matches the BMF to the cent
EST_TOLERANCE = 0.005  # € per year: whole euros of the tariff, Soli rounded to the cent
EST_YEAR = 2017  # the Lohnsteuerrechner of the BMF starts with 2021; the Einkommensteuerrechner checks 2017


def _check(name: str, holds: bool, text: str) -> Check:
    return Check(name, OK if holds else FAIL, text)


def net_wage_checks(rules: dict[int, WageRules], reference: dict[tuple[int, str], tuple[float, float, float]],
                    est_reference: dict[int, tuple[float, float]],
                    grosses: dict[tuple[int, str], float]) -> list[Check]:
    """The own wage tax against the Lohnsteuerrechner of the BMF (`reference`: (year, person) -> (gross wage,
    Lohnsteuer, Soli) per month) and the tariff of 2017 against the Einkommensteuerrechner (`est_reference`: taxable
    income -> (Einkommensteuer, Soli) per year). Every year of `rules` but EST_YEAR needs a row for each of PERSONS,
    and the gross of each row must be the gross the model uses (`grosses`: (year, person) -> € per month), to the
    cent."""
    expected = {(year, person) for year in rules if year != EST_YEAR for person in PERSONS}
    missing = sorted(expected - set(reference))
    wrong = []  # rows whose year has no rules or whose gross is not the gross of the model
    for (year, person), (wage, _, _) in sorted(reference.items()):
        if year not in rules:
            wrong.append(f"{year} {person}: no rules")
        elif (year, person) not in grosses or round(grosses[(year, person)], 2) != round(wage, 2):
            own = grosses.get((year, person))
            wrong.append(f"{year} {person}: gross {wage:.2f} against the model "
                         f"{'none' if own is None else f'{own:.2f}'}")
    worst, worst_text = 0.0, "no reference rows"
    for (year, person), (wage, lohnsteuer, soli) in sorted(reference.items()):
        if year not in rules:
            continue
        own_lohnsteuer, own_soli = income_tax(wage, rules[year])
        diff = max(abs(own_lohnsteuer - lohnsteuer), abs(own_soli - soli))
        if diff >= worst:
            worst = diff
            worst_text = (f"{year} {person}, gross {wage:.2f}: Lohnsteuer {own_lohnsteuer:.2f} against "
                          f"{lohnsteuer:.2f}, Soli {own_soli:.2f} against {soli:.2f}")
    bmf_ok = bool(reference) and not missing and not wrong and worst <= TOLERANCE + 1e-9
    notes = ([f"no row for {', '.join(f'{y} {p}' for y, p in missing)}"] if missing else []) + wrong
    gaps = "".join(f"; {note}" for note in notes)
    bmf = Check("net wage against BMF", OK if bmf_ok else FAIL,
                f"{len(reference)} rows of the Lohnsteuerrechner; largest difference {worst:.2f} € per month "
                f"({worst_text}); needs at most {TOLERANCE:.2f} €, a row per year and person, the gross of the "
                f"model{gaps}")
    r = rules[EST_YEAR]
    worst_est, est_text = 0.0, "no reference rows"
    for zve, (est, soli) in sorted(est_reference.items()):
        own = tariff(zve, r.tariff)
        own_soli = round(soli_of(own, r), 2)
        diff = max(abs(own - est), abs(own_soli - soli))
        if diff >= worst_est:
            worst_est = diff
            est_text = (f"taxable {zve}: Einkommensteuer {own:.2f} against {est:.2f}, Soli {own_soli:.2f} against "
                        f"{soli:.2f}")
    tariff_ok = bool(est_reference) and worst_est < EST_TOLERANCE
    tariff_check = Check(f"net wage tariff {EST_YEAR}", OK if tariff_ok else FAIL,
                         f"{len(est_reference)} rows of the Einkommensteuerrechner; largest difference "
                         f"{worst_est:.2f} € per year ({est_text}); needs under {EST_TOLERANCE} €")
    return [bmf, tariff_check]


def wage_checks(facts: dict, quantiles: dict[int, int], ceiling: float, measured: float, phrases: dict[str, str],
                t: Texts) -> list[Check]:
    """Every statement of title and ⓘ of S1 (catalog WAGE_TEXTS) against `wage_facts`; the lead takes its euros
    from the table. `quantiles`: P88 and P89 of the monthly gross wage of full-time employees in Hessen, `ceiling`:
    the pension ceiling of the last year, `measured`: the published city value of LIF_RENT_BURDEN_RATIO. `phrases`:
    PHRASES of the source language (the messages quote the statements; the checks compare numbers, which every
    language shares), `t`: its texts."""
    factor_low, factor_high = facts["factor"]
    sensitivity_low, sensitivity_high = facts["sensitivity"]
    sensitivity_rounded = tuple(int(round_half_up(v, 1)) for v in facts["sensitivity"])
    gaps = {person: high for person, (_, high) in facts["sensitivity_persons"].items()}
    largest = max(gaps, key=gaps.get)
    p88, p89 = quantiles[88], quantiles[89]
    above_low, above_high = 100 - 89, 100 - 88
    return [
        _check("rent wage heading", FACTOR_RANGE[0] <= factor_low and factor_high <= FACTOR_RANGE[1],
               f"„{phrases['factor']}“: the Mindestlohn share ÷ the high wage share is {factor_low:.2f} to {factor_high:.2f} "
               f"in {facts['year']}, both contracts (needs {FACTOR_RANGE[0]} to {FACTOR_RANGE[1]})"),
        _check("rent wage sensitivity",
               sensitivity_rounded == SENSITIVITY_POINTS and largest == "mindestlohn",
               f"with the Nebenkosten of the Mietspiegel the share is {sensitivity_low:.2f} to "
               f"{sensitivity_high:.2f} points lower, rounded {sensitivity_rounded[0]} to {sensitivity_rounded[1]} "
               f"(needs {SENSITIVITY_POINTS[0]} to {SENSITIVITY_POINTS[1]}); the largest gap is at {largest} "
               f"(needs mindestlohn)"),
        _check("rent wage ceiling",
               p88 < ceiling < p89 and above_low <= CEILING_ABOVE < above_high,
               f"„{phrases['ceiling_above']}“ earn more: the pension ceiling {t.number(ceiling, 0)} € lies between P88 "
               f"{p88} and P89 {p89} (needs P88 < ceiling < P89), so {above_low} to under {above_high} % earn more "
               f"(needs {CEILING_ABOVE} within)"),
        _check("rent wage measured", measured == MEASURED,
               f"„{phrases['measured']}“: the published city value of LIF_RENT_BURDEN_RATIO is {measured:g} "
               f"(needs {MEASURED})"),
    ]


def low_income_checks(facts: dict, phrases: dict[str, str]) -> list[Check]:
    """Every statement of title, lead and ⓘ of S2 (catalog LOW_INCOME_TEXTS) against `low_income_facts`. `phrases`:
    PHRASES of the source language (the messages quote them)."""
    main = facts["main"]
    medians = {f"{kind} {key}": value for kind, by in facts["medians"].items() for key, value in by.items()}
    farthest = max(medians, key=lambda k: abs(medians[k] - 50))
    highest = float(main.loc[BREAKDOWN_IDS[-1], "median"])
    share = float(main.loc[BREAKDOWN_IDS[0], "share"])
    sure, at_most = facts["bounds"]
    shares = [v for by in facts["shares"].values() for v in by.values()]
    shown = int(round_half_up(share, 1))
    spread = [int(round_half_up(v, 1)) for v in shares]
    return [
        _check("low income heading", all(abs(v - 50) <= ABOUT_HALF for v in medians.values()),
               f"„{phrases['about_half']}“: the median of the lowest group is {min(medians.values()):.1f} to "
               f"{max(medians.values()):.1f} % over all positions of the income (farthest: {farthest}); needs "
               f"50 ± {ABOUT_HALF} points"),
        _check("low income lead", ALMOST_QUARTER[0] <= highest < ALMOST_QUARTER[1],
               f"„{phrases['almost_quarter']}“: the median of the highest group is {highest:.1f} % (needs "
               f"{ALMOST_QUARTER[0]} to under {ALMOST_QUARTER[1]} %)"),
        _check("low income share",
               sure <= share <= at_most and all(abs(v - shown) <= ABOUT_SHARE for v in spread),
               f"the share of the lowest group in the lead is {share:.1f} % of the adult tenants, shown {shown} % "
               f"(needs {sure:.1f} to {at_most:.1f} %, the bounds of the class edges); over all positions of the "
               f"income {min(shares):.1f} to {max(shares):.1f} %, rounded {min(spread)} to {max(spread)} (needs "
               f"{shown} ± {ABOUT_SHARE})"),
    ]
