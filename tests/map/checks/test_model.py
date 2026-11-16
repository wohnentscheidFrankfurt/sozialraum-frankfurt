import pandas as pd

from pipeline.map.checks.model import report
from pipeline.shared.core.checks import FAIL, OK, Check


def test_report_lists_fail_first():
    t = report([Check("a", OK, "good"), Check("b", FAIL, "bad")], ["## Extra\n"], "2026-10-08")
    assert t.startswith("# Check report 2026-10-08") and t.index("| FAIL") < t.index("| OK") and "## Extra" in t


def test_plausibility_names_highest_and_lowest():
    import pandas as pd
    from pipeline.map.checks.model import plausibility
    districts = pd.DataFrame({"id": [str(i) for i in range(12)], "name": [f"B{i}" for i in range(12)], "small": 0,
                              "SOC_MIN_INCOME": [float(i) for i in range(12)]})
    text = plausibility(districts, [("SOC_MIN_INCOME", "Mindestsicherung")])
    assert "Mindestsicherung" in text and "B11 (11) 11.0" in text and "B0 (0) 0.0" in text


def test_plausibility_without_counts():
    import pandas as pd
    from pipeline.map.checks.model import plausibility
    from pipeline.map.checks.step import PLAUSIBILITY
    districts = pd.DataFrame({"id": [str(i) for i in range(6)], "name": [f"B{i}" for i in range(6)], "small": 0,
                              "OWN_COOP": [float(i) for i in range(6)], "OWN_PUBLIC_DWELLINGS": [100.0 * i for i in range(6)]})
    text = plausibility(districts, PLAUSIBILITY)
    # ownership exists only per Stadtteil (docs/data-rules.md, Level): no ownership share and no count in the district plausibility
    assert not any(i.startswith("OWN_") or i == "OWN_PUBLIC_DWELLINGS" for i, _ in PLAUSIBILITY)
    assert "Genossenschaften" not in text and "Wohnungen" not in text


def test_low_coverage_names_name_and_number():
    import pandas as pd
    from pipeline.map.checks.model import low_coverage
    districts = pd.DataFrame({"id": ["152", "153"], "name": ["Gallus", "Gallus"], "COV_HOU_RENTERS": [40.0, 90.0],
                              "COV_HOU_RENT": [100.0, 100.0], "COV_HOU_VACANT_MARKET": [30.0, 100.0],
                              "COV_HOU_VACANT_ALL": [100.0, 45.0]})
    assert low_coverage(districts) == ["- Gallus (152): COV_HOU_RENTERS 40 %", "- Gallus (152): COV_HOU_VACANT_MARKET 30 %",
                                       "- Gallus (153): COV_HOU_VACANT_ALL 45 %"]


def test_quarters_without_ownership():
    import pandas as pd
    from pipeline.map.checks.model import quarters_without_ownership
    quarters = pd.DataFrame({"id": ["1", "2", "3"], "name": ["A", "B", "C"], "COV_OWN": [45.0, 79.9, 80.0]})
    assert quarters_without_ownership(quarters) == ["- A (1): 55 % without ownership type",
                                                    "- B (2): 20 % without ownership type"]


def test_report_sections_compute_the_share_from_the_rounded_count():
    import pandas as pd
    from pipeline.map.checks.model import report_sections
    districts = pd.DataFrame({"id": ["1"], "name": ["A"], "small": [0], "COV_OWN": [100.0], "POP": [1], "POP_MONITORING": [1],
                              "COV_HOU_RENTERS": [100.0], "COV_HOU_RENT": [100.0],
                              "COV_HOU_VACANT_MARKET": [100.0], "COV_HOU_VACANT_ALL": [100.0]})
    quarters = pd.DataFrame({"id": ["q1", "q2"], "name": ["Gallus", "Bonames"], "COV_OWN": [70.0, 95.0]})
    text = "\n".join(report_sections(9.6, 400, 0.0, 0, districts, quarters, []))
    assert "Stadtteile with less than 80 % assigned dwellings:\n- Gallus (q1): 30 % without ownership type" in text
    assert "the shares OWN_* refer to all dwellings; the four other groups take the unassigned ones in proportion." in text
    assert "10 of 400 dwellings (2.5 %)" in text  # old code: round(9.6) = 10, 10 / 400 = 2.5 %
