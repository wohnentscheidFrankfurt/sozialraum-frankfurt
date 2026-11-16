import pytest

from pipeline.shared.core.calc_example import CalcExample, Row, example_payload, require_example_quarters


def test_payload_is_a_plain_dict():
    e = CalcExample("Ginnheim", (Row("", 102, 0, "Gebäude"), Row("÷", 8186, 0, "bekannt", total=True)))
    p = example_payload(e)
    assert p["area"] == "Ginnheim" and p["rows"][1] == {"op": "÷", "number": 8186, "decimals": 0, "text": "bekannt",
                                                        "total": True, "estimate": False, "unit": ""}


def test_require_example_quarters_raises_on_an_unknown_stadtteil():
    require_example_quarters(["Gallus"], {"OWN_PUBLIC": "Gallus"})
    with pytest.raises(ValueError, match="no Stadtteil Atlantis for the example of X"):
        require_example_quarters(["Gallus"], {"X": "Atlantis"})


def test_an_example_may_carry_its_own_label():
    """The browser writes „Rechnung am Beispiel <area>“, or the label where one is set (view Miete)."""
    e = CalcExample("Mindestlohn", (Row("", 2222, 0, "Bruttolohn", unit="€"),), label="Nettolohn am Beispiel")
    assert example_payload(e)["label"] == "Nettolohn am Beispiel"
    assert example_payload(CalcExample("Gallus", ()))["label"] == ""


def test_rows_may_carry_euros():
    """A worked example of money (survey) writes „€“ on its rows; the docstring of Row names the allowed units."""
    assert "€" in Row.__doc__ and "%" in Row.__doc__
    assert Row("", 550, 0, "Kaltmiete", unit="€").unit == "€"
