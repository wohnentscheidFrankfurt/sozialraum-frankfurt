from pipeline.shared.core.checks import (FAIL, OK, WARN, Check, as_rows, check_agreed_tolerance, check_same_values,
                                         check_tolerance, check_wfs, de_thousands, from_rows, thousands)


def test_number_formats():
    assert thousands(5574438) == "5,574,438" and de_thousands(5574438) == "5.574.438" and thousands(999) == "999"


def test_check_tolerance_writes_english_numbers():
    assert check_tolerance("x", 53739.13, 54122, rel=0.1).text == "is 53,739.13, expected 54,122.00, allowed ± 5,412.20"


def test_check_same_values():
    assert check_same_values("x", {"a": 1, "b": 2}, {"a": 1, "b": 2}).status == OK
    c = check_same_values("x", {"a": 1, "b": 3}, {"a": 1, "b": 2})
    assert c.status == FAIL and "b: 3 against 2" in c.text


def test_check_wfs():
    assert check_wfs("pending_plans.gml", None).status == FAIL and check_wfs("pending_plans.gml", 0).status == FAIL
    assert check_wfs("social_preservation.gml", 1).text == "1 features with an area"


def test_check_tolerance_status():
    assert check_tolerance("x", 101, 100, rel=0.01).status == OK
    assert check_tolerance("x", 102, 100, rel=0.01).status == FAIL
    assert check_tolerance("x", 11.1, 11.3, absolute=0.3, on_failure=WARN).status == OK
    assert check_tolerance("x", 11.7, 11.3, absolute=0.3, on_failure=WARN).status == WARN


def test_check_rows_round_trip():
    checks = [Check("Grid: population", OK, "is 1"), Check("x", FAIL, "y")]
    assert as_rows(checks) == [{"name": "Grid: population", "status": "OK", "text": "is 1"},
                               {"name": "x", "status": "FAIL", "text": "y"}]
    assert from_rows(as_rows(checks)) == checks


def test_check_agreed_tolerance():
    # agreed tolerance: 9 of 10 Stadtteile with at least 200 dwellings of the group within ±15 %
    c = check_agreed_tolerance("Coops: tolerance", [1000.0] * 9 + [400.0, 150.0], [150.0] * 9 + [100.0, 140.0])
    assert (c.name, c.status) == ("Coops: tolerance", OK)
    # the second clause (at most 3 share points in all areas) needs the denominator; not checked here
    assert c.text == ("9 of 10 Stadtteile with at least 200 dwellings within ± 15 % (agreed: 9 of 10; the clause "
                      "„at most 3 share points“ is not checked)")
    assert check_agreed_tolerance("x", [1000.0, 400.0], [150.0, 100.0]).status == WARN  # 1 of 2
    assert check_agreed_tolerance("x", [100.0], [90.0]).status == OK  # no Stadtteil with 200


def test_check_agreed_tolerance_with_an_accepted_share():
    # the user accepted fewer areas (ABG and NH): OK down to that share, WARN below it
    values, halves = [1000.0] * 4, [150.0] * 3 + [300.0]
    c = check_agreed_tolerance("x", values, halves, accepted=(3, 4))
    assert c.status == OK
    assert c.text == ("3 of 4 Stadtteile with at least 200 dwellings within ± 15 % (agreed: 9 of 10; accepted on "
                      "11.10.2026: 3 of 4; the clause „at most 3 share points“ is not checked)")
    assert check_agreed_tolerance("x", values, [150.0] * 2 + [300.0] * 2, accepted=(3, 4)).status == WARN
    # the share counts, not the number: 3 of 5 is below 3 of 4
    assert check_agreed_tolerance("x", [1000.0] * 5, [150.0] * 3 + [300.0] * 2, accepted=(3, 4)).status == WARN


_EXAMPLES = [{"name": "A", "source": "A_PDF", "phrases": ["A hat rund 1.000 Wohnungen", "1. Mai 2026"]},
             {"name": "B", "source": "B_HTML", "phrases": ["B besitzt ein Haus"]}]
_TEXTS = {"A_PDF": "Pressemitteilung 1. Mai 2026 … A hat rund \n1.000 Wohnungen.", "B_HTML": "Text: B  besitzt ein Haus."}


def test_check_examples_finds_every_phrase_in_its_source():
    from pipeline.shared.core.checks import check_examples
    c = check_examples("x", _TEXTS, _EXAMPLES)
    assert c.name == "x" and c.status == OK and "A" in c.text and "B" in c.text


def test_check_examples_fails_on_a_changed_number_or_a_missing_source():
    from pipeline.shared.core.checks import check_examples
    c = check_examples("x", _TEXTS | {"A_PDF": _TEXTS["A_PDF"].replace("1.000", "2.000")}, _EXAMPLES)
    assert c.status == FAIL and "A hat rund 1.000 Wohnungen" in c.text
    assert check_examples("x", {"A_PDF": _TEXTS["A_PDF"]}, _EXAMPLES).status == FAIL


def test_check_examples_names_a_name_with_two_sources_once():
    from pipeline.shared.core.checks import check_examples
    two = _EXAMPLES + [{"name": "A", "source": "B_HTML", "phrases": ["B besitzt ein Haus"]}]
    assert check_examples("x", _TEXTS, two).text == "A, B"
