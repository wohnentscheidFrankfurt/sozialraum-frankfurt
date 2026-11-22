from pipeline.use_cases.protection.catalog import INDICATORS as BY_LANGUAGE, OVERLAYS as OVERLAYS_BY_LANGUAGE, T

INDICATORS, OVERLAYS, TEXTS = BY_LANGUAGE["de"], OVERLAYS_BY_LANGUAGE["de"], T["de"]


def test_protection_catalog_and_overlays():
    assert [k.id for k in INDICATORS] == ["PROT_SOCIAL"]
    assert list(OVERLAYS) == ["social_preservation", "social_preservation_pending", "townscape", "townscape_pending"]
    assert all("{fetch_date}" in v["as_of"] for v in OVERLAYS.values())
    assert "{fetch_date}" in INDICATORS[0].as_of and INDICATORS[0].as_of.endswith(f" · {TEXTS['core.z22_as_of']}")
