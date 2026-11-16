from pipeline import config
from pipeline.shared.readers.reference import read_column, read_reference


def test_read_reference(tmp_path):
    path = tmp_path / "r.csv"
    path.write_text("key,value,note\npop_zensus_2022,743529,x\n", encoding="utf-8")
    assert read_reference(path) == {"pop_zensus_2022": 743529}


def test_read_reference_by_another_key_column(tmp_path):
    path = tmp_path / "m.csv"
    path.write_text("indicator,value\nSH_SHARE_MONITORING,7.0\nOTHER,1.5\n", encoding="utf-8")
    assert read_reference(path, "indicator") == {"SH_SHARE_MONITORING": 7.0, "OTHER": 1.5}


def test_read_column_keeps_the_order_and_the_text(tmp_path):
    path = tmp_path / "e.csv"
    path.write_text("project_no,title\nE52,A\nE047,B\n", encoding="utf-8")
    assert read_column(path, "project_no") == ["E52", "E047"]


def test_monitoring_reference_keeps_social_housing_for_the_comparison():
    # the checks compare SH_SHARE with this value; without an indicator SH_SHARE_MONITORING the row looks orphaned, but it stays
    assert read_reference(config.MONITORING_CITY_VALUES_CSV, "indicator")["SH_SHARE_MONITORING"] == 7.0
    import pandas as pd
    assert pd.read_csv(config.MONITORING_CITY_VALUES_CSV).set_index("indicator").loc["SH_SHARE_MONITORING", "page"] == 53


def test_reference_holds_the_1_km_vacancy():
    # pipeline/use_cases/housing/README.md: 185 cells of 1 km wholly inside Frankfurt
    r = read_reference(config.CHECK_REFERENCE_CSV)
    assert (r["vacancy_market_km_2022"], r["vacancy_all_km_2022"]) == (1.83, 3.08)
