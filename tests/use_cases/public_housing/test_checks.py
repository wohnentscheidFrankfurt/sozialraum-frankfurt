import pandas as pd

from pipeline.shared.core.checks import FAIL, OK, WARN
from pipeline.use_cases.public_housing.checks import check_public_quarters, check_secrecy_fill, public_checks


def test_check_secrecy_fill():
    c = check_secrecy_fill(4922.0, 5047)
    assert c.status == OK and c.name == "Public housing: secrecy 2011 filled from 2022" and "4,922 of 5,047 (98 %)" in c.text
    assert check_secrecy_fill(4038, 5047).status == OK and check_secrecy_fill(4000, 5047).status == WARN
    assert check_secrecy_fill(5600, 5047).status == WARN and check_secrecy_fill(0, 0).status == OK


def test_check_public_quarters():
    q = pd.DataFrame({"quarter": ["A", "B"], "public_value": [100.0, 0.0], "public_half": [10.0, 0.0]})
    assert check_public_quarters(q).status == OK
    bad = check_public_quarters(q.assign(public_half=[10.0, -1.0]))
    assert bad.status == FAIL and "B" in bad.text


def test_public_checks_keep_their_names():
    public = pd.DataFrame({"quarter": ["Gallus"], "public_value": [69000.0], "public_half": [1.0],
                           "abg_value": [5600.0], "fill_2011": [5000.0]})
    names = [c.name for c in public_checks(public, 69558, {"abg_group_2022": 54122, "abg_gallus_chronicle_2015": 5700},
                                           5047)]
    assert names == ["Public housing: Frankfurt against 4000W-2002 (Kommune)",
                     "ABG: city total against group report (31.12.2022)", "ABG: Gallus against ABG chronicle (2015)",
                     "Public housing: secrecy 2011 filled from 2022", "Public housing: value and range not negative",
                     "Public housing: tolerance of 10.10.2026"]


def test_public_tolerance_ok_down_to_the_accepted_35_of_41():
    def status(passing: int) -> str:
        halves = [100.0] * passing + [500.0] * (41 - passing)
        public = pd.DataFrame({"quarter": ["Gallus"] + [f"Q{i}" for i in range(40)], "public_value": [1000.0] * 41,
                               "public_half": halves, "abg_value": [100.0] * 41, "fill_2011": [100.0] * 41})
        checks = public_checks(public, 41000, {"abg_group_2022": 4100, "abg_gallus_chronicle_2015": 100}, 4100)
        return next(c.status for c in checks if c.name == "Public housing: tolerance of 10.10.2026")
    assert (status(35), status(34)) == (OK, WARN)
