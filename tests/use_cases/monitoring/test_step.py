import pandas as pd


from pipeline import config
from pipeline.engine.datasets import (MONITORING_BY_DISTRICT, MONITORING_BY_QUARTER, MONITORING_CHECKS, MONITORING_CITY)
from pipeline.use_cases.monitoring.sources import read_monitoring
from pipeline.use_cases.monitoring.step import STEP


def test_monitoring_step_on_a_fake_store(tmp_path, run_step):
    """The step needs nothing from the grid; the area tables are keyed by `id`."""
    units = list(dict.fromkeys(read_monitoring(config.MONITORING_CSV)["unit"]))
    store, _ = run_step(tmp_path, STEP, {}, MONITORING_CSV=config.MONITORING_CSV, DISTRICTS_GML=config.DISTRICTS_GML,
                        MONITORING_CITY_VALUES_CSV=config.MONITORING_CITY_VALUES_CSV)
    by_district, by_quarter = store.read(MONITORING_BY_DISTRICT), store.read(MONITORING_BY_QUARTER)
    assert len(by_district) == len(units) and by_district["id"].tolist() == units
    assert {"POP_MONITORING", "SOC_MIN_INCOME", "SOC_UNEMPLOYED", "SOC_INDEX"} <= set(by_district.columns)
    assert {"SOC_MIN_INCOME_SHARED", "SOC_UNEMPLOYED_SHARED"} <= set(by_district.columns)
    shared = by_district.set_index("id")["SOC_UNEMPLOYED_SHARED"]
    assert shared["202"] == "202, 203 und 213" and shared["326"] == "323, 325, 326, 327, 328 und 329"
    assert len(by_quarter) == 45 and "id" in by_quarter.columns and "quarter" not in by_quarter.columns
    city = {r["indicator"]: r for r in store.read(MONITORING_CITY)}
    assert set(city) == {"SOC_MIN_INCOME", "SOC_UNEMPLOYED"}
    quarters = by_quarter.set_index("id")
    assert pd.isna(quarters.loc["Sachsenhausen-Süd und Flughafen", "SOC_MIN_INCOME"])  # district 326 has no value
    assert quarters["SOC_MIN_INCOME"].notna().sum() == 44
    assert city["SOC_MIN_INCOME"]["kind"] == "published"
    assert [r["status"] for r in store.read(MONITORING_CHECKS)] == ["OK", "OK"]
