import pandas as pd
import pytest

from pipeline.use_cases.coops.model import HALF_ESTIMATED, coop_cells, coops_by_quarter
from pipeline.shared.zensus.model import CLASSES


def _cell(quarter="Bornheim", dwellings=100, dw_coop=0.0, total_2011=0, bld=None, dw_2011=None):
    row = {"quarter": quarter, "dwellings": dwellings, "dw_coop": dw_coop, "dw_total_2011": total_2011,
           **{f"bld_{k}": 0 for k in CLASSES}, **{f"dw_{k}_2011": 0 for k in CLASSES}}
    row |= {f"bld_{k}": v for k, v in (bld or {}).items()} | {f"dw_{k}_2011": v for k, v in (dw_2011 or {}).items()}
    return row


def test_counted_cell_keeps_its_2011_dwellings_and_gets_its_share_of_the_secrecy_gap():
    # 2011: 60 coop, 30 person, 10 without owner; 2022: coop holds 40 of 100 dwellings
    cells = pd.DataFrame([_cell(dw_coop=40.0, total_2011=100, bld={"coop": 2, "person": 1},
                                dw_2011={"coop": 60, "person": 30})])
    p = coop_cells(cells).iloc[0]
    assert (p["counted_2011"], p["gap_2011"], p["estimate_2022"]) == (60, pytest.approx(10 * 0.4), 0)


def test_no_gap_share_where_the_cell_has_no_owner_in_2022():
    cells = pd.DataFrame([_cell(dw_coop=0.0, total_2011=100, dw_2011={"coop": 60})])
    assert coop_cells(cells).iloc[0]["gap_2011"] == 0


def test_cell_without_coop_in_2011_takes_the_estimate_2022():
    cells = pd.DataFrame([_cell(dw_coop=25.0, total_2011=80, bld={"coop": 1}, dw_2011={"person": 80})])
    p = coop_cells(cells).iloc[0]
    assert (p["counted_2011"], p["gap_2011"], p["estimate_2022"]) == (0, 0, 25.0)


def test_cell_without_dwellings_gives_no_share():
    cells = pd.DataFrame([_cell(dwellings=0, total_2011=10, bld={"coop": 1}, dw_2011={"coop": 5})])
    assert coop_cells(cells).iloc[0]["gap_2011"] == 0


def test_sum_and_range_per_stadtteil():
    cells = pd.DataFrame([_cell(dw_coop=40.0, total_2011=100, bld={"coop": 2}, dw_2011={"coop": 60, "person": 30}),
                          _cell(dw_coop=25.0, total_2011=80, bld={"coop": 1}, dw_2011={"person": 80}),
                          _cell(quarter="Harheim", dw_coop=0.0, bld={"person": 3})])
    q = coops_by_quarter(coop_cells(cells)).set_index("quarter")
    assert list(q.index) == ["Bornheim", "Harheim"]
    assert q.loc["Bornheim", "coop_value"] == pytest.approx(60 + 4 + 25)
    assert q.loc["Bornheim", "coop_half"] == pytest.approx(HALF_ESTIMATED * (4 + 25))  # no range on the counted part
    assert (q.loc["Harheim", "coop_value"], q.loc["Harheim", "coop_half"]) == (0, 0)
    assert HALF_ESTIMATED == 0.34


# scenarios of a Stadtteil (docs/data-rules.md, Uncertainty): the range covers only the estimated parts b and c
COOP_SCENARIOS = [
    ("counted only", {"counted_2011": 500.0, "gap_2011": 0.0, "estimate_2022": 0.0}, 500.0, 0.0),
    ("gap of 2011 only", {"counted_2011": 0.0, "gap_2011": 100.0, "estimate_2022": 0.0}, 100.0, 34.0),
    ("estimate 2022 only", {"counted_2011": 0.0, "gap_2011": 0.0, "estimate_2022": 50.0}, 50.0, 17.0),
    # Bornheim-like: 80 % counted, the half range is 34 % of the rest
    ("mostly counted", {"counted_2011": 800.0, "gap_2011": 120.0, "estimate_2022": 80.0}, 1000.0, 68.0),
    ("no coop", {"counted_2011": 0.0, "gap_2011": 0.0, "estimate_2022": 0.0}, 0.0, 0.0),
]


@pytest.mark.parametrize("scenario, parts, value, half", COOP_SCENARIOS, ids=[s for s, *_ in COOP_SCENARIOS])
def test_coop_scenario(scenario, parts, value, half):
    q = coops_by_quarter(pd.DataFrame([{"quarter": "X", **parts}])).iloc[0]
    assert (q["coop_value"], q["coop_half"]) == (pytest.approx(value), pytest.approx(half))
