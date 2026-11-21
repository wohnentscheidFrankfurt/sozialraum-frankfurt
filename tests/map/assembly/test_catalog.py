import re
from pathlib import Path
from dataclasses import asdict, is_dataclass, replace

import pytest

from pipeline.use_cases.election.catalog import election_indicators
from pipeline.map.assembly.catalog import (CATALOG, LAYER_ORDER, _ENTRIES, breakdown_numbers, catalog_numbers, map_catalog,
                                           merge_examples, map_overlays, map_sources)
from pipeline.shared.core.indicator import Z11_AS_OF, Z22_AS_OF, fill, format_de
from pipeline.use_cases.ownership_history import catalog as ownership_history_catalog
from pipeline.use_cases.ownership_cells.catalog import GRID_OVERLAY
from pipeline.use_cases.survey.catalog import half_width_numbers
from pipeline.use_cases.survey.model import INCOME_LIMITS


def test_catalog_is_unique_and_complete():
    ids = [k.id for k in CATALOG]
    assert len(ids) == len(set(ids))
    assert {"OWN_PUBLIC", "SOC_MIN_INCOME", "HOU_RENTERS", "LAND_VALUE", "PROT_SOCIAL", "LAND_PENDING_PLAN"} <= set(ids)
    k = {x.id: x for x in CATALOG}
    # pipeline/use_cases/public_housing/README.md: ABG and NH together, only per Stadtteil, with the count beside it
    assert not {"OWN_ABG", "OWN_NH", "ABG_DWELLINGS", "NH_DWELLINGS"} & set(ids)
    assert "PUBLIC_DWELLINGS" not in ids
    # the count stands in the tooltip, its ⓘ is the one of the layer (docs/texts.md, ⓘ protocol)
    assert "OWN_DWELLINGS" not in ids
    assert k["OWN_PUBLIC"].levels == ("quarter",) and k["OWN_PUBLIC"].ramp == "color:#d40000"
    assert all(x.criterion for x in CATALOG if x.id not in ("SH_COUNT", "HOU_PRE1919_DWELLINGS",
                                                            "HOU_1949_1978_DWELLINGS",
                                                            "HOU_VACANT_MARKET_DWELLINGS",
                                                            "HOU_VACANT_ALL_DWELLINGS",
                                                            "LIF_RENT_BURDEN_INCOME_LOW", "LIF_RENT_BURDEN_INCOME_MID",
                                                            "LIF_RENT_BURDEN_INCOME_HIGH"))


FETCH = {"fetch_date": "8.10.2026"}
ALL_RANGES = {k.id: {"low": 1.0, "high": 1.0} for k in CATALOG}
CITY_BREAKDOWN = [{"indicator": "LIF_RENT_BURDEN_INCOME_LOW", "value": 53.3, "kind": "computed"},
                  {"indicator": "LIF_RENT_BURDEN_INCOME_MID", "value": 36.1, "kind": "computed"},
                  {"indicator": "LIF_RENT_BURDEN_INCOME_HIGH", "value": 23.9, "kind": "computed"}]
HALF_WIDTHS = {"typical": 4.6, "max_low": 13.3, "max_upper": 3.8}
NUMBERS = FETCH | catalog_numbers(ALL_RANGES) | breakdown_numbers(CITY_BREAKDOWN) | half_width_numbers(HALF_WIDTHS)


def test_map_catalog_sets_the_as_of_date_of_the_wfs_indicators():
    raw = {x.id: x for x in CATALOG}
    k = {x.id: x for x in map_catalog(NUMBERS, [])}
    for i in ("PROT_SOCIAL", "LAND_PENDING_PLAN"):
        assert "{fetch_date}" in raw[i].as_of and k[i].as_of == raw[i].as_of.replace("{fetch_date}", "8.10.2026"), i
    assert Z22_AS_OF in k["PROT_SOCIAL"].as_of
    assert k["OWN_PUBLIC"].as_of == raw["OWN_PUBLIC"].as_of  # unchanged, no placeholder
    assert Z22_AS_OF in k["OWN_PUBLIC"].as_of and Z11_AS_OF in k["OWN_PUBLIC"].as_of
    assert [x.id for x in map_catalog(NUMBERS, [])][:len(CATALOG)] == [x.id for x in CATALOG]


