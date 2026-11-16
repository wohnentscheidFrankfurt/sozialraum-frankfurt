from pipeline.shared.core.checks import OK, WARN
from pipeline.use_cases.protection.checks import check_social_preservation


def test_check_social_preservation():
    assert check_social_preservation({"E9", "E52"}, {"E9", "E52"}).status == OK
    c = check_social_preservation({"E9", "E60"}, {"E9", "E52"})
    assert c.status == WARN and "E60" in c.text and "E52" in c.text
