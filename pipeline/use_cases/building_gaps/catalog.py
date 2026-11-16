"""Title, ⓘ, overlay texts, tooltip and the worked sum of the building gaps (Baulücken). Pure module."""
from __future__ import annotations

import math

from pipeline.shared.core.calc_example import CalcExample, Row
from pipeline.shared.core.indicator import BOTH, Indicator, Source, format_de
from pipeline.use_cases.building_gaps.model import (BUILDING_MAX, BUILT_MAX_M2, BUILT_MAX_SHARE, FREE_FRONT_M,
                                                    HALF_WIDTH_M, HOUSING_SHARE_MIN, MIN_AREA_M2, MIN_FRONT_M,
                                                    WALL_MIN_M, Candidate, suitability)

ALKIS_AS_OF = "4.11.2026"  # delivery of the ALKIS extract; the check compares it with the portion date of the NAS
DOM_YEAR = "2023"  # flight of the height models DOM1 and DGM1
DOP_AS_OF = "19.8.2025"  # flight of the orthophoto of most candidates; the check compares it with the cover extract
BORIS_ZONES_AS_OF = "1.1.2024"  # the zones are those of the WFS 2024 (land README)
COLOUR = "#c51b7d"  # magenta of the layer; the overlay in web/js uses the same tone


def _pct(share: float) -> str:
    return f"{format_de(share * 100, 0)} %"


SOURCE = ("HVBG, ALKIS, Höhenmodelle DOM1 und DGM1, Luftbild DOP20, eigene Auswertung und Prüfung von Hand · "
          "BORIS Hessen, Bodenrichtwertzonen")
AS_OF = f"ALKIS {ALKIS_AS_OF} · Höhenmodell {DOM_YEAR} · Luftbild {DOP_AS_OF} · Zonen {BORIS_ZONES_AS_OF}"
LEGEND_NOTE = f"Fläche geprüfter Baulücken in Wohn- und Mischgebieten, Kataster {ALKIS_AS_OF[-4:]}"
CALC = ("Die Karte addiert die Flächen aller Flurstücke im Gebiet, die nach der Prüfung als Baulücke zählen. Eine "
        "Baulücke zählt für das Gebiet, in dem ihr Mittelpunkt liegt.")
RULE = (f"Eine Baulücke ist ein Flurstück fast ohne Hauptgebäude (höchstens {_pct(BUILT_MAX_SHARE)} der Fläche oder "
        f"{format_de(BUILT_MAX_M2, 0)} m²). Es ist mindestens {format_de(MIN_AREA_M2, 0)} m² groß und "
        f"{format_de(2 * HALF_WIDTH_M, 0)} m breit. Mindestens {_pct(HOUSING_SHARE_MIN)} seiner Fläche dienen dem "
        f"Wohnen oder gemischter Nutzung. Es liegt mit mindestens {format_de(MIN_FRONT_M, 0)} m an einer Straße, "
        f"einem Weg oder einem Platz. Es grenzt auf mindestens {format_de(WALL_MIN_M, 0)} m an die Wand eines "
        f"Nachbarhauses, oder seine Front ist mindestens {format_de(FREE_FRONT_M, 0)} m lang. Es liegt in einer "
        f"Bodenrichtwertzone für Wohn- oder Mischgebiete. Höchstens die Hälfte ist grün, höchstens "
        f"{_pct(BUILDING_MAX)} sind bebaut, und mindestens die Hälfte ist weder bebaut noch grün. Jedes solche "
        f"Flurstück wird von Hand im Luftbild oder vor Ort geprüft. Es zählen nur Parkplätze, Höfe, Lagerplätze und "
        f"Brachen. "
        f"Wiesen, Gärten, Schulhöfe, Spielplätze, öffentliche Plätze und Neubauten zählen nicht.")
UNCERTAINTY = (f"Das Kataster hat den Stand vom {ALKIS_AS_OF}, das Höhenmodell ist von {DOM_YEAR} und das Luftbild vom "
               f"{DOP_AS_OF}. Neubauten seit dem Luftbild fehlen. Die Karte kennt keinen Bebauungsplan und keine "
               f"Eigentümer*innen. Die Prüfung geschieht nach Augenschein. Manche Flurstücke müssen vor Ort geprüft "
               f"werden.")

INDICATORS: list[Indicator] = [
    Indicator("GAP_AREA", "Baulücken", "Boden", "m²", BOTH, SOURCE, AS_OF, CALC, f"color:{COLOUR}", 0,
              rule=RULE, uncertainty=UNCERTAINTY, legend_note=LEGEND_NOTE, section="land"),
]

SOURCES = [Source("ALKIS, DOM1, DGM1 und DOP20 (HVBG), eigene Auswertung", f"ALKIS {ALKIS_AS_OF}, Luftbild {DOP_AS_OF}",
                  "Geobasisdaten Hessen, Nutzung ohne Einschränkung, verändert"),
           # the examples of SUITABILITY_TEXT (reference/building_gaps_examples.csv); the Gemeinwohlbau with its page,
           # where its presentation is public (user, 15.11.2026)
           Source("Beispiele der Baulücken: Deutsches Architektenblatt 05/2025, Website gpwirth architekten, "
                  "Pressemitteilungen der ABG", "2015–2025",
                  "Veröffentlichungen des Architektenblatts, des Architekturbüros und der ABG"),
           Source("Beispiel „Haus für alle“: Präsentation der Gemeinwohlbau, Berlin", "6/2026",
                  "Veröffentlichung der Gemeinwohlbau", url="https://gemeinwohlbau.de/idee")]

