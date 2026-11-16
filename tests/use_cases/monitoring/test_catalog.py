from pipeline.map.assembly.catalog import CATALOG
from pipeline.use_cases.monitoring.catalog import MON_RULE
from pipeline.use_cases.monitoring.model import QUARTER_MIN_COVERAGE


def test_monitoring_protocols_follow_the_report():
    k = {x.id: x for x in CATALOG}
    assert all(k[s].as_of == "Ende 2022" for s in ("SOC_MIN_INCOME", "SOC_UNEMPLOYED", "SOC_INDEX"))


def test_monitoring_indicators_share_one_rule():
    k = {x.id: x for x in CATALOG}
    assert all(k[s].rule == MON_RULE for s in ("SOC_MIN_INCOME", "SOC_UNEMPLOYED", "SOC_INDEX"))
    # the rule names the share of residents a Stadtteil may miss
    assert f" {round((1 - QUARTER_MIN_COVERAGE) * 100)} % " in MON_RULE


def test_the_deprivation_index_is_a_rank_of_114_without_decimals():
    index = next(x for x in CATALOG if x.id == "SOC_INDEX")
    assert index.rank == 114 and index.decimals == 0
    # the legend and the ⓘ name the range of the rank
    assert f"1 bis {index.rank}" in index.legend_note and f"1 bis {index.rank}" in index.calc
