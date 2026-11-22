import re

from shapely.geometry import box

from pipeline.shared.core.indicator import BOTH
from pipeline.use_cases.flat_roofs import model
from pipeline.use_cases.flat_roofs.catalog import (BORIS_ZONES_AS_OF, BORIS_ZONES_DATE, INDICATORS as BY_LANGUAGE,
                                                   LOD2_AS_OF, LOD2_CREATED_YEAR, LOD2_DATE,
                                                   NOT_COUNTED as NOT_COUNTED_BY_LANGUAGE,
                                                   OVERLAYS as OVERLAYS_BY_LANGUAGE, SOURCES as SOURCES_BY_LANGUAGE, T,
                                                   funnel_calc_example, roof_text)
from pipeline.use_cases.flat_roofs.model import Roof

INDICATORS, OVERLAYS, SOURCES = BY_LANGUAGE["de"], OVERLAYS_BY_LANGUAGE["de"], SOURCES_BY_LANGUAGE["de"]
NOT_COUNTED, TEXTS = NOT_COUNTED_BY_LANGUAGE["de"], T["de"]
BANNED = ("Rücktest", "Lücke", "Geheimhaltung", "Maß:", "Rechenweg", "Zelle", "Spanne", "Abgleich", "NH")
UNGENDERED = re.compile(r"\b\w*(?:eigentümer|einwohner|bewohner|wähler|mieter|bauherr)(?:e?n|s)?\b(?!\*)", re.I)
FUNNEL = {"candidates_m2": 2331545.8, "not_housing_m2": 1420178.2, "very_low_m2": 91616.2, "wall_m2": 86417.7,
          "counted_m2": 733333.7, "modules": 14666.7}


def roof(**kw) -> Roof:
    args = dict(building="a", use="31001_2000", area_m2=1250.4, height_m=6.44, wall_m2=0.0, very_low=False,
                housing=True, geom=box(0, 0, 1, 1), x=0.5, y=0.5)
    return Roof(**{**args, **kw})


def map_texts() -> list[str]:
    (k,) = INDICATORS
    return [k.title, k.source, k.as_of, k.calc, k.rule, k.uncertainty, k.legend_note, *OVERLAYS["flat_roofs"].values(),
            *(s.title for s in SOURCES), *NOT_COUNTED.values()]


def test_the_indicator():
    """Tests check rules and numbers, not wording (tests/test_text_copies.py)."""
    (k,) = INDICATORS
    assert (k.id, k.group, k.unit, k.levels, k.decimals, k.section) == ("ROOF_FLAT", "Boden", "m²", BOTH, 0, "land")
    assert k.layer and k.criterion and not k.estimate and k.ramp != "orange"
    assert (k.source, k.legend_note) == (TEXTS["ROOF_FLAT.source"], TEXTS["ROOF_FLAT.legend_note"])
    assert TEXTS.date(LOD2_DATE) == LOD2_AS_OF and TEXTS.date(BORIS_ZONES_DATE) == BORIS_ZONES_AS_OF
    assert (LOD2_AS_OF, LOD2_CREATED_YEAR, BORIS_ZONES_AS_OF) == ("26.6.2026", "2020", "1.1.2024")
    delivery, zones = k.as_of.split(" · ")  # Stand names the dates the numbers describe, one per line
    assert delivery.endswith(LOD2_AS_OF) and zones.endswith(BORIS_ZONES_AS_OF)
    assert LOD2_CREATED_YEAR not in k.as_of and LOD2_CREATED_YEAR in k.uncertainty  # the footprints: Unsicherheit
    assert "2026" in k.legend_note


def test_the_source_names_the_building_code():
    (k,) = INDICATORS
    lod2, zones, code = k.source.split(" · ")
    assert "LoD2" in lod2 and "BORIS" in zones and "§ 6" in code


def test_thresholds_in_the_texts_follow_the_model_constants():
    (k,) = INDICATORS
    for text in ("200 m²", "2,5 bis", "8 m", "25 m²"):
        assert text in k.calc, text
    for text in ("3,2 m", "mehr als 3 m", "2,5 m"):
        assert text in k.rule, text
    assert "2,5 m" in k.uncertainty
    for text in ("200 m²", "2,5 bis", "8 m"):
        assert text in OVERLAYS["flat_roofs"]["rule"], text
    assert (model.MIN_ROOF_M2, model.HEIGHT_MIN_M, model.HEIGHT_MAX_M, model.TALLER_BY_M, model.VERY_LOW_M,
            model.WALL_GAP_M, model.MODULE_M2) == (200.0, 2.5, 8.0, 3.0, 3.2, 2.5, 25.0)


def test_no_map_text_names_a_neighbour():
    """The wall strip replaced the taller neighbour: no text speaks of „Nachbar“ any more."""
    texts = map_texts() + [roof_text(roof(**kw), TEXTS) for kw in (
        {}, {"housing": False}, {"very_low": True}, {"wall_m2": 180.0}, {"very_low": True, "wall_m2": 180.0})]
    assert not [t for t in texts if "Nachbar" in t]


