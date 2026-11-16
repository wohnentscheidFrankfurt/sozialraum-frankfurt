from pipeline.shared.core.indicator import QUARTERS_RULE, TIP_DWELLINGS_RULE
from pipeline.use_cases.public_housing.catalog import INDICATORS, PUBLIC_COUNTING_RULE


def test_public_protocol():
    k = {x.id: x for x in INDICATORS}
    p = k["OWN_PUBLIC"]
    assert "PUBLIC_DWELLINGS" not in k
    assert "{range_OWN_PUBLIC}" in p.uncertainty and p.estimate


def test_public_rechnung_is_the_worked_example_alone():
    assert {x.id: x for x in INDICATORS}["OWN_PUBLIC"].calc == ""


def test_public_rule_holds_the_counting_rule_between_the_shared_phrases():
    k = {x.id: x for x in INDICATORS}
    assert k["OWN_PUBLIC"].rule == f"{QUARTERS_RULE} {PUBLIC_COUNTING_RULE} {TIP_DWELLINGS_RULE}"


NIEDERRAD = {"scaled_2011": 3336.07, "factor": 0.9098, "abg_scaled": 1896.24, "nh_scaled": 1138.81, "new": 319.70,
             "research_new": 405.0, "public_value": 4504.14}  # the build of 22 Oct 2026


def test_public_example_niederrad():
    from pipeline.use_cases.public_housing.catalog import public_calc_example
    e = public_calc_example("Niederrad", NIEDERRAD, 15389.0, 29.27)
    assert [r.op for r in e.rows] == ["", "×", "", "+", "+", "", "÷", ""]
    assert [r.number for r in e.rows] == [3336, 0.91, 3035, 744, 725, 4504, 15389, 29.3]
    assert all(r.text for i, r in enumerate(e.rows) if i != 2)
    assert (e.rows[6].op, e.rows[6].number, e.rows[6].decimals) == ("÷", 15389, 0)
    assert e.rows[2].number + e.rows[3].number + e.rows[4].number == e.rows[5].number  # the fills close the sum
    assert all(r.estimate for r in e.rows[:6] if r.op != "×")  # the 2011 count includes the filled secrecy gap
    assert e.rows[2].total and not e.rows[2].text
    assert e.rows[5].total and "2022" in e.rows[5].text
    assert e.rows[-1].unit == "%"

