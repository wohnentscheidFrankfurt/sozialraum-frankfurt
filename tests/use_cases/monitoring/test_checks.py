import pandas as pd

from pipeline.shared.core.checks import FAIL, OK
from pipeline.use_cases.monitoring.checks import check_monitoring


def test_check_monitoring_only_for_the_indicators_of_the_map():
    # SH_SHARE_MONITORING is in the reference file only for the social housing check
    by_district = pd.DataFrame({"SOC_MIN_INCOME": [11.0, 12.0], "POP_MONITORING": [100, 100],
                                "SOC_UNEMPLOYED": [4.0, 5.8], "POP_15_65": [50, 50]})  # recomputed: 11.5 and 4.9
    checks = check_monitoring(by_district, {"SOC_MIN_INCOME": 11.3, "SOC_UNEMPLOYED": 4.5, "SH_SHARE_MONITORING": 7.0})
    assert [c.name for c in checks] == ["Monitoring: SOC_MIN_INCOME recomputed", "Monitoring: SOC_UNEMPLOYED recomputed"]
    assert [c.status for c in checks] == [OK, FAIL]
