import pandas as pd
import pytest

from pipeline.use_cases.monitoring.catalog import T
from pipeline.use_cases.monitoring.model import (QUARTER_MIN_COVERAGE, monitoring_by_district, monitoring_city,
                                                 quarter_monitoring)
from pipeline.use_cases.monitoring.sources import monitoring_frame


GROUPS = {"SOC_UNEMPLOYED": "Gruppe_Arbeitslosendichte_%", "SOC_MIN_INCOME": "Gruppe_Mindestsich_%",
          "SOC_INDEX": "Gruppe_Benacht_Index"}


def _monitoring(**columns):
    """One row per unit; the group of each table is the unit itself unless a test sets it."""
    basis = {"Einheit": ["10"], "EW": [100], "HH": [50], "EW15_65": [70], "Mindestsich_%": [5.0],
             "Arbeitslosendichte_%": [3.0], "Benacht_Index": [1.0], "Sozialwhg_%": [1.0]}
    basis |= columns
    rows = len(basis["Einheit"])
    basis = {name: values * rows if len(values) == 1 else values for name, values in basis.items()}
    for column in GROUPS.values():
        basis.setdefault(column, list(basis["Einheit"]))
    return pd.DataFrame(basis)


def test_monitoring_by_district_joins_units_with_weights():
    mon = _monitoring(Einheit=["10", "40/50", "40/50"], EW=[100, 300, 100], HH=[50, 10, 30], EW15_65=[70, 200, 0],
                      **{"Mindestsich_%": [5.0, 12.0, 12.0], "Arbeitslosendichte_%": [3.0, 4.0, 4.0],
                         "Benacht_Index": [1.0, 2.0, 2.0], "Sozialwhg_%": [1.0, 0.0, 4.0]})
    b = monitoring_by_district(monitoring_frame(mon), T["de"]).set_index("district")
    assert b.loc["40/50", "POP_MONITORING"] == 400 and b.loc["40/50", "HOUSEHOLDS"] == 40
    assert b.loc["40/50", "SOC_MIN_INCOME"] == 12.0 and b.loc["10", "SOC_UNEMPLOYED"] == 3.0


def test_monitoring_by_district_has_no_rank_column():
    # the profile no longer shows the rank of the monitoring; it ran opposite to the Benachteiligungsindex
    assert "SOC_RANK" not in monitoring_by_district(monitoring_frame(_monitoring()), T["de"]).columns


def test_monitoring_by_district_without_weight_takes_the_first_value():
    mon = _monitoring(EW=[0], HH=[0], EW15_65=[0], **{"Mindestsich_%": [7.0]})
    assert monitoring_by_district(monitoring_frame(mon), T["de"]).loc[0, "SOC_MIN_INCOME"] == 7.0


def test_quarter_monitoring_weighted():
    situation = pd.DataFrame({"district": ["1", "2"], "POP_MONITORING": [100, 300], "POP_15_65": [50, 50], "HOUSEHOLDS": [10, 30],
                         "SOC_MIN_INCOME": [10.0, 20.0], "SOC_UNEMPLOYED": [2.0, 4.0]})
    s = quarter_monitoring(situation, {"1": "Nied", "2": "Nied"}).set_index("quarter")
    assert s.loc["Nied", "SOC_MIN_INCOME"] == 17.5 and s.loc["Nied", "SOC_UNEMPLOYED"] == 3.0


def test_monitoring_city_has_nothing_for_the_index():
    rows = monitoring_city({"SOC_MIN_INCOME": 17.0, "SOC_UNEMPLOYED": 6.0, "SOC_INDEX": 50.0})
    assert [r["indicator"] for r in rows] == ["SOC_MIN_INCOME", "SOC_UNEMPLOYED"]
    assert {r["kind"] for r in rows} == {"published"}


def test_monitoring_by_district_treats_suppressed_residents_like_zero():
    # districts 40 and 592 have no EW, HH and EW15_65 in the source (suppressed)
    mon = _monitoring(Einheit=["40", "50"], EW=[float("nan"), 200], HH=[float("nan"), 80], EW15_65=[float("nan"), 120],
                      **{"Mindestsich_%": [9.0, 11.0], "Arbeitslosendichte_%": [3.0, 5.0]})
    b = monitoring_by_district(monitoring_frame(mon), T["de"]).set_index("district")
    assert b.loc["40", "POP_MONITORING"] == 0 and b.loc["40", "SOC_MIN_INCOME"] == 9.0  # no weight: the first value
    assert b.loc["50", "POP_MONITORING"] == 200 and b.loc["50", "HOUSEHOLDS"] == 80


