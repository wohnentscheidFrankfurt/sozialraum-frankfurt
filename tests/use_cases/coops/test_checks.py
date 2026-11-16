import pandas as pd

from pipeline.use_cases.coops.checks import coop_checks


def test_coop_checks():
    q = pd.DataFrame({"quarter": ["A", "B"], "coop_value": [6000.0, 7196.0], "coop_half": [100.0, 0.0]})
    checks = coop_checks(q, table_coop=12932)
    assert [(c.name, c.status) for c in checks] == [
        ("Coops: Frankfurt against 4000W-2002 (Wohnungsgenossenschaft)", "OK"),
        ("Coops: value and range not negative", "OK"), ("Coops: tolerance of 10.10.2026", "OK")]


def test_coop_checks_fail():
    q = pd.DataFrame({"quarter": ["A"], "coop_value": [-1.0], "coop_half": [0.0]})
    assert [c.status for c in coop_checks(q, table_coop=12000)] == ["FAIL", "FAIL", "OK"]