def test_every_catalog_entry_carries_its_five_ramp_colours():
    from pipeline.shared.core import colours
    entries = map_catalog(NUMBERS, [{"name": "FDP", "color": "#ffd600", "key": "ELEC_FDP", "position": 5}])
    assert all(k.colors == tuple(colours.ramp(k.ramp)) and len(k.colors) == 5 for k in entries)
    assert {k.id: k.colors[4] for k in entries}["OWN_PUBLIC"] == "#d40000"
    assert any(k.id == "ELEC_FDP" for k in entries)


PROTOCOL_FIELDS = ("source", "as_of", "calc")
NOT_A_FACT = (r"\beher\b", "2026 im Mittel", "gut zwei Drittel", "Grobe Schätzung", "Anteil an den Stimmen")


def test_every_info_is_a_protocol(example_ids):
    """docs/texts.md, ⓘ protocol: Quelle, Stand, Rechnung always; Regel and Unsicherheit only when needed; only
    facts."""
    lists = [{"name": "CDU", "key": "ELEC_CDU", "color": "#1d1d1b"}, {"name": "Sonstige", "key": "ELEC_OTHER", "color": "#999"}]
    for k in [*CATALOG, *election_indicators(lists)]:
        # an indicator with a worked example: the example is the Rechnung, assembly adds it
        fields = [f for f in PROTOCOL_FIELDS if not (f == "calc" and k.id in example_ids)]
        assert all(getattr(k, f).strip() for f in fields), k.id
        assert k.id not in example_ids or k.calc == "", k.id
        text = " ".join((k.source, k.as_of, k.calc, k.rule, k.uncertainty))
        assert not [w for w in NOT_A_FACT if re.search(w, text)], (k.id, text)
        assert not hasattr(k, "caveat")


def test_numbers_in_the_protocols_follow_the_code():
    from pipeline.shared.geography.model import MIN_OVERLAP_M2
    k = {x.id: x for x in CATALOG}
    assert f"{MIN_OVERLAP_M2 // 10_000} ha" in k["LAND_PENDING_PLAN"].calc


def test_layer_order_names_every_indicator_once():
    # against _ENTRIES, not CATALOG: CATALOG is built from LAYER_ORDER, so it would drop a missing id silently
    assert sorted(k.id for k in _ENTRIES) == sorted(LAYER_ORDER)
    assert len(_ENTRIES) == len(LAYER_ORDER)
    assert len(set(LAYER_ORDER)) == len(LAYER_ORDER)
    assert [k.id for k in CATALOG] == list(LAYER_ORDER)


def test_map_overlays_has_all_nine_with_the_fetch_date():
    info = map_overlays({"fetch_date": "1.10.2026"})
    assert list(info) == ["social_preservation", "social_preservation_pending", "townscape", "townscape_pending",
                          "pending_plans", "land_value", "flat_roofs", "building_gaps", "grid"]
    # docs/texts.md, ⓘ protocol: areas need no Rechnung, the grid has one
    assert all({"title", "source", "as_of", "rule"} <= set(v) <= {"title", "key", "key_not_counted", "tip", "since",
                                                                 "source", "as_of", "calc",
                                                                 "rule", "uncertainty"}
               and all(v.values()) for v in info.values())
    assert set(info["grid"]) == {"title", "source", "as_of", "calc", "rule", "uncertainty"}
    assert "1.10.2026" in info["social_preservation"]["as_of"]
    assert info["grid"] == GRID_OVERLAY["de"]