# The overlay: title in the list, one key row, tip before the text in the tooltip and the result protocol of the ⓘ
OVERLAYS: dict[str, dict] = {
    "building_gaps": {"title": "Baulücken (magenta)", "key": "Baulücke", "tip": "Baulücke:", "source": SOURCE,
                      "as_of": AS_OF,
                      "rule": "Die Karte zeigt Flurstücke, die die Regeln für eine Baulücke erfüllen und von Hand "
                              "geprüft werden. Sie zeigt nur Flurstücke, die zählen oder vor Ort geprüft werden "
                              "müssen. Flurstücke, die nach der Prüfung nicht zählen oder noch nicht geprüft sind, "
                              "fehlen. Der Tooltip sagt, ob "
                              "die Baulücke zählt oder vor Ort geprüft werden muss."}}

# The kind of sealed or open land of a counted gap (model.COUNT_REASONS)
COUNT_TEXT = {"parking": "Parkplatz", "yard": "Hof", "storage": "Lagerplatz", "brownfield": "Brache"}
KIND_TEXT = {"row": "zwischen Nachbarhäusern", "free": "freistehend"}
# What a counted gap could carry, keyed like model.SUITABILITY; reference/building_gaps_examples.csv holds the sources
SUITABILITY_TEXT = {
    "coop": "Platz zum Beispiel für ein Haus einer Genossenschaft. Im Nordend wohnen 25 Menschen in 9 Wohnungen auf "
            "312 m², wo früher ein Parkplatz war.",
    "house_for_all": "Platz zum Beispiel für ein Haus für alle. Die Gemeinwohlbau plant in Berlin 19 Mieter*innen auf "
                     "365 m² und 15 m Breite.",
    "student": "Platz zum Beispiel für ein Studierendenwohnheim. In Nürnberg stehen seit 2015 177 Apartments auf "
               "1.270 m² in einer Baulücke.",
    "multi_family": "Platz zum Beispiel für ein Mehrfamilienhaus. Die ABG baut im Gallus 42 geförderte Wohnungen auf "
                    "rund 2.000 m².",
    "complex": "Platz zum Beispiel für eine Wohnanlage. Die ABG hat 2025 in Griesheim 67 Wohnungen auf 5.400 m² "
               "fertiggestellt.",
}
SITE_TEXT = "Muss vor Ort geprüft werden."


def german_date(iso: str) -> str:
    """'2025-08-19' gives '19.8.2025'; anything else gives ""."""
    parts = iso[:10].split("-")
    if len(parts) != 3 or not all(p.isdigit() for p in parts):
        return ""
    return f"{int(parts[2])}.{int(parts[1])}.{parts[0]}"


def gap_text(c: Candidate, kz: str) -> str:
    """The tooltip of a drawn gap after the tip: parcel, area, front and kind, then the verdict. kz is the parcel as
    text (sources.kz_text). Area and front are rounded down, so a gap never reads larger than it is. A counted gap
    starts its verdict with „Zählt:“; a gap to check on site gets SITE_TEXT. A gap that is not drawn (judged not, not
    judged yet, or dropped by a filter) has no tooltip."""
    if not c.drawn:
        raise ValueError(f"{c.gap.gml_id} is not drawn ({c.reason}): it has no tooltip")
    g = c.gap
    text = (f"{kz}. {format_de(math.floor(g.area_m2), 0)} m², {format_de(math.floor(g.front_m), 0)} m an der Straße, "
            f"{KIND_TEXT[g.kind]}.")
    fits = SUITABILITY_TEXT[suitability(g.area_m2)]
    v = c.verdict or {}
    if c.counts:
        what = COUNT_TEXT.get(v.get("reason", ""), v.get("reason", ""))
        if v.get("by") == "site":
            return f"{text} Zählt: {what}, geprüft vor Ort am {german_date(v.get('checked', ''))}. {fits}"
        flight = german_date((c.cover or {}).get("flight", "")) or DOP_AS_OF
        return f"{text} Zählt: {what}, geprüft im Luftbild vom {flight}. {fits}"
    return f"{text} {SITE_TEXT} {fits}"


def funnel_calc_example(f: dict[str, float]) -> CalcExample:
    """The funnel of the city as a written sum, in parcels, ending in the counted gaps and their area. A step that drops
    no parcel goes; the two totals always stand."""
    steps = [("main_building", f"mit Hauptgebäude über {_pct(BUILT_MAX_SHARE)} oder {format_de(BUILT_MAX_M2, 0)} m²"),
             ("small", f"unter {format_de(MIN_AREA_M2, 0)} m²"),
             ("use", "nicht überwiegend Wohnen oder gemischt"),
             ("narrow", f"schmaler als {format_de(2 * HALF_WIDTH_M, 0)} m"),
             ("front", f"unter {format_de(MIN_FRONT_M, 0)} m an der Straße"),
             ("no_wall", f"ohne Nachbarwand und unter {format_de(FREE_FRONT_M, 0)} m an der Straße"),
             ("zone", "außerhalb von Wohn- und Mischgebieten"),
             ("no_cover", "ohne Luftbild"),
             ("green", "mehr als zur Hälfte grün"),
             ("built", "laut Höhenmodell bebaut"),
             ("not_open", "nicht überwiegend offen"),
             ("not", "zählen nach Prüfung nicht"),
             ("site", "müssen vor Ort geprüft werden"),
             ("no_verdict", "noch nicht geprüft")]
    rows = [Row("", round(f["parcels"]), 0, "Flurstücke")]
    rows += [Row("−", round(f[key]), 0, text) for key, text in steps if round(f[key]) != 0]
    rows += [Row("", round(f["counted"]), 0, "Baulücken zählen", total=True),
             Row("", round(f["counted_m2"]), 0, "m² zählen", total=True)]
    return CalcExample("ganz Frankfurt", tuple(rows), "Rechnung für ganz Frankfurt")
