"""Checks of the social housing figures against the annual report, the reference and the Monitoring. Pure module."""
from __future__ import annotations

import re

from pipeline.shared.core.checks import FAIL, OK, WARN, Check, thousands
from pipeline.use_cases.social_housing.catalog import SH_AS_OF, SH_CONTRACT_ONLY, SH_HIGHER_INCOME, SH_OUTSIDE_STOCK

# page 5 of the report: "… Reservoir an vertraglich gesicherten „zukünftig“ zum Erwerb von Belegungsrechten (Modell 2)
# vorgesehenen Wohnungen: 2.294 Wohnungen"; the line breaks of the PDF text are free
CONTRACT_ONLY_SENTENCE = re.compile(r"Reservoir\s+an\s+vertraglich\s+gesicherten.{0,200}?Wohnungen:\s*(\d{1,3}(?:\.\d{3})*)\s+Wohnungen",
                                    re.DOTALL)


def check_social_housing(info: dict) -> Check:
    name = "Social housing: rows against total row"
    stock, expected = info["SH_COUNT"] + info["outside_stock"][0], info["total_stock"][0]
    if stock != expected:
        return Check(name, FAIL, f"quarters + outside {thousands(stock)}, total row {thousands(expected)}")
    return Check(name, OK, f"{thousands(info['SH_COUNT'])} in Frankfurt + {thousands(info['outside_stock'][0])} "
                           f"outside = {thousands(stock)}")


def check_social_housing_totals(info: dict, reference: dict[str, float]) -> list[Check]:
    """Totals of the annual report and of the city's dwelling count against reference/check_reference.csv. A new
    report or a new count fails here until the reference is checked by hand."""
    pairs = (("Social housing: total of table 1.2 against the reference", info["total_stock"][0], "sh_report_stock"),
             ("Social housing: dwellings of the city (base of the share) against the reference", info["dwellings_total"],
              "sh_dwellings_city"))
    return [Check(name, OK if value == reference[key] else FAIL, f"{thousands(value)}, reference {thousands(int(reference[key]))}")
            for name, value, key in pairs]


def contract_only_in_report(report_text: str) -> int | None:
    """The dwellings secured by contract that the report names apart from the subsidised ones; None if the sentence
    is missing."""
    m = CONTRACT_ONLY_SENTENCE.search(report_text)
    return int(m.group(1).replace(".", "")) if m else None


def check_social_housing_protocol(info: dict) -> Check:
    """The numbers in the Regel lines of the social housing ⓘ against the report (info["report_text"]: its pages)."""
    pairs = {"outside Frankfurt, stock": (SH_OUTSIDE_STOCK, info["outside_stock"][0]),
             "higher incomes": (SH_HIGHER_INCOME, info["total_stock"][2]),
             "secured by contract only": (SH_CONTRACT_ONLY, contract_only_in_report(info["report_text"]))}
    wrong = [f"{k}: text {a}, report {b if b is not None else 'sentence not found'}" for k, (a, b) in pairs.items() if a != b]
    return Check("Social housing: numbers in the ⓘ against the report", FAIL if wrong else OK,
                 "; ".join(wrong) or ", ".join(f"{k} {a}" for k, (a, _) in pairs.items()))


def check_social_housing_monitoring(share: float, monitoring_share: float, limit: float = 1.5) -> Check:
    status = OK if abs(share - monitoring_share) <= limit else WARN
    return Check("Social housing: city share against Monitoring 2022", status,
                 f"{SH_AS_OF[-4:]} {share:.2f} %, Monitoring 2022 {monitoring_share:.2f} %, allowed ± {limit} points")