def test_overlays_carry_the_name_of_their_key_row_without_the_pattern_word():
    info = map_overlays({"fetch_date": "1.10.2026"})
    keys = {n: v["key"] for n, v in info.items() if "key" in v}
    assert list(keys) == ["social_preservation", "social_preservation_pending", "townscape", "townscape_pending",
                          "pending_plans", "land_value", "flat_roofs", "building_gaps"]
    # the pattern word stands in brackets: the key row has none, the sidebar keeps it
    assert all(k.strip() and "(" not in k for k in keys.values()) and len(set(keys.values())) == len(keys)
    assert "(" in info["social_preservation"]["title"]


RANGES = {"OWN_PUBLIC": {"low": 0.57, "high": 8.82}, "OWN_COMPANY": {"low": 3.5, "high": 3.5},
          "OWN_COOP": {"low": 0.0, "high": 2.14}}


def test_catalog_numbers():
    n = catalog_numbers(RANGES)
    # half ranges in the unit of the row: points with one decimal
    assert (n["range_OWN_PUBLIC"], n["range_OWN_COMPANY"], n["range_OWN_COOP"]) == ("0,6 bis 8,8", "3,5", "0 bis 2,1")
    # the largest half range alone (Genossenschaften and the groups with a fixed half range)
    assert (n["high_OWN_PUBLIC"], n["high_OWN_COMPANY"], n["high_OWN_COOP"]) == ("8,8", "3,5", "2,1")
    assert set(n) == {f"{p}_{k}" for p in ("range", "high") for k in RANGES}


def test_catalog_numbers_fill_the_unsicherheit_of_every_ownership_layer():
    """docs/texts.md, ⓘ protocol: the Unsicherheit of every ownership layer gets its numbers from the build."""
    n = catalog_numbers(RANGES | {"OWN_STATE": {"low": 2.0, "high": 2.0}})
    k = {x.id: replace(x, uncertainty=fill(x.uncertainty, n)) for x in CATALOG if f"range_{x.id}" in n}
    assert "0,6 bis 8,8 Prozentpunkte" in k["OWN_PUBLIC"].uncertainty
    assert "2,1 Prozentpunkte" in k["OWN_COOP"].uncertainty and "3,5 Prozentpunkte" in k["OWN_COMPANY"].uncertainty
    # Review Focus 2: no „,0“
    assert "2 Prozentpunkte" in k["OWN_STATE"].uncertainty and "2,0" not in k["OWN_STATE"].uncertainty
    # low and high round alike: one number
    same = fill(next(x for x in CATALOG if x.id == "OWN_PUBLIC").uncertainty,
                catalog_numbers({"OWN_PUBLIC": {"low": 3.5, "high": 3.52}}))
    assert "3,5 Prozentpunkte" in same and "3,5 bis" not in same


def test_every_placeholder_of_the_map_is_known():
    # every name a text uses is one the build delivers: fetch_date and the ranges of the build; an unknown name raises
    map_catalog(NUMBERS, [])
    map_overlays(NUMBERS)
    map_sources(NUMBERS)
    with pytest.raises(KeyError):
        map_catalog(FETCH, [])  # the Unsicherheit of the owner groups needs the ranges


def test_breakdown_numbers_give_the_city_value_of_each_line_as_the_tooltip_shows_it():
    """Rounded half up to 5 points, with „~“ (docs/texts.md, Numbers)."""
    assert breakdown_numbers(CITY_BREAKDOWN) == {"city_LIF_RENT_BURDEN_INCOME_LOW": "~55 %",
                                                 "city_LIF_RENT_BURDEN_INCOME_MID": "~35 %",
                                                 "city_LIF_RENT_BURDEN_INCOME_HIGH": "~25 %"}
    assert breakdown_numbers([*CITY_BREAKDOWN, {"indicator": "LIF_RENT_BURDEN_RATIO", "value": 29,
                                                "kind": "published"}]) == breakdown_numbers(CITY_BREAKDOWN)
    with pytest.raises(KeyError):
        breakdown_numbers(CITY_BREAKDOWN[:2])  # a line without its city value must not reach the ⓘ