def _shared(group, units=("202", "203", "213"), indicator="SOC_UNEMPLOYED", **groups):
    mon = _monitoring(Einheit=list(units), **{GROUPS[indicator]: [group] * len(units)} | groups)
    return monitoring_by_district(monitoring_frame(mon), T["de"]).set_index("district")[f"{indicator}_SHARED"]


def test_shared_value_names_all_members():
    shared = _shared("202/203/213")
    assert shared.tolist() == ["202, 203 und 213"] * 3
    mon = _monitoring(Einheit=["202", "203", "213", "204"],
                      **{GROUPS["SOC_UNEMPLOYED"]: ["202/203/213"] * 3 + ["204"]})
    b = monitoring_by_district(monitoring_frame(mon), T["de"]).set_index("district")["SOC_UNEMPLOYED_SHARED"]
    assert b["202"] == "202, 203 und 213" and pd.isna(b["204"])  # pandas stores a missing string as NaN


def test_shared_value_is_none_for_the_unit_itself_and_for_every_indicator():
    mon = _monitoring(Einheit=["424", "425"], **{GROUPS["SOC_MIN_INCOME"]: ["424/25", "424/25"]})
    b = monitoring_by_district(monitoring_frame(mon), T["de"]).set_index("district")
    assert b["SOC_MIN_INCOME_SHARED"].tolist() == ["424 und 425"] * 2
    assert b["SOC_UNEMPLOYED_SHARED"].tolist() == [None, None]


def test_shared_value_across_merged_unit():
    group = "323/25/26/27/28/29"
    mon = _monitoring(Einheit=["323/325/327/328/329", "326"], **{GROUPS["SOC_UNEMPLOYED"]: [group, group]})
    b = monitoring_by_district(monitoring_frame(mon), T["de"]).set_index("district")["SOC_UNEMPLOYED_SHARED"]
    assert b.tolist() == ["323, 325, 326, 327, 328 und 329"] * 2


def test_shared_value_is_none_where_the_unit_is_the_whole_group():
    mon = _monitoring(Einheit=["40/50/60"], **{GROUPS["SOC_UNEMPLOYED"]: ["40/50/60"]})
    assert monitoring_by_district(monitoring_frame(mon), T["de"]).loc[0, "SOC_UNEMPLOYED_SHARED"] is None


def test_empty_group_is_not_shared():
    mon = _monitoring(Einheit=["326", "327"], **{GROUPS["SOC_MIN_INCOME"]: [float("nan"), "327"]})
    b = monitoring_by_district(monitoring_frame(mon), T["de"]).set_index("district")["SOC_MIN_INCOME_SHARED"]
    assert b.tolist() == [None, None]


def test_unknown_group_member_stops():
    with pytest.raises(ValueError, match="999"):
        _shared("202/999", units=("202",))


def test_group_label_notation_does_not_matter():
    # table 12 prints 591/92, table 28 prints 591/592
    mon = _monitoring(Einheit=["591", "592"], **{GROUPS["SOC_UNEMPLOYED"]: ["591/92"] * 2,
                                                  GROUPS["SOC_INDEX"]: ["591/592"] * 2})
    b = monitoring_by_district(monitoring_frame(mon), T["de"])
    assert b["SOC_UNEMPLOYED_SHARED"].tolist() == ["591 und 592"] * 2


def test_quarter_mean_needs_95_percent():
    assert QUARTER_MIN_COVERAGE == 0.95

    def mean(missing_weight):
        situation = pd.DataFrame({"district": ["1", "2"], "POP_MONITORING": [100 - missing_weight, missing_weight],
                                  "POP_15_65": [100 - missing_weight, missing_weight], "HOUSEHOLDS": [1, 1],
                                  "SOC_MIN_INCOME": [10.0, None], "SOC_UNEMPLOYED": [2.0, None]})
        return quarter_monitoring(situation, {"1": "Nied", "2": "Nied"}).set_index("quarter").loc["Nied"]
    assert mean(5)["SOC_MIN_INCOME"] == 10.0 and mean(5)["SOC_UNEMPLOYED"] == 2.0
    assert pd.isna(mean(6)["SOC_MIN_INCOME"]) and pd.isna(mean(6)["SOC_UNEMPLOYED"])
