import re

import pytest

from shapely.geometry import box

from pipeline.shared.core.indicator import BOTH
from pipeline.use_cases.building_gaps import model
from pipeline.use_cases.building_gaps.catalog import (ALKIS_AS_OF, AS_OF, BORIS_ZONES_AS_OF, COUNT_TEXT, DOM_YEAR,
                                                      DOP_AS_OF, INDICATORS, OVERLAYS, SITE_TEXT, SOURCE,
                                                      SOURCES, SUITABILITY_TEXT, funnel_calc_example, gap_text,
                                                      german_date)
from pipeline.use_cases.building_gaps.model import Candidate, Gap

BANNED = ("Rücktest", "Lücke", "Geheimhaltung", "Maß:", "Rechenweg", "Zelle", "Spanne", "Abgleich", "NH")
UNGENDERED = re.compile(r"\b\w*(?:eigentümer|einwohner|bewohner|wähler|mieter|bauherr)(?:e?n|s)?\b(?!\*)", re.I)
KZ = "Gemarkung 0466, Flur 171, Nr. 9"
COVER = {"px": 1000, "building": 0.0, "tree": 0.1, "green": 0.1, "open": 0.8, "nan_share": 0.0, "flight": "2025-08-19"}
FUNNEL = {"parcels": 174650, "main_building": 75252, "small": 53428, "use": 44075, "narrow": 837, "front": 280,
          "no_wall": 161, "zone": 213, "no_cover": 0, "green": 243, "built": 62, "not_open": 4, "not": 30, "site": 10,
          "no_verdict": 0, "counted": 55, "counted_m2": 61234.6}


def gap(area=1056.6, front=23.9, kind="row"):
    return Gap("g", "06046617100009______", area, front, 6.0, kind, "1990-01-01", 1, box(0, 0, 1, 1), 0.5, 0.5)


def cand(verdict=None, cover=COVER, **kw):
    return Candidate(gap(**kw), True, cover, verdict)


def verdict(v="counts", reason="parking", by="aerial", note="", checked="2026-11-15"):
    return {"gml_id": "g", "kz": "", "verdict": v, "reason": reason, "note": note, "checked": checked, "by": by}


def texts() -> list[str]:
    (k,) = INDICATORS
    return [k.title, k.source, k.as_of, k.calc, k.rule, k.uncertainty, k.legend_note,
            *OVERLAYS["building_gaps"].values(), *(s.title for s in SOURCES), *COUNT_TEXT.values(),
            *SUITABILITY_TEXT.values(), SITE_TEXT]


def test_the_indicator():
    (k,) = INDICATORS
    assert (k.id, k.title, k.group, k.unit, k.levels, k.decimals, k.section) == (
        "GAP_AREA", "Baulücken", "Boden", "m²", BOTH, 0, "land")
    assert k.layer and k.criterion and not k.estimate and k.ramp == "color:#c51b7d"
    assert (k.source, k.as_of) == (SOURCE, AS_OF)
    assert (ALKIS_AS_OF, DOM_YEAR, DOP_AS_OF, BORIS_ZONES_AS_OF) == ("4.11.2026", "2023", "19.8.2025", "1.1.2024")
    alkis, dom, dop, zones = k.as_of.split(" · ")  # one date per line
    assert alkis.endswith(ALKIS_AS_OF) and dom.endswith(DOM_YEAR) and dop.endswith(DOP_AS_OF)
    assert zones.endswith(BORIS_ZONES_AS_OF)
    assert "2026" in k.legend_note  # docs/texts.md, Map: legend: the note names the year
    assert "BORIS" in k.source.split(" · ")[1] and "ALKIS" in k.source.split(" · ")[0]


def test_the_uncertainty_names_the_dates_and_what_the_map_does_not_know():
    (k,) = INDICATORS
    for text in (ALKIS_AS_OF, DOM_YEAR, DOP_AS_OF, "Bebauungsplan", "Eigentümer*innen", "Augenschein"):
        assert text in k.uncertainty, text


