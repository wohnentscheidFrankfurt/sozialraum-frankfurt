from pipeline.shared.core.checks import FAIL, OK
from pipeline.use_cases.election.checks import check_election_sums, check_gazette
from pipeline.use_cases.election.sources import result_row

CITY = result_row({"gebiet-name": "x", "A": "513170", "B": "254377", "D": "22300148", "D1": "5574438", "D2": "0"})


def test_check_election_sums():
    parts = [result_row({"gebiet-name": "x", "A": "500000", "B": "254377", "D": "22300148", "D1": "5574438", "D2": "0"}),
             result_row({"gebiet-name": "x", "A": "13170", "B": "0", "D": "0", "D1": "0", "D2": "0"})]
    assert check_election_sums(parts, CITY).status == OK
    parts[1]["eligible"] = 1
    c = check_election_sums(parts, CITY)
    assert c.status == FAIL and "eligible" in c.text


def test_check_gazette():
    text = "Wahlberechtigte 513.170 Wähler 254.377 gültige 22.300.148 CDU 5.574.438"
    assert check_gazette(CITY, text).status == OK
    assert check_gazette(CITY, text.replace("5.574.438", "5.574.439")).status == FAIL
    assert check_gazette(CITY, None).status == FAIL
