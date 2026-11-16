
from pipeline import config
from pipeline.engine.datasets import (COMPANY_BUILDINGS_BY_DECADE, OWNERSHIP_BY_SIZE, OWNERSHIP_HISTORY,
                                      OWNERSHIP_HISTORY_CHECKS, OWNERSHIP_HISTORY_VIEW)
from pipeline.use_cases.ownership_history.catalog import EXAMPLES
from pipeline.use_cases.ownership_history.step import STEP


def test_history_step_writes_three_datasets(tmp_path, run_step):
    store, _ = run_step(tmp_path, STEP, {}, ZENSUS_4000W_1011=config.ZENSUS_4000W_1011,
                        ZENSUS_3000G_2001=config.ZENSUS_3000G_2001, ZENSUS_3000G_2007=config.ZENSUS_3000G_2007,
                        ZENSUS_4000W_2013=config.ZENSUS_4000W_2013, ZENSUS_4000W=config.ZENSUS_4000W,
                        **{e["source"]: getattr(config, e["source"]) for e in EXAMPLES})
    g = store.read(OWNERSHIP_HISTORY).set_index(["group", "year"])
    assert g.loc[("housing_company", 2022), "dwellings"] == 57076 and g.loc[("public", 2011), "dwellings"] == 72650
    assert g.loc[("other_company", 2022), "buildings"] == 1623 and g.loc[("public", 2011), "buildings"] == 9647
    d = store.read(COMPANY_BUILDINGS_BY_DECADE)
    assert len(d) == 20 and d[d["year"] == 2022]["buildings"].sum() == 6795
    s = store.read(OWNERSHIP_BY_SIZE).set_index(["group", "year", "size"])
    assert len(s) == 90 and s.loc[("company", 2022, "13_plus"), "dwellings"] == 40934
    assert set(store.read(OWNERSHIP_HISTORY_VIEW)) == {"groups", "company", "bar_order", "sectors", "sizes", "decades",
                                                          "source", "charts"}
    checks = store.read(OWNERSHIP_HISTORY_CHECKS)
    assert checks and [r["text"] for r in checks if r["status"] != "OK"] == []