def test_the_rent_burden_info_gets_the_half_widths_and_the_city_lines():
    rent = next(k for k in map_catalog(NUMBERS, []) if k.id == "LIF_RENT_BURDEN_RATIO")
    assert not [f for f in INFO_FIELDS if "{" in getattr(rent, f)]
    lower, upper = (format_de(limit, 0, "€") for limit in INCOME_LIMITS)
    # the half widths of the build (typical and largest below the lower limit, largest above it), in any order
    assert sorted(re.findall(r"±(\d+)", rent.uncertainty)) == sorted(half_width_numbers(HALF_WIDTHS).values())
    assert lower in rent.uncertainty
    with pytest.raises(KeyError):
        map_catalog(FETCH | catalog_numbers(ALL_RANGES) | breakdown_numbers(CITY_BREAKDOWN), [])
    # the city value of each income group and both income limits
    assert sorted(re.findall(r"~\d+ %", rent.calc)) == sorted(breakdown_numbers(CITY_BREAKDOWN).values())
    assert lower in rent.calc and upper in rent.calc


def test_map_catalog_fills_every_text_field():
    placeholder = re.compile(r"\{\w+\}")
    assert not [k.id for k in map_catalog(NUMBERS, LISTS) for f in INFO_FIELDS if placeholder.search(getattr(k, f))]


def test_estimates_are_the_ownership_construction_year_vacancy_and_income_indicators():
    """docs/texts.md, Numbers: the map writes „~“ before these values. The construction year is an estimate
    because of the cap per cell (pipeline/use_cases/construction_year/README.md), the vacancy because of the filling of the „–“
    cells (pipeline/use_cases/housing/README.md), the rent burden by income because the map computes it from a sample
    (pipeline/use_cases/survey/README.md)."""
    assert {k.id for k in CATALOG if k.estimate} == {"OWN_PUBLIC", "OWN_COOP", "OWN_COMPANY", "OWN_PERSON", "OWN_STATE",
                                                     "OWN_NONPROFIT", "HOU_PRE1919", "HOU_PRE1919_DWELLINGS",
                                                     "HOU_1949_1978", "HOU_1949_1978_DWELLINGS", "HOU_VACANT_MARKET",
                                                     "HOU_VACANT_MARKET_DWELLINGS", "HOU_VACANT_ALL",
                                                     "HOU_VACANT_ALL_DWELLINGS", "LIF_RENT_BURDEN_INCOME_LOW",
                                                     "LIF_RENT_BURDEN_INCOME_MID", "LIF_RENT_BURDEN_INCOME_HIGH"}


BANNED = ("Rücktest", "Lücke", "Geheimhaltung", "Maß:", "Rechenweg", "Zelle", "Spanne", "Abgleich")
INFO_FIELDS = ("source", "as_of", "calc", "rule", "uncertainty")
LISTS = [{"name": "CDU", "key": "ELEC_CDU", "color": "#1d1d1b"}, {"name": "Sonstige", "key": "ELEC_OTHER", "color": "#999"}]


def _info_texts():
    """Every text of every ⓘ as the map shows it: (where, field, text)."""
    catalog = map_catalog(NUMBERS, LISTS)
    out = [(k.id, f, getattr(k, f)) for k in catalog for f in INFO_FIELDS]
    return out + [(f"overlay {n}", f, t) for n, v in map_overlays(NUMBERS).items() for f, t in v.items()]


def test_no_info_uses_a_term_of_the_working_sessions():
    """docs/texts.md, Terms: a reader without our context understands every ⓘ."""
    texts = _info_texts()
    hits = [(i, f, w) for i, f, t in texts for w in BANNED if w in t]
    hits += [(i, f, "NH") for i, f, t in texts if re.search(r"\bNH\b", t)]
    hits += [(i, f, "4000W") for i, f, t in texts if "4000W" in t and f != "source"]
    assert not hits


