from pipeline.shared.core.indicator import Z22_AS_OF
from pipeline.use_cases.protection.catalog import INDICATORS, OVERLAYS


def test_protection_catalog_and_overlays():
    assert [k.id for k in INDICATORS] == ["PROT_SOCIAL"]
    assert list(OVERLAYS) == ["social_preservation", "social_preservation_pending", "townscape", "townscape_pending"]
    assert all("{fetch_date}" in v["as_of"] for v in OVERLAYS.values())
    assert "{fetch_date}" in INDICATORS[0].as_of and INDICATORS[0].as_of.endswith(f" · {Z22_AS_OF}")