def test_thresholds_in_the_rule_follow_the_model_constants():
    (k,) = INDICATORS
    for text in ("300 m²", "15 m breit", "80 %", "15 m an", "5 m an", "30 m lang", "10 %", "Hälfte"):
        assert text in k.rule, text
    # user, 15.11.: almost without a main building, with both limits of the rule
    first = k.rule.split(". ")[0]
    assert "fast ohne" in first and "(höchstens 5 %" in first and "oder 20 m²)" in first
    assert (model.BUILT_MAX_SHARE, model.BUILT_MAX_M2) == (0.05, 20)
    assert (model.MIN_AREA_M2, 2 * model.HALF_WIDTH_M, model.HOUSING_SHARE_MIN, model.MIN_FRONT_M, model.WALL_MIN_M,
            model.FREE_FRONT_M, model.BUILDING_MAX, model.GREEN_MAX, model.OPEN_MIN) == (
        300, 15, 0.8, 15, 5, 30, 0.10, 0.5, 0.5)


def test_the_rule_says_neither_built_nor_green_not_open_ground():
    """User, 15.11.: the open class is the rest, neither built nor green."""
    (k,) = INDICATORS
    assert "weder bebaut" in k.rule and "offener Boden" not in k.rule


def test_texts_are_full_sentences_without_working_terms():
    (k,) = INDICATORS
    for t in texts():
        assert not [w for w in BANNED if w in t], t
        assert not UNGENDERED.findall(t), t
        assert "{" not in t
    for t in (k.calc, k.rule, k.uncertainty, OVERLAYS["building_gaps"]["rule"], SITE_TEXT, *SUITABILITY_TEXT.values()):
        assert t[0].isupper() and t.endswith("."), t


def test_the_overlay_and_the_source():
    o = OVERLAYS["building_gaps"]
    assert set(o) == {"title", "key", "tip", "source", "as_of", "rule"}
    assert "(" in o["title"] and "(" not in o["key"] and o["tip"].endswith(":")
    assert o["source"] == INDICATORS[0].source and o["as_of"] == INDICATORS[0].as_of
    data, examples, house_for_all = SOURCES
    assert ALKIS_AS_OF in data.as_of and DOP_AS_OF in data.as_of and "verändert" in data.license
    assert data.url == "" and examples.url == ""


def test_the_sources_name_every_example_and_link_the_gemeinwohlbau():
    # user, 15.11.2026: the presentation of the Gemeinwohlbau is public; the map links its page
    _, examples, house_for_all = SOURCES
    assert all(n in examples.title for n in ("Architektenblatt", "gpwirth", "ABG"))
    assert "Gemeinwohlbau" in house_for_all.title and house_for_all.url == "https://gemeinwohlbau.de/idee"
    assert "Gemeinwohlbau" in SUITABILITY_TEXT["house_for_all"]


def test_reason_texts_cover_the_model_reasons():
    assert set(COUNT_TEXT) == set(model.COUNT_REASONS)
    assert list(SUITABILITY_TEXT) == [name for _, name in model.SUITABILITY]


def test_each_suitability_names_its_example_area():
    numbers = {"coop": ("312 m²", "9 "), "house_for_all": ("365 m²", "19 "), "student": ("1.270 m²", "177 "),
               "multi_family": ("2.000 m²", "42 "), "complex": ("5.400 m²", "67 ")}
    for key, (area, number) in numbers.items():
        assert area in SUITABILITY_TEXT[key] and number in SUITABILITY_TEXT[key], key


def test_german_date():
    assert [german_date(d) for d in ("2025-08-19", "2023-07-07", "", "x")] == ["19.8.2025", "7.7.2023", "", ""]


def test_gap_text_starts_with_parcel_area_front_and_kind():
    site = verdict("site", "")
    assert gap_text(cand(site), KZ).startswith(f"{KZ}. 1.056 m², 23 m an der Straße, ")  # rounded down
    assert gap_text(cand(site, kind="free"), KZ) != gap_text(cand(site, kind="row"), KZ)