def test_rules_and_uncertainties_are_full_sentences():
    """docs/texts.md, Lines: Regel and Unsicherheit are full sentences."""
    texts = [(i, t) for i, f, t in _info_texts() if f in ("rule", "uncertainty") and t]
    assert not [(i, t) for i, t in texts if not (t[0].isupper() and t.endswith("."))]


def test_owner_groups_have_the_colours_of_the_view_trend():
    # docs/design.md, Owner groups: the colour of a group (profile, grid) and the ramp of its layer
    k = {x.id: x for x in CATALOG}
    colours = {"OWN_PUBLIC": "#d40000", "OWN_STATE": "#ffc9c2", "OWN_COOP": "#8c0000", "OWN_COMPANY": "#262626",
               "OWN_PERSON": "#a6a6a6", "OWN_NONPROFIT": "#f07067"}
    assert {i: k[i].color for i in colours} == colours
    assert all(k[i].ramp == f"color:{c}" for i, c in colours.items() if i != "OWN_STATE")
    # a ramp to the light #ffc9c2 turns muddy when darkened: Bund oder Land takes the ramp of the public red
    assert k["OWN_STATE"].ramp == "color:#d40000"
    # only owner groups have a colour; every other layer keeps its ramp (docs/design.md, Owner groups)
    assert {x.id for x in CATALOG if x.color} == set(colours)
    assert not [x.id for x in CATALOG if x.ramp.startswith("list:")]


def test_map_sources_put_in_the_fetch_date_and_keep_the_footer_fields():
    from pipeline.map.assembly.catalog import SOURCE_ORDER
    out = map_sources(FETCH)
    assert len(out) == len(SOURCE_ORDER) == len({s.title for s in SOURCE_ORDER})
    assert all(set(s) == {"title", "as_of", "license", "url"} and "{" not in s["as_of"] for s in out)
    assert all(s["url"] == "" or s["url"].startswith("https://") for s in out)
    from pipeline.use_cases.protection.catalog import SOURCES as PROTECTION_SOURCES
    planas = PROTECTION_SOURCES[0]
    assert "{fetch_date}" in planas.as_of and "8.10.2026" in out[SOURCE_ORDER.index(planas)]["as_of"]
    from pipeline.use_cases.new_construction.catalog import SOURCES as NEW_CONSTRUCTION_SOURCES
    assert all(s in SOURCE_ORDER for s in NEW_CONSTRUCTION_SOURCES)
    assert {s.title for s in NEW_CONSTRUCTION_SOURCES} <= {s["title"] for s in out}
    # the end of the last rent year; „Melderegister“ is the name of the source
    assert [s["as_of"] for s in out if "Melderegister" in s["title"]] == ["31.12.2025"]


# docs/texts.md, Map: profile: the topics of the profile and of „Stadt“, in this order
SECTIONS = ("ownership", "situation", "rent", "stock", "land", "planning", "election")
SECTION_IDS = {
    "ownership": ["OWN_PUBLIC", "OWN_COOP", "OWN_COMPANY", "OWN_PERSON", "OWN_STATE", "OWN_NONPROFIT"],
    "situation": ["SOC_MIN_INCOME", "SOC_UNEMPLOYED", "SOC_INDEX", "LIF_ATTACHMENT"],
    "rent": ["HOU_RENTERS", "HOU_RENT", "LIF_RENT_BURDEN_RATIO", "LIF_RENT_BURDEN_INCOME_LOW",
             "LIF_RENT_BURDEN_INCOME_MID", "LIF_RENT_BURDEN_INCOME_HIGH"],
    "stock": ["SH_SHARE", "SH_COUNT", "HOU_VACANT_MARKET", "HOU_VACANT_MARKET_DWELLINGS", "HOU_VACANT_ALL",
              "HOU_VACANT_ALL_DWELLINGS", "HOU_PRE1919", "HOU_PRE1919_DWELLINGS", "HOU_1949_1978",
              "HOU_1949_1978_DWELLINGS"],
    "land": ["LAND_VALUE", "ROOF_FLAT", "GAP_AREA"],
    "planning": ["PROT_SOCIAL", "LAND_PENDING_PLAN"],
}