def test_texts_are_full_sentences_without_working_terms():
    (k,) = INDICATORS
    texts = [k.calc, k.rule, k.uncertainty, k.legend_note, *(v for v in OVERLAYS["flat_roofs"].values())]
    for t in texts:
        assert not [w for w in BANNED if w in t], t
        assert not UNGENDERED.findall(t), t
    for t in (k.calc, k.rule, k.uncertainty, OVERLAYS["flat_roofs"]["rule"]):
        assert t.endswith(".") and "{" not in t


def test_the_overlay_and_the_source():
    o = OVERLAYS["flat_roofs"]
    assert set(o) == {"title", "key", "key_not_counted", "tip", "source", "as_of", "rule"}
    assert o["key_not_counted"].startswith(o["key"]) and o["tip"].endswith(":")
    assert o["source"] == INDICATORS[0].source and o["as_of"] == INDICATORS[0].as_of
    (s,) = SOURCES
    assert LOD2_AS_OF in s.as_of and "verändert" in s.license


def test_roof_text_by_reason():
    base = roof_text(roof(), TEXTS)
    assert base == "1.250 m², 6,4 m hoch (Gebäude für Wirtschaft oder Gewerbe)."
    assert set(NOT_COUNTED) == {"zone", "very_low"} and "3,2 m" in NOT_COUNTED["very_low"]
    assert roof_text(roof(housing=False), TEXTS) == base + " Zählt nicht: " + NOT_COUNTED["zone"]
    assert roof_text(roof(very_low=True), TEXTS) == base + " Zählt nicht: " + NOT_COUNTED["very_low"]
    assert roof_text(roof(housing=False, very_low=True), TEXTS).count("Zählt nicht") == 1


def test_roof_text_names_the_function_of_the_building():
    assert roof_text(roof(use="31001_1000"), TEXTS).endswith("(Wohngebäude).")
    assert roof_text(roof(use="31001_9999"), TEXTS).endswith("(Gebäude).")  # an unknown code, like 9998
    assert roof_text(roof(use="31001_9998"), TEXTS) == roof_text(roof(use="31001_9999"), TEXTS)


def test_roof_text_rounds_the_height_down():
    """A shown height never contradicts a threshold: 3,17 m is no 3,2 m roof, 7,97 m no 8 m roof."""
    for height, shown in ((3.17, "3,1"), (7.97, "7,9"), (6.4, "6,4"), (3.2, "3,2"), (2.5, "2,5"), (6.0, "6,0")):
        assert roof_text(roof(height_m=height), TEXTS).startswith(f"1.250 m², {shown} m hoch "), height
    assert roof_text(roof(area_m2=1250.6), TEXTS).startswith("1.251 m², ")


def test_roof_text_names_the_wall_strip_of_a_counted_roof():
    base = roof_text(roof(), TEXTS)
    walled = roof_text(roof(wall_m2=180.4), TEXTS)
    assert walled.startswith(base + " ") and "180 m²" in walled[len(base):] and walled.endswith(".")
    assert "Zählt nicht" not in walled
    assert roof_text(roof(wall_m2=0.4), TEXTS) == base  # a strip that rounds to 0 m² goes unsaid
    assert "m² frei" not in roof_text(roof(very_low=True, wall_m2=180.4), TEXTS)  # only counted roofs name it
    assert "m² frei" not in roof_text(roof(housing=False, wall_m2=180.4), TEXTS)


def test_calc_example_closes_and_labels():
    e = funnel_calc_example(FUNNEL, TEXTS)
    assert e.area in e.label
    assert [(r.op, r.number, r.total, r.estimate) for r in e.rows] == [
        ("", 2331546, False, False), ("−", 1420178, False, False), ("−", 91616, False, False),
        ("−", 86418, False, False), ("", 733334, True, False), ("×", 0.5, False, False), ("÷", 25, False, False),
        ("", 14700, True, True)]  # the model value rounded to hundreds
    assert all(r.decimals == 0 for i, r in enumerate(e.rows) if i != 5) and e.rows[5].decimals == 1
    assert all("m²" in r.text for r in e.rows[:5])  # the rows before the model value carry the unit
    assert "200 m²" in e.rows[0].text and "3,2 m" in e.rows[2].text and "Wohnmodule" in e.rows[-1].text


def test_calc_example_rounds_the_modules_half_up_to_hundreds():
    numbers = {m: funnel_calc_example({**FUNNEL, "modules": m}, TEXTS).rows[-1].number for m in (14649.9, 14650.0, 14750.0)}
    assert numbers == {14649.9: 14600, 14650.0: 14700, 14750.0: 14800}


def test_calc_example_leaves_out_a_row_that_rounds_to_zero():
    e = funnel_calc_example({**FUNNEL, "wall_m2": 0.3}, TEXTS)
    assert [r.number for r in e.rows] == [2331546, 1420178, 91616, 733334, 0.5, 25, 14700]
