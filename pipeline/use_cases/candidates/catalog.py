"""The candidate templates (German titles; README; texts.<lang>.yaml). Pure module."""
from __future__ import annotations

from pipeline.shared.core.texts import Texts, package_texts, per_language

T: dict[str, Texts] = package_texts(__file__)
CITY_VALUE = "city_value"  # threshold = the city value of the indicator
UPPER_END_NOTE: dict[str, str] = per_language(lambda t: t["upper_end_note"], T)
CUSTOM_NOTE: dict[str, str] = per_language(lambda t: t["custom_note"], T)


def _templates(t: Texts) -> list[dict]:
    return [
        {"id": "social_preservation", "title": t["templates.social_preservation.title"], "level": "district",
         "lead": t["templates.social_preservation.lead"], "criteria": [
            {"indicator": "HOU_RENTERS", "op": ">=", "threshold": CITY_VALUE},
            {"indicator": "SOC_MIN_INCOME", "op": ">=", "threshold": CITY_VALUE},
            {"indicator": "HOU_PRE1919", "op": ">=", "threshold": CITY_VALUE},  # pipeline/use_cases/construction_year/README.md
            {"indicator": "LAND_VALUE", "op": ">=", "threshold": CITY_VALUE},
            {"indicator": "PROT_SOCIAL", "op": "<", "threshold": 50}]},
        # ownership only per Stadtteil, the upper end of the range below the city value
        # (docs/data-rules.md, Level; docs/data-rules.md, Demands)
        {"id": "coop", "title": t["templates.coop.title"], "level": "quarter", "lead": t["templates.coop.lead"],
         "criteria": [
            {"indicator": "OWN_COOP_HIGH", "city": "OWN_COOP", "label": t["templates.coop.criteria.1.label"],
             "op": "<", "threshold": CITY_VALUE, "note": t["templates.coop.criteria.1.note"]},
            {"indicator": "HOU_RENTERS", "op": ">=", "threshold": CITY_VALUE},
            {"indicator": "LAND_PENDING_PLAN", "op": "==", "threshold": 1}]},
        # README: ABG and Nassauische Heimstätte exist only per Stadtteil
        {"id": "public_company", "title": t["templates.public_company.title"], "level": "quarter",
         "lead": t["templates.public_company.lead"],
         "criteria": [
            {"indicator": "SOC_MIN_INCOME", "op": ">=", "threshold": CITY_VALUE},
            # only what holds despite the doubt counts (docs/data-rules.md, Demands)
            {"indicator": "OWN_PUBLIC_HIGH", "city": "OWN_PUBLIC", "label": t["templates.public_company.criteria.2.label"],
             "op": "<", "threshold": CITY_VALUE, "note": t["templates.public_company.criteria.2.note"]}]},
    ]


TEMPLATES: dict[str, list[dict]] = per_language(_templates, T)