def test_every_entry_has_a_section_and_one_german_group_has_one_section():
    entries = [*_ENTRIES, *election_indicators([])]
    assert {k.section for k in entries} == set(SECTIONS)
    sections_of = {}
    for k in entries:
        sections_of.setdefault(k.group, set()).add(k.section)
    assert all(len(v) == 1 for v in sections_of.values()), sections_of
    assert len({next(iter(v)) for v in sections_of.values()}) == len(sections_of)  # and one group per section


def test_every_section_has_a_heading():
    entries = [*_ENTRIES, *election_indicators([{"name": "CDU", "key": "ELEC_CDU", "color": "#000"}])]
    assert {k.section for k in entries if k.group.strip()} == set(SECTIONS)


def test_layer_order_follows_the_topics():
    assert list(LAYER_ORDER) == [i for ids in SECTION_IDS.values() for i in ids]
    assert all(k.section == s for s, ids in SECTION_IDS.items() for k in CATALOG if k.id in ids)


def test_survey_area_marks_exactly_the_survey_values():
    entries = [*_ENTRIES, *election_indicators([])]
    assert {k.id for k in entries if k.survey_area} == {"LIF_RENT_BURDEN_RATIO", "LIF_RENT_BURDEN_INCOME_LOW",
                                                         "LIF_RENT_BURDEN_INCOME_MID", "LIF_RENT_BURDEN_INCOME_HIGH",
                                                         "LIF_ATTACHMENT"}


def test_every_overlay_has_a_title_and_a_tip_except_the_grid_whose_tip_is_built_in_the_browser():
    info = map_overlays(NUMBERS)
    assert all(v["title"].strip() for v in info.values())
    assert all(v["tip"].strip() for n, v in info.items() if n != "grid") and "tip" not in info["grid"]
    from pipeline.use_cases.land.catalog import BORIS_AS_OF
    assert BORIS_AS_OF in info["land_value"]["tip"]


def test_the_map_catalog_holds_no_ramp_name_the_browser_reads_the_colours():
    from dataclasses import asdict
    from pipeline.map.assembly.catalog import map_catalog_payload
    entries = map_catalog_payload(map_catalog(NUMBERS, []))
    assert all("ramp" not in e and len(e["colors"]) == 5 for e in entries) and entries[0]["section"] == "ownership"


# docs/texts.md, Texts per view: a text explains only the view, layer and state the reader is in. A text of the map never names
# the view Trend. A text of the view Trend never names the map or one of its layers.
MAP_TEXT_FIELDS = ("title", "group", "legend_note", "legend_detail", "source", "as_of", "calc", "rule", "uncertainty")


def _strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for v in value.values():
            yield from _strings(v)
    elif isinstance(value, (list, tuple)):
        for v in value:
            yield from _strings(v)
    elif is_dataclass(value):
        yield from _strings(asdict(value))


def _view_texts():
    trend = {name: getattr(ownership_history_catalog, name)["de"]
             for name in ("GROUP_TEXTS", "SECTORS", "CHARTS", "SIZE_LABELS", "SOURCES", "HISTORY_SOURCE")}
    yield from (("Trend", name, text) for name, v in trend.items() for text in _strings(v))


def _map_texts():
    for k in map_catalog(NUMBERS, []):
        for f in MAP_TEXT_FIELDS:
            yield "map", f"{k.id}.{f}", getattr(k, f)
    for name, overlay in map_overlays(NUMBERS).items():
        for f, text in overlay.items():
            yield "map", f"overlay {name}.{f}", text


