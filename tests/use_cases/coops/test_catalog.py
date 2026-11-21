from pipeline.use_cases.coops.catalog import INDICATORS as BY_LANGUAGE, T

INDICATORS = BY_LANGUAGE["de"]


def test_coop_indicator_lives_here():
    assert [k.id for k in INDICATORS] == ["OWN_COOP"]
    assert "{high_OWN_COOP}" in INDICATORS[0].uncertainty and INDICATORS[0].estimate
    assert INDICATORS[0].calc == ""  # the worked example is the Rechnung


def test_coop_example_riederwald():
    from pipeline.use_cases.coops.catalog import coop_calc_example
    row = {"counted_2011": 712.0, "gap_2011": 155.9, "estimate_2022": 0.0, "coop_value": 867.9}
    e = coop_calc_example("Riederwald", row, 2482.0, 34.97, T["de"])
    assert [r.number for r in e.rows] == [712, 156, 868, 2482, 35.0]
    assert [r.op for r in e.rows] == ["", "+", "", "÷", ""]
    assert (e.rows[3].op, e.rows[3].number, e.rows[3].decimals) == ("÷", 2482, 0)
    assert e.rows[2].total and e.rows[2].estimate and e.rows[2].text
    assert e.rows[-1].unit == "%"


def test_coop_example_with_estimate_from_buildings():
    from pipeline.use_cases.coops.catalog import coop_calc_example
    row = {"counted_2011": 100.0, "gap_2011": 20.0, "estimate_2022": 33.0, "coop_value": 153.0}
    e = coop_calc_example("X", row, 1000.0, 15.3, T["de"])
    assert [r.number for r in e.rows] == [100, 20, 33, 153, 1000, 15.3]
    # the estimate from the buildings of 2022 is a third added row
    assert [r.op for r in e.rows] == ["", "+", "+", "", "÷", ""] and e.rows[2].text
