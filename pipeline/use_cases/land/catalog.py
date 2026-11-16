"""Titles and ⓘ of land values and pending plans, and the ⓘ of their overlays. Pure module."""
from __future__ import annotations

from pipeline.shared.core.indicator import BOTH, Indicator, Source

BORIS_AS_OF = "1.1.2026"
SOURCES = [Source("Bodenrichtwerte (BORIS Hessen)", BORIS_AS_OF, "dl-de/zero-2-0, Gutachterausschüsse")]
PLANS_SOURCE = "planAS, Bebauungspläne im Verfahren"
# BORIS use codes of the overlay, spelled out for the tooltip (a code we do not know stays as it is)
USE_NAMES = {"W": "Wohngebiet", "M": "Mischgebiet"}
# BORIS building types (ergaenzung), spelled out as the WMS of 2026 does
BUILDING_NAMES = {"EFH": "Ein- und Zweifamilienhäuser", "MFH": "Mehrfamilienhäuser", "BH": "Bürohäuser",
                  "WGH": "Wohn- und Geschäftshäuser", "BGH": "Büro- und Geschäftshäuser"}
# the zones of the WFS 2024 with the values of 2026 (land README, Formula)
ZONES_2024 = "Die Grenzen der Zonen stammen von 2024. Zonen, deren Nummer 2026 nicht mehr gilt, fehlen."
BORIS_RULE = ("Es zählen nur Wohn- und Mischgebiete mit baureifem Land. Felder außerhalb dieser Zonen zählen nicht. "
              + ZONES_2024)

INDICATORS: list[Indicator] = [
    Indicator("LAND_VALUE", "Bodenrichtwert", "Boden", "€/m²", BOTH, "BORIS Hessen, Bodenrichtwerte", BORIS_AS_OF,
              "Median der 100-m-Felder im Gebiet, gewichtet nach Einwohner*innen. Jedes Feld hat den Wert der Zone an seinem "
              "Mittelpunkt.",
              "orange", 0, rule=BORIS_RULE,
              legend_note=f"Median der Bodenrichtwerte in Wohn- und Mischgebieten, {BORIS_AS_OF}", section="land"),
    Indicator("LAND_PENDING_PLAN", "B-Plan im Verfahren", "Planung", "", BOTH, PLANS_SOURCE,
              "Abruf {fetch_date}", "Ja, wenn ein Plan mindestens 1 ha des Gebiets überdeckt", layer=False,
              type="yes_no", rule="Es zählen alle Pläne, auch für Gewerbe.", section="planning"),
]


def use_name(code: str, building: str = "") -> str:
    """„Mischgebiet, Mehrfamilienhäuser“: the area, then the building type where the zone has one."""
    return ", ".join(x for x in (USE_NAMES.get(code, code), BUILDING_NAMES.get(building, building)) if x)


# The two overlays: title in the list, tip before the values in the tooltip, and the result protocol of the ⓘ: Quelle,
# Stand, Regel (docs/texts.md, ⓘ protocol)
OVERLAYS: dict[str, dict] = {
    "pending_plans": {"title": "B-Pläne im Verfahren (lila)", "key": "B-Plan im Verfahren", "tip": "B-Plan im Verfahren:",
                      "source": PLANS_SOURCE, "as_of": "Abruf {fetch_date}",
                      "rule": "Die Karte zeigt alle Pläne im Verfahren, auch für Gewerbe."},
    "land_value": {"title": f"Bodenrichtwertzonen {BORIS_AS_OF[-4:]}", "key": "Bodenrichtwertzonen", "tip": f"Bodenrichtwert {BORIS_AS_OF}:",
                   "source": "BORIS Hessen, Bodenrichtwerte", "as_of": BORIS_AS_OF,
                   "rule": "Die Zonen zeigen den Bodenrichtwert in €/m². Es zählen nur Wohn- und Mischgebiete "
                           "mit baureifem Land. " + ZONES_2024}}