# (view of the text, where it stands, text) -> the words the view must not name
FORBIDDEN = {"map": ("Trend",), "Trend": ("Karte", "Schicht")}
TEXTS = [*_map_texts(), *_view_texts()]


def test_the_texts_cover_every_indicator_and_overlay():
    where = {w for _, w, _ in TEXTS}
    assert {f"{k.id}.calc" for k in map_catalog(NUMBERS, [])} <= where
    assert {"overlay grid.rule", "overlay pending_plans.rule"} <= where
    assert "GROUP_TEXTS" in {w for v, w, _ in TEXTS if v == "Trend"} and len(TEXTS) > 300


@pytest.mark.parametrize("view,where,text", TEXTS, ids=[f"{v}:{w}" for v, w, _ in TEXTS])
def test_a_text_explains_only_the_view_it_is_in(view, where, text):
    assert not [word for word in FORBIDDEN[view] if word in text], text


# docs/texts.md, Gender: a person noun carries the gender star or gives way to a neutral form. Compounds
# (Eigentümerquote, Mieteranteil) pass: the noun must end the word. Proper names stay.
UNGENDERED = re.compile(r"\b\w*(?:eigentümer|einwohner|bewohner|wähler|mieter|bauherr)(?:e?n|s)?\b(?!\*)", re.I)
# source vocabulary: the column „Einwohner“ of the Zensus grid
SOURCE_TERMS = {"pipeline/shared/zensus/sources.py": ["Einwohner"]}


@pytest.mark.parametrize("view,where,text", TEXTS, ids=[f"{v}:{w}" for v, w, _ in TEXTS])
def test_a_text_genders_its_person_nouns(view, where, text):
    assert not UNGENDERED.findall(text), text


def test_the_pipeline_genders_its_person_nouns():
    """All texts of the pipeline, also those outside TEXTS (Neubau, candidates, worked examples, cover note)."""
    root = Path(__file__).resolve().parents[3]
    found = {str(f.relative_to(root)): UNGENDERED.findall(f.read_text(encoding="utf-8"))
             for f in sorted((root / "pipeline").rglob("*.py"))}
    assert {k: v for k, v in found.items() if v and v != SOURCE_TERMS.get(k)} == {}

    assert UNGENDERED.findall("Eigentümers, Bauherr, Hauseigentümer, Kleinvermietern, Einwohner*innen, Eigentümerquote, "
                              "Mieteranteil") == ["Eigentümers", "Bauherr", "Hauseigentümer", "Kleinvermietern"]


# docs/texts.md, Map: legend: one line under the legend title says what the shown number is.
PARTIES = ("CDU", "AFD", "SPD", "GRUENE", "FDP", "DIELINKE", "VOLT", "OTHER")
ALL_LISTS = [{"name": p.title(), "key": f"ELEC_{p}", "color": "#999"} for p in PARTIES]


def test_every_layer_has_its_legend_note_and_no_other_indicator_needs_one():
    catalog = map_catalog(NUMBERS, ALL_LISTS)
    layers = {k.id: k.legend_note for k in catalog if k.layer}
    assert all(note.strip() for note in layers.values())
    assert not [k.id for k in catalog if not k.layer and k.legend_note]


def test_every_legend_note_names_the_latest_year_of_its_as_of_date():
    """docs/texts.md, Map: legend: the note names numerator, base and year. A rank names its range instead."""
    catalog = [k for k in map_catalog(NUMBERS, ALL_LISTS) if k.layer and not k.rank]
    years = {k.id: max(re.findall(r"(?:19|20)\d\d", k.as_of)) for k in catalog}
    assert len(years) > 20
    assert not [(k.id, years[k.id], k.legend_note) for k in catalog if years[k.id] not in k.legend_note]


