from pipeline.shared.core.indicator import year_of
from pipeline.use_cases.land.catalog import (BORIS_AS_OF, BORIS_DATE, BUILDING_NAMES, INDICATORS as BY_LANGUAGE,
                                             OVERLAYS as OVERLAYS_BY_LANGUAGE, SOURCES as SOURCES_BY_LANGUAGE, T,
                                             USE_NAMES as USE_BY_LANGUAGE, use_name)

INDICATORS, OVERLAYS, SOURCES, TEXTS = BY_LANGUAGE["de"], OVERLAYS_BY_LANGUAGE["de"], SOURCES_BY_LANGUAGE["de"], T["de"]
USE_NAMES = USE_BY_LANGUAGE["de"]


def test_land_catalog_and_overlays():
    assert [k.id for k in INDICATORS] == ["LAND_VALUE", "LAND_PENDING_PLAN"]
    assert set(OVERLAYS) == {"pending_plans", "land_value"}
    assert "{fetch_date}" in OVERLAYS["pending_plans"]["as_of"]


def test_use_codes_are_spelled_out():
    names = BUILDING_NAMES["de"]
    assert use_name("W", "", TEXTS) == USE_NAMES["W"] and use_name("M", "", TEXTS) == USE_NAMES["M"]
    assert use_name("WA", "", TEXTS) == "WA"
    # one form for every zone: area, then the building type of BORIS where the zone has one
    assert use_name("M", "EFH", TEXTS) == f"{USE_NAMES['M']}, {names['EFH']}"
    assert [use_name("W", b, TEXTS) for b in ("MFH", "BH", "WGH", "BGH", "XY")] == [
        f"{USE_NAMES['W']}, {names[b]}" for b in ("MFH", "BH", "WGH", "BGH")] + [f"{USE_NAMES['W']}, XY"]


def test_land_values_are_of_2026_on_the_zones_of_2024():
    zones_2024 = TEXTS["zones_2024"]
    land = INDICATORS[0]
    assert BORIS_AS_OF == "1.1.2026" and land.as_of == BORIS_AS_OF and BORIS_AS_OF in land.legend_note
    assert TEXTS.date(BORIS_DATE) == BORIS_AS_OF  # the string of the cover note and the date of the texts agree
    assert "2024" in zones_2024 and year_of(BORIS_AS_OF) in zones_2024
    assert land.rule.endswith(zones_2024) and OVERLAYS["land_value"]["rule"].endswith(zones_2024)
    assert OVERLAYS["land_value"]["title"].endswith(" " + year_of(BORIS_AS_OF))
    assert OVERLAYS["land_value"]["tip"].endswith(f" {BORIS_AS_OF}:")


def test_boris_licence_is_zero():
    # the WFS 2024 and the WMS 2026 allow every use without condition (AccessConstraints of both services)
    # the licence names the Gutachterausschüsse as licensor
    assert SOURCES[0].license.split(", ") == ["dl-de/zero-2-0", "Gutachterausschüsse"]