def test_gap_text_of_a_counted_gap_names_the_kind_the_date_and_what_fits():
    aerial = gap_text(cand(verdict()), KZ)
    assert f"Zählt: Parkplatz, geprüft im Luftbild vom {DOP_AS_OF}. " in aerial  # user, 15.11.: the verdict first
    assert aerial.endswith(" " + SUITABILITY_TEXT["house_for_all"]) and "Zählt nicht" not in aerial
    assert gap_text(cand(verdict(), area=364.9), KZ).endswith(" " + SUITABILITY_TEXT["coop"])
    own_flight = gap_text(cand(verdict(), cover={**COVER, "flight": "2023-07-07"}), KZ)
    assert "7.7.2023" in own_flight and DOP_AS_OF not in own_flight  # the flight of this candidate
    site = gap_text(cand(verdict(reason="yard", by="site", checked="2026-11-20")), KZ)
    assert "Zählt: Hof, geprüft vor Ort am 20.11.2026. " in site and "Luftbild" not in site
    assert gap_text(cand(verdict(), area=5400.0), KZ).endswith(SUITABILITY_TEXT["complex"])
    assert gap_text(cand(verdict(), area=5399.9), KZ).endswith(SUITABILITY_TEXT["multi_family"])


def test_gap_text_refuses_a_gap_that_is_not_drawn():
    """User, 15.11.: a gap judged not is not on the map, so it has no tooltip."""
    with pytest.raises(ValueError, match="not drawn"):
        gap_text(cand(verdict("not", "square")), KZ)


def test_the_overlay_rule_says_what_the_map_leaves_out():
    rule = OVERLAYS["building_gaps"]["rule"]
    assert "nicht zählen" in rule and "Zählt nicht" not in rule and "warum nicht" not in rule
    assert "noch nicht geprüft" in rule  # user, 15.11.: a gap without a verdict is not drawn


def test_gap_text_of_a_gap_to_check_on_site_has_no_zaehlt_nicht():
    """User 15.11.: who wants to know goes there. The site line has no prefix."""
    site = gap_text(cand(verdict("site", "")), KZ)
    assert site == f"{KZ}. 1.056 m², 23 m an der Straße, zwischen Nachbarhäusern. {SITE_TEXT} " \
                   f"{SUITABILITY_TEXT['house_for_all']}"
    assert "Zählt" not in site


def test_gap_text_refuses_a_gap_without_a_verdict():
    """User, 15.11.: a gap without a verdict (after a new delivery) is not drawn until judged."""
    with pytest.raises(ValueError, match="not drawn"):
        gap_text(cand(), KZ)


def test_calc_example_lists_the_funnel():
    e = funnel_calc_example(FUNNEL)
    assert e.area in e.label
    assert [(r.op, r.number, r.total) for r in e.rows] == [
        ("", 174650, False), ("−", 75252, False), ("−", 53428, False), ("−", 44075, False), ("−", 837, False),
        ("−", 280, False), ("−", 161, False), ("−", 213, False), ("−", 243, False), ("−", 62, False), ("−", 4, False),
        ("−", 30, False), ("−", 10, False), ("", 55, True), ("", 61235, True)]
    assert all(r.decimals == 0 and not r.estimate for r in e.rows)
    rows = {r.number: r.text for r in e.rows}
    assert "300 m²" in rows[53428] and "15 m" in rows[837] and "15 m" in rows[280] and "30 m" in rows[161]
    assert rows[75252] == "mit Hauptgebäude über 5 % oder 20 m²"
    assert "m²" in e.rows[-1].text


def test_calc_example_adds_up():
    e = funnel_calc_example(FUNNEL)
    assert e.rows[0].number - sum(r.number for r in e.rows if r.op == "−") == e.rows[-2].number


def test_calc_example_keeps_the_totals_when_nothing_counts():
    e = funnel_calc_example({**FUNNEL, "not": 0, "site": 0, "no_verdict": 95, "counted": 0, "counted_m2": 0.0})
    assert [(r.number, r.total) for r in e.rows[-3:]] == [(95, False), (0, True), (0, True)]
