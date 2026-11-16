import pandas as pd

from pipeline.use_cases.ownership_cells.model import GROUPS
from pipeline.use_cases.ownership_shares.checks import (check_city_shares, check_city_within_range,
                                                        check_dwellings, check_dwellings_total, check_examples, check_ownership_shares, check_ranges,
                                                        check_rest)
from pipeline.shared.zensus.model import CLASSES


def test_check_ownership_shares():
    groups = ["OWN_PUBLIC", "OWN_COOP", "OWN_COMPANY", "OWN_PERSON", "OWN_STATE", "OWN_NONPROFIT"]
    q = pd.DataFrame([{"name": "A", **dict(zip(groups, [20.0, 10.0, 30.0, 39.95, 0.0, 0.0]))}])
    assert check_ownership_shares(q).status == "OK"
    bad = check_ownership_shares(q.assign(OWN_COOP=10.2))
    assert bad.status == "FAIL" and "A" in bad.text


def test_check_dwellings():
    groups = ["OWN_PUBLIC", "OWN_COOP", "OWN_COMPANY", "OWN_PERSON", "OWN_STATE", "OWN_NONPROFIT"]
    counts = [200.0, 100.0, 300.0, 400.0, 0.0, 0.0]
    q = pd.DataFrame([{"name": "A", **dict(zip(groups, [20.0, 10.0, 30.0, 40.0, 0.0, 0.0])),
                       **{f"{g}_DWELLINGS": c for g, c in zip(groups, counts)}}])
    assert check_dwellings(q).status == "OK"
    bad = check_dwellings(q.assign(OWN_PERSON_DWELLINGS=404.0))
    assert bad.status == "FAIL" and "A" in bad.text


def test_check_dwellings_total():
    groups = ["OWN_PUBLIC", "OWN_COOP", "OWN_COMPANY", "OWN_PERSON", "OWN_STATE", "OWN_NONPROFIT"]
    q = pd.DataFrame([{"id": "a", "name": "A", **{f"{g}_DWELLINGS": c for g, c in
                                                  zip(groups, [200.0, 100.0, 300.0, 400.0, 0.0, 0.0])}}])
    total = pd.DataFrame({"id": ["a"], "total": [1000.0]})
    assert check_dwellings_total(q, total).status == "OK"
    assert check_dwellings_total(q, total.assign(total=1000.4)).status == "OK"
    bad = check_dwellings_total(q, total.assign(total=1001.0))
    assert bad.status == "FAIL" and "A" in bad.text
    assert check_dwellings_total(q, total).name == "Ownership: the six counts add up to all dwellings"


def test_check_city_shares_one_per_group():
    table = {k: 10 for k in CLASSES}
    city = {g: 100 * 10 * len(classes) / 80 for g, classes in GROUPS.items()}
    checks = check_city_shares(city, table)
    assert [c.name for c in checks] == [f"Ownership: city share {g} against 4000W" for g in GROUPS]
    assert {c.status for c in checks} == {"OK"}


def test_check_city_shares_only_warn():
    table = {k: 10 for k in CLASSES}
    city = {g: 100.0 for g in GROUPS}
    assert {c.status for c in check_city_shares(city, table)} == {"WARN"}


def test_check_rest():
    ok = check_rest(pd.DataFrame({"name": ["A", "B"], "rest": [5.0, 0.0]}))
    bad = check_rest(pd.DataFrame({"name": ["A", "B"], "rest": [5.0, -1.0]}))
    assert (ok.name, ok.status) == ("Ownership: rest after ABG, NH and Genossenschaften not negative", "OK")
    assert bad.status == "FAIL" and "['B']" in bad.text


def _quarters(value, low, high):
    return pd.DataFrame({"id": ["A"], "name": ["Alt"], "OWN_COOP": [value], "OWN_COOP_LOW": [low],
                         "OWN_COOP_HIGH": [high]})


def test_check_ranges_the_range_at_the_value_is_value_plus_minus_the_half_range():
    halves = pd.DataFrame({"id": ["A"], "OWN_COOP": [1.5]})
    ok = check_ranges(_quarters(1.0, 0.0, 2.5), halves)  # the lower end stops at 0
    assert (ok.name, ok.status) == ("Ownership: range at the value = value ± half range of the ⓘ", "OK")
    assert ok.text == "1 Stadtteile; half range in points: OWN_COOP 1.50"
    bad = check_ranges(_quarters(1.0, 0.0, 2.0), halves)
    assert bad.status == "FAIL" and "OWN_COOP in ['Alt']" in bad.text


def test_check_ranges_name_the_widest_stadtteil_where_the_half_range_differs():
    q = pd.concat([_quarters(1.0, 0.0, 2.5), _quarters(5.0, 4.5, 5.5).assign(id="B", name="Bon")])
    ok = check_ranges(q, pd.DataFrame({"id": ["A", "B"], "OWN_COOP": [1.5, 0.5]}))
    assert ok.status == "OK" and ok.text.endswith("OWN_COOP 0.50 to 1.50 (widest Alt)")


def test_check_ranges_fail_on_a_value_without_half_range_or_a_missing_stadtteil():
    bad = check_ranges(_quarters(1.0, 0.0, 2.5), pd.DataFrame({"id": ["A"], "OWN_COOP": [None]}))
    assert bad.status == "FAIL" and "OWN_COOP in ['Alt']" in bad.text
    bad = check_ranges(_quarters(1.0, 0.0, 2.5), pd.DataFrame({"id": ["B"], "OWN_COOP": [1.5]}))
    assert bad.status == "FAIL" and "no half range for ['Alt']" in bad.text


def test_check_ranges_ignore_stadtteile_without_a_value():
    halves = pd.DataFrame({"id": ["A"], "OWN_COOP": [None]})
    assert check_ranges(_quarters(None, None, None), halves).status == "OK"


def test_check_ranges_tolerate_the_rounding_of_the_stored_table():
    halves = pd.DataFrame({"id": ["A"], "OWN_COOP": [1.5]})
    assert check_ranges(_quarters(3.0, 1.5 + 1e-9, 4.5), halves).status == "OK"


def test_check_city_within_range():
    table = {k: 10 for k in CLASSES}  # every group of one class has 12.5 %
    city = {g: 100 * 10 * len(classes) / 80 for g, classes in GROUPS.items()} | {"OWN_COOP": 13.5}
    halves = {g: 1.0 for g in GROUPS}
    ok = check_city_within_range(city, halves, table)
    assert (ok.name, ok.status) == ("Ownership: share of 4000W within the range of the city value", "OK")
    assert "OWN_COOP 13.50 against 12.50 (± 1.00)" in ok.text
    bad = check_city_within_range(city | {"OWN_COOP": 13.6}, halves, table)
    assert bad.status == "WARN" and bad.text.startswith("outside: OWN_COOP")



def test_check_examples_names_the_examples_of_own_company():
    from pipeline.use_cases.ownership_shares.catalog import EXAMPLES
    texts = {e["source"]: " ".join(e["phrases"]) for e in EXAMPLES}
    c = check_examples(texts)
    assert c.name == "Ownership: examples in the ⓘ of OWN_COMPANY stand in their sources" and c.status == "OK"
