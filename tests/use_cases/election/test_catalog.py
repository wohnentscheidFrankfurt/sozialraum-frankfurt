from pipeline.use_cases.election.catalog import INDICATORS, election_indicators
from pipeline.use_cases.election.model import THRESHOLD


def test_election_catalog_has_the_fixed_entries_and_one_per_list():
    assert [k.id for k in INDICATORS] == ["ELEC_STRONGEST", "ELEC_TURNOUT", "ELEC_VOTERS"]
    shares = election_indicators([{"key": "ELEC_CDU", "name": "CDU", "color": "#000000"}])
    assert [k.id for k in shares] == ["ELEC_STRONGEST", "ELEC_TURNOUT", "ELEC_VOTERS", "ELEC_CDU"]


def test_election_indicators_are_quarter_indicators_with_their_ramps():
    w = election_indicators([{"name": "CDU", "key": "ELEC_CDU", "color": "#1d1d1b"}])
    assert [k.id for k in w] == ["ELEC_STRONGEST", "ELEC_TURNOUT", "ELEC_VOTERS", "ELEC_CDU"] and w[3].levels == ("quarter",)
    assert w[3].ramp == "color:#1d1d1b" and w[0].type == "category"


def test_numbers_in_the_protocols_follow_the_code():
    lists = [{"name": "Sonstige", "key": "ELEC_OTHER", "color": "#999"}]
    k = {x.id: x for x in election_indicators(lists)}
    assert f" {THRESHOLD:.0f} % " in k["ELEC_OTHER"].calc


def test_voters_is_a_count_of_the_turnout_without_layer_and_criterion():
    k = {x.id: x for x in election_indicators([])}
    v, t = k["ELEC_VOTERS"], k["ELEC_TURNOUT"]
    assert (v.unit, v.levels, v.decimals) == ("Wählende", ("quarter",), 0)
    assert v.source == t.source and v.as_of == t.as_of
    assert not v.layer and not v.criterion and not v.rule
    assert v.count_of == "ELEC_TURNOUT" and v.count_total == "ELEC_ELIGIBLE" and v.section == "election"
