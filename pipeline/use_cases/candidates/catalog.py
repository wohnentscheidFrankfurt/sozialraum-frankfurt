"""The candidate templates (German titles; README). Pure module."""
from __future__ import annotations

CITY_VALUE = "city_value"  # threshold = the city value of the indicator
UPPER_END_NOTE = "Der Stadtteil zählt nur, wenn auch das obere Ende der Schätzung unter der Schwelle liegt."
# the own query works on districts; these groups exist only per Stadtteil (tests pin it against the catalog)
CUSTOM_NOTE = ("Die eigene Abfrage rechnet mit Bezirken. Eigentum, Sozialwohnungen und Wahl fehlen, weil es sie nur "
               "je Stadtteil gibt.")
TEMPLATES = [
    {"id": "social_preservation", "title": "Milieuschutz-Kandidat", "level": "district",
     "lead": "Gesucht sind Bezirke mit überdurchschnittlich vielen Mietwohnungen, viel Altbau, hohem Bodenwert und "
             "viel Mindestsicherung. Bezirke mit viel Milieuschutz fallen heraus. Ein Treffer ist ein Anlass für eine "
             "Prüfung, kein Befund.", "criteria": [
        {"indicator": "HOU_RENTERS", "op": ">=", "threshold": CITY_VALUE},
        {"indicator": "SOC_MIN_INCOME", "op": ">=", "threshold": CITY_VALUE},
        {"indicator": "HOU_PRE1919", "op": ">=", "threshold": CITY_VALUE},  # pipeline/use_cases/construction_year/README.md
        {"indicator": "LAND_VALUE", "op": ">=", "threshold": CITY_VALUE},
        {"indicator": "PROT_SOCIAL", "op": "<", "threshold": 50}]},
    # ownership only per Stadtteil, the upper end of the range below the city value
    # (docs/data-rules.md, Level; docs/data-rules.md, Demands)
    {"id": "coop", "title": "Genossenschafts-Lücke", "level": "quarter",
     "lead": "Gesucht sind Stadtteile mit wenig Genossenschaften, in denen gerade ein Bebauungsplan entsteht.",
     "criteria": [
        {"indicator": "OWN_COOP_HIGH", "city": "OWN_COOP", "label": "Genossenschaften (Schätzung plus Unsicherheit)",
         "op": "<", "threshold": CITY_VALUE,
         "note": UPPER_END_NOTE},
        {"indicator": "HOU_RENTERS", "op": ">=", "threshold": CITY_VALUE},
        {"indicator": "LAND_PENDING_PLAN", "op": "==", "threshold": 1}]},
    # README: ABG and Nassauische Heimstätte exist only per Stadtteil
    {"id": "public_company", "title": "Lücke bei öffentlichen Wohnungsbaugesellschaften", "level": "quarter",
     "lead": "Gesucht sind Stadtteile mit viel Mindestsicherung, in denen ABG und Nassauische Heimstätte wenige "
             "Wohnungen haben.",
     "criteria": [
        {"indicator": "SOC_MIN_INCOME", "op": ">=", "threshold": CITY_VALUE},
        # only what holds despite the doubt counts (docs/data-rules.md, Demands)
        {"indicator": "OWN_PUBLIC_HIGH", "city": "OWN_PUBLIC",
         "label": "ABG und Nassauische Heimstätte (Schätzung plus Unsicherheit)", "op": "<", "threshold": CITY_VALUE,
         "note": UPPER_END_NOTE}]},
]
