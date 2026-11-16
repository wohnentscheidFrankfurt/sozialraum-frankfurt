import re

import pytest

from pipeline import config
from pipeline.shared.core.indicator import (QUARTERS_RULE, TEST_2011, TIP_DWELLINGS_RULE, Indicator, estimate_backtest,
                                            estimate_range, estimate_up_to, fill, format_de, range_de,
                                            tooltip_rounding)


def test_format_de():
    assert format_de(18.364, 1, "%") == "18,4 %" and format_de(10.583, 2, "€/m²") == "10,58 €/m²"
    assert format_de(69219.4, 0) == "69.219" and format_de(3.5, 1) == "3,5"


def test_indicator_has_uncertainty_but_no_comparison():
    # docs/texts.md, ⓘ protocol: no line Abgleich, the checks hold it
    k = Indicator("X", "t", "g", "%", ("quarter",), "s", "a", "c")
    assert k.uncertainty == "" and not hasattr(k, "comparison") and not hasattr(k, "accuracy")


@pytest.mark.parametrize("low, high, decimals, text", [
    (0.57, 8.82, 1, "0,6 bis 8,8"),  # ABG und NH: half range differs per Stadtteil
    (3.5, 3.5, 1, "3,5"),  # fixed points: one number
    (2.0, 2.0, 1, "2"),  # no ",0", as the survey writes „±4 bis 4,5“
    (0.0, 2.14, 1, "0 bis 2,1"),  # Genossenschaften: a Stadtteil with counted dwellings only
    (0.04, 0.049, 1, "0"),  # both round to the same number
    (10.0, 250.0, 0, "10 bis 250"),  # dwellings
    (1000.0, 1250.0, 0, "1.000 bis 1.250"),
])
def test_range_de(low, high, decimals, text):
    assert range_de(low, high, decimals) == text


def test_estimate_texts():
    """docs/texts.md, Lines: plain sentences, numbers as placeholders."""
    texts = {"{range_OWN_PUBLIC} Prozentpunkte": estimate_range("OWN_PUBLIC"),
             "{range_OWN_PUBLIC_DWELLINGS} Wohnungen": estimate_range("OWN_PUBLIC_DWELLINGS", "Wohnungen"),
             "{high_OWN_COOP} Prozentpunkte": estimate_up_to("OWN_COOP"),
             "{high_OWN_STATE} Prozentpunkte": estimate_backtest("OWN_STATE", 40, 45)}
    assert all(number in text for number, text in texts.items())
    assert all(t[0].isupper() and t.endswith(".") for t in [*texts.values(), QUARTERS_RULE])
    backtest = estimate_backtest("OWN_STATE", 40, 45)
    assert backtest.startswith(TEST_2011) and backtest.index("40") < backtest.index("45")


def test_indicator_is_no_estimate_by_default():
    assert Indicator("X", "t", "g", "%", ("quarter",), "s", "a", "c").estimate is False


def test_indicator_is_no_breakdown_by_default():
    k = Indicator("X", "t", "g", "%", ("quarter",), "s", "a", "c")
    assert (k.breakdown_of, k.breakdown_lead) == ("", "")


def test_fill_puts_in_the_names_and_raises_on_an_unknown_one():
    assert fill("Abruf {fetch_date}", {"fetch_date": "8.10.2026"}) == "Abruf 8.10.2026"
    assert fill("Nichts", {}) == "Nichts"
    with pytest.raises(KeyError):
        fill("{x}", {})


def test_fill_leaves_a_literal_brace_alone():
    assert fill("Menge {a, b} und { oder }", {}) == "Menge {a, b} und { oder }"
    assert fill('{"a": 1} {fetch_date}', {"fetch_date": "8.10.2026"}) == '{"a": 1} 8.10.2026'


def test_the_dwellings_rule_names_the_numbers_of_the_tooltip():
    """docs/texts.md, ⓘ protocol: the ⓘ of each ownership layer explains the count as the browser shows it
    (APP.roundTo50 and APP.dwellingsText in web/js/01_base.js): the rounding step, the threshold of the upper end and
    the third of the value."""
    js = (config.WEB / "js" / "01_base.js").read_text(encoding="utf-8")
    step, divisor = re.search(r"APP\.roundTo50 = \(x\) => (\d+) \* Math\.round\(x / (\d+)\)", js).groups()
    threshold = re.search(r"if \(high < (\d+)\)", js).group(1)
    part = re.search(r"high - value <= value / (\d+)", js).group(1)
    assert step == divisor and part == "3"
    assert set(re.findall(r"\d+", TIP_DWELLINGS_RULE)) == {step, threshold}
    assert "Drittel" in TIP_DWELLINGS_RULE  # value / 3


def test_rounding_of_a_count_in_the_tooltip():
    """docs/texts.md, ⓘ protocol: the Regel of the Baujahr and the Leerstand puts in the step and the dwellings."""
    text = tooltip_rounding("<dwellings>", 7)
    assert set(re.findall(r"\d+", text)) == {"7"}
    assert "<dwellings>" in text and "{" not in text
