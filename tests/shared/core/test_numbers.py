import pytest

from pipeline.shared.core.numbers import format_number, format_range


def test_format_number_de_and_en():
    assert format_number(18.44, 1, "%") == "18,4 %"
    assert format_number(18.44, 1, "%", "en") == "18.4%"
    assert format_number(69219, 0) == "69.219"
    assert format_number(69219, 0, lang="en") == "69,219"
    assert format_number(1200, 0, "€") == "1.200 €"
    assert format_number(1200, 0, "€", "en") == "€1,200"
    assert format_number(5, 0, "m", "en") == "5 m"


@pytest.mark.parametrize("low, high, decimals, de, en", [
    (2.0, 2.0, 1, "2", "2"),  # no trailing zero decimal
    (0.04, 0.049, 1, "0", "0"),  # both round to the same number
    (1000.0, 1250.0, 0, "1.000 bis 1.250", "1,000 to 1,250"),
    (10.0, 250.0, 0, "10 bis 250", "10 to 250"),
])
def test_format_range_edge_cases(low, high, decimals, de, en):
    assert format_range(low, high, decimals) == de
    assert format_range(low, high, decimals, "en") == en


def test_format_range_de_and_en():
    assert format_range(0.6, 8.8) == "0,6 bis 8,8"
    assert format_range(0.6, 8.8, lang="en") == "0.6 to 8.8"
    assert format_range(3.5, 3.5) == "3,5"
    assert format_range(3.5, 3.5, lang="en") == "3.5"
    assert format_range(3.0, 3.01) == "3"
    assert format_range(3.0, 3.01, lang="en") == "3"
