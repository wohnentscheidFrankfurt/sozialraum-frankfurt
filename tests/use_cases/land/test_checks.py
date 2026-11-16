from shapely.geometry import box

from pipeline.use_cases.land.checks import check_values
from pipeline.use_cases.land.model import Zone


def _zones(n):
    return [Zone(box(0, 0, 1, 1), 1.0, "W", str(i)) for i in range(n)]


def test_check_values_names_the_count_and_warns_above_two_percent():
    values = {str(i): (1.0, "01.01.2026") for i in range(98)}
    c = check_values(_zones(100), values)
    assert (c.status, c.text) == ("OK", "98 of 100 zones with a value of 01.01.2026")
    assert check_values(_zones(100), {k: v for k, v in values.items() if k != "0"}).status == "WARN"


def test_check_values_fails_on_another_stichtag():
    values = {"0": (1.0, "01.01.2026"), "1": (1.0, "01.01.2024")}
    c = check_values(_zones(2), values)
    assert c.status == "FAIL" and "01.01.2024" in c.text
