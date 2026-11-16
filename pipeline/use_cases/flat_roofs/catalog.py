"""Title, ⓘ, overlay texts and the worked sum of the low flat roofs. Pure module."""
from __future__ import annotations

import math

from pipeline.shared.core.calc_example import CalcExample, Row
from pipeline.shared.core.indicator import BOTH, Indicator, Source, format_de
from pipeline.use_cases.flat_roofs.model import (HEIGHT_MAX_M, HEIGHT_MIN_M, MIN_ROOF_M2, MODULE_M2, MODULE_SHARE,
                                                 TALLER_BY_M, VERY_LOW_M, WALL_GAP_M, Roof)

LOD2_AS_OF = "26.6.2026"  # delivery of the building model; the check compares it with the gemarkung table
LOD2_CREATED_YEAR = "2020"  # the year most footprints were captured in (Unsicherheit; the check compares it)
BORIS_ZONES_AS_OF = "1.1.2024"  # the zones are those of the WFS 2024 (land README)
MODULES_STEP = 100  # the module estimate of the written sum is rounded half up to this step


def _de(x: float) -> str:
    """A length or an area for a text: whole number if it is one, else one decimal."""
    return format_de(x, 0 if float(x).is_integer() else 1)


SOURCE = ("HVBG, 3D-Gebäudemodell LoD2, eigene Auswertung · BORIS Hessen, Bodenrichtwertzonen · Hessische Bauordnung "
          "§ 6 (Abstandsflächen)")
AS_OF = f"Lieferung {LOD2_AS_OF} · Zonen {BORIS_ZONES_AS_OF}"
LEGEND_NOTE = "Dachfläche in Wohn- und Mischgebieten, Gebäudemodell 2026"
CALC = (f"Summe der Flachdachflächen im Gebiet, die nach der Regel zählen. Niedrig heißt {_de(HEIGHT_MIN_M)} bis unter "
        f"{_de(HEIGHT_MAX_M)} m hoch, etwa ein bis zwei Geschosse. Ein Gebäude kommt ab {_de(MIN_ROOF_M2)} m² solcher "
        f"Dachfläche in Frage. Für die Module bleibt die Hälfte der Fläche frei, für Rand, Wege und Technik. Ein Modul "
        f"braucht etwa {_de(MODULE_M2)} m², rund 2,5 × 10 m. So breit darf ein Lkw samt Ladung sein.")
RULE = (f"Es zählen nur Dächer in Bodenrichtwertzonen für Wohn- oder Mischgebiete. Ein Dach unter {_de(VERY_LOW_M)} m "
        f"Höhe zählt nicht. Vor einer Wand, die mehr als {_de(TALLER_BY_M)} m höher ist als das Dach, bleiben "
        f"{_de(WALL_GAP_M)} m frei. So viel Abstand verlangt die Hessische Bauordnung mindestens. Umformer, "
        f"Gewächshäuser, Kirchen und andere religiöse Bauten, Krankenhäuser, Türme, Überdachungen und Verkehrsbauwerke "
        f"zählen nie.")
UNCERTAINTY = (f"Die Karte kennt Statik, Solaranlagen, Begrünung, Eigentum und Baurecht der Dächer nicht. Die Höhen "
               f"sind größtenteils auf 1 m genau. Die Grundrisse stammen meist von {LOD2_CREATED_YEAR}. Die "
               f"Bodenrichtwertzone zeigt die übliche Nutzung, nicht den Bebauungsplan. Vor hohen Wänden verlangt die "
               f"Bauordnung mehr Abstand als {_de(WALL_GAP_M)} m.")

INDICATORS: list[Indicator] = [
    Indicator("ROOF_FLAT", "Niedrige Flachdächer", "Boden", "m²", BOTH, SOURCE, AS_OF, CALC, "color:#8a5a2b", 0,
              rule=RULE, uncertainty=UNCERTAINTY, legend_note=LEGEND_NOTE, section="land"),
]

SOURCES = [Source("3D-Gebäudemodell LoD2 (HVBG), eigene Auswertung", f"Lieferung {LOD2_AS_OF}",
                  "Geobasisdaten Hessen, Nutzung ohne Einschränkung, verändert")]

# The overlay: title in the list, the two key rows, tip before the values in the tooltip and the result protocol of the ⓘ
OVERLAYS: dict[str, dict] = {
    "flat_roofs": {"title": "Niedrige Flachdächer (braun)", "key": "Niedriges Flachdach, zählt",
                   "key_not_counted": "Niedriges Flachdach, zählt nicht", "tip": "Flachdach:",
                   "source": SOURCE, "as_of": AS_OF,
                   "rule": f"Die Karte zeigt Gebäude mit mindestens {_de(MIN_ROOF_M2)} m² Flachdach in "
                           f"{_de(HEIGHT_MIN_M)} bis unter {_de(HEIGHT_MAX_M)} m Höhe. Dächer ohne Muster zählen "
                           f"nicht für die Fläche je Gebiet. Ausgeschlossene Gebäude wie Kirchen oder Krankenhäuser "
                           f"zeichnet die Karte nicht."}}

# Why a roof does not count, after „Zählt nicht:“ in its tooltip (Roof.reason)
NOT_COUNTED = {"zone": "kein Wohn- oder Mischgebiet.", "very_low": f"niedriger als {_de(VERY_LOW_M)} m."}


def _height_down(height_m: float) -> str:
    """A height rounded down to 0.1 m, so it never reads as a threshold it misses (3,17 m reads 3,1, not 3,2). The
    epsilon keeps 6.4 at 6,4 against float noise."""
    return format_de(math.floor(height_m * 10 + 1e-6) / 10, 1)


def roof_text(r: Roof, use_name: str) -> str:
    """The tooltip of a roof after the tip: area, height, function, and why it does not count or, for a counted roof,
    the strip in front of a taller wall."""
    text = f"{format_de(r.area_m2, 0)} m², {_height_down(r.height_m)} m hoch ({use_name})."
    if r.reason:
        return f"{text} Zählt nicht: {NOT_COUNTED[r.reason]}"
    if round(r.wall_m2) >= 1:
        return f"{text} Vor einer höheren Wand bleiben {format_de(r.wall_m2, 0)} m² frei."
    return text


def funnel_calc_example(f: dict[str, float]) -> CalcExample:
    """The funnel of the city as a written sum, ending in the module estimate (rounded to MODULES_STEP). A row that
    rounds to 0 goes."""
    modules = MODULES_STEP * math.floor(f["modules"] / MODULES_STEP + 0.5)
    rows = [Row("", round(f["candidates_m2"]), 0, f"m² niedrige Flachdächer ab {_de(MIN_ROOF_M2)} m²"),
            Row("−", round(f["not_housing_m2"]), 0, "m² außerhalb von Wohn- und Mischgebieten"),
            Row("−", round(f["very_low_m2"]), 0, f"m² unter {_de(VERY_LOW_M)} m hoch"),
            Row("−", round(f["wall_m2"]), 0, "m² Abstand vor höheren Wänden"),
            Row("", round(f["counted_m2"]), 0, "m² zählen", total=True),
            Row("×", MODULE_SHARE, 1, "Hälfte für Module"),
            Row("÷", round(MODULE_M2), 0, "m² je Modul"),
            Row("", modules, 0, "leichte Wohnmodule haben Platz", total=True, estimate=True)]
    return CalcExample("ganz Frankfurt", tuple(r for r in rows if r.number != 0), "Rechnung für ganz Frankfurt")