def test_two_ownership_layers_have_a_second_note_line():
    from pipeline.map.assembly.catalog import map_catalog_payload
    catalog = map_catalog(NUMBERS, ALL_LISTS)
    details = {k.id: k.legend_detail for k in catalog if k.legend_detail}
    assert set(details) == {"OWN_COMPANY", "OWN_PERSON"}
    payload = {e["id"]: e for e in map_catalog_payload(catalog)}
    assert {i: payload[i]["legend_detail"] for i in details} == details


def test_the_legend_note_travels_in_the_payload():
    from pipeline.map.assembly.catalog import map_catalog_payload
    catalog = map_catalog(NUMBERS, ALL_LISTS)
    payload = {e["id"]: e for e in map_catalog_payload(catalog)}
    assert ({i: e["legend_note"] for i, e in payload.items() if e["layer"]}
            == {k.id: k.legend_note for k in catalog if k.layer})


def test_every_ownership_layer_explains_the_dwellings_of_its_tooltip():
    """docs/texts.md, ⓘ protocol: Regel and Unsicherheit end with the count of the tooltip
    (the Rechnung says it in the tooltip row of the worked example). No layer, no tooltip: OWN_NONPROFIT."""
    from pipeline.shared.core.indicator import (TIP_DWELLINGS_RULE,
                                                 TIP_DWELLINGS_UNCERTAINTY)
    own = {k.id: k for k in CATALOG if k.section == "ownership"}
    layers = [k for k in own.values() if k.layer]
    assert [k.id for k in layers] == ["OWN_PUBLIC", "OWN_COOP", "OWN_COMPANY", "OWN_PERSON", "OWN_STATE"]
    assert all(k.rule.endswith(" " + TIP_DWELLINGS_RULE) for k in layers)
    assert all(k.uncertainty.endswith(" " + TIP_DWELLINGS_UNCERTAINTY) for k in layers)
    nonprofit = own["OWN_NONPROFIT"]
    assert "Tooltip" not in nonprofit.calc + nonprofit.rule + nonprofit.uncertainty


def test_map_catalog_puts_the_example_on_its_indicator():
    example = {"area": "X", "rows": []}
    by_id = {k.id: k for k in map_catalog(NUMBERS, ALL_LISTS, {"OWN_STATE": example})}
    assert by_id["OWN_STATE"].calc_example == example
    assert [i for i, k in by_id.items() if k.calc_example] == ["OWN_STATE"]
    assert all(k.calc_example is None for k in map_catalog(NUMBERS, ALL_LISTS))


def test_only_the_deprivation_index_is_a_rank():
    assert {k.id for k in CATALOG if k.rank} == {"SOC_INDEX"}


def test_every_grid_group_has_a_dative_name():
    from pipeline.use_cases.ownership_cells.catalog import GROUP_DATIVE
    from pipeline.use_cases.ownership_cells.model import GRID_GROUPS
    assert set(GROUP_DATIVE["de"]) == set(GRID_GROUPS)


def test_each_count_is_a_tooltip_line_of_its_share():
    k = {x.id: x for x in CATALOG}
    pairs = {x.id: x.count_of for x in CATALOG if x.count_of}
    assert pairs == {"SH_COUNT": "SH_SHARE", "HOU_PRE1919_DWELLINGS": "HOU_PRE1919",
                     "HOU_1949_1978_DWELLINGS": "HOU_1949_1978",
                     "HOU_VACANT_MARKET_DWELLINGS": "HOU_VACANT_MARKET", "HOU_VACANT_ALL_DWELLINGS": "HOU_VACANT_ALL"}
    assert all(k[s].layer and not k[c].layer and k[c].levels == k[s].levels and k[c].unit.endswith("Wohnungen")
               for c, s in pairs.items())


def test_merge_examples_joins_the_parts():
    assert merge_examples({"A": 1}, {"B": 2}) == {"A": 1, "B": 2}


def test_merge_examples_rejects_a_duplicate_id():
    with pytest.raises(ValueError, match="A"):
        merge_examples({"A": 1}, {"A": 2})
