"""Step monitoring: Monitoring 2024 per district, Stadtteil and Frankfurt, and its checks."""
from __future__ import annotations

from pipeline.engine.datasets import (MONITORING_BY_DISTRICT, MONITORING_BY_QUARTER, MONITORING_CHECKS, MONITORING_CITY,
                                      in_language, languages)
from pipeline.shared.core.texts import LANGUAGES, SOURCE_LANGUAGE
from pipeline.shared.geography.sources import load_districts
from pipeline.shared.readers.reference import read_reference
from pipeline.use_cases.monitoring.catalog import T
from pipeline.use_cases.monitoring.checks import check_monitoring
from pipeline.use_cases.monitoring.model import monitoring_by_district, monitoring_city, quarter_monitoring
from pipeline.use_cases.monitoring.sources import read_monitoring
from pipeline.engine.steps import Context, Step, write_checks


def run(ctx: Context) -> None:
    s, c = ctx.store, ctx.config
    monitoring = read_monitoring(c.MONITORING_CSV)
    for lang in LANGUAGES:  # the column `_SHARED` holds a text; the numbers are the same in every language
        s.write(in_language(MONITORING_BY_DISTRICT, lang),
                monitoring_by_district(monitoring, T[lang]).rename(columns={"district": "id"}))
    # the numbers of the following steps come from the source language
    by_district = monitoring_by_district(monitoring, T[SOURCE_LANGUAGE]).rename(columns={"district": "id"})
    districts = load_districts(c.DISTRICTS_GML, c.MONITORING_CSV)
    by_quarter = quarter_monitoring(by_district.rename(columns={"id": "district"}), {d.id: d.quarter for d in districts})
    s.write(MONITORING_BY_QUARTER, by_quarter.rename(columns={"quarter": "id"}))
    published = read_reference(c.MONITORING_CITY_VALUES_CSV, "indicator")
    s.write(MONITORING_CITY, monitoring_city(published))
    write_checks(s, MONITORING_CHECKS, check_monitoring(by_district, published))
    ctx.log(f"{len(by_district)} districts, {len(by_quarter)} quarters")


STEP = Step("monitoring", run, needs=(),
            makes=(*languages(MONITORING_BY_DISTRICT), MONITORING_BY_QUARTER, MONITORING_CITY, MONITORING_CHECKS))
