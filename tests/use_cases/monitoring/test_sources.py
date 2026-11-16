import pandas as pd
import pytest

from pipeline import config
from pipeline.use_cases.monitoring.sources import label_members, monitoring_frame, read_monitoring


@pytest.mark.parametrize("label, members", [("10", (10,)), ("010", (10,)), ("424/25", (424, 425)),
                                           ("591/92", (591, 592)), ("591/592", (591, 592)),
                                           ("323/25/26/27/28/29", (323, 325, 326, 327, 328, 329)),
                                           ("40/50/60", (40, 50, 60))])
def test_label_members(label, members):
    assert label_members(label) == members


def test_monitoring_frame_stops_without_a_group_column():
    raw = pd.DataFrame({"Einheit": ["10"], "Gruppe_Mindestsich_%": ["10"], "Gruppe_Benacht_Index": ["10"]})
    with pytest.raises(ValueError, match="Gruppe_Arbeitslosendichte_%"):
        monitoring_frame(raw)


def test_read_monitoring_keeps_the_group_labels_of_the_source():
    frame = read_monitoring(config.MONITORING_CSV).drop_duplicates("unit").set_index("unit")
    assert frame.loc["40/50/60", "unit_members"] == (40, 50, 60)
    assert frame.loc["10", "unemployment_group"] == (10,)  # printed "010"
    assert frame.loc["326", "min_income_group"] is None  # table 14 has no row for 326
    assert "rank" not in frame.columns
