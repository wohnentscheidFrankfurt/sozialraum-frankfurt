"""Builds the map into output/ from sources/ and reference/. Call: .venv/bin/python -I -m pipeline.build [--step NAME]
Downloading the sources and publishing the map run by hand, outside the build."""
from __future__ import annotations

import argparse

from pipeline import config
from pipeline.map.assembly import step as assembly_step
from pipeline.map.checks import step as checks_step
from pipeline.use_cases.coops import step as coops_step
from pipeline.use_cases.construction_year import step as construction_year_step
from pipeline.use_cases.candidates import step as candidates_step
from pipeline.use_cases.election import step as election_step
from pipeline.use_cases.housing import step as housing_step
from pipeline.use_cases.flat_roofs import step as flat_roofs_step
from pipeline.use_cases.building_gaps import step as building_gaps_step
from pipeline.use_cases.land import step as land_step
from pipeline.map.html import step as map_step
from pipeline.use_cases.monitoring import step as monitoring_step
from pipeline.use_cases.new_construction import step as new_construction_step
from pipeline.use_cases.ownership_cells import step as ownership_cells_step
from pipeline.use_cases.ownership_history import step as ownership_history_step
from pipeline.use_cases.ownership_shares import step as ownership_shares_step
from pipeline.use_cases.protection import step as protection_step
from pipeline.use_cases.public_housing import step as public_housing_step
from pipeline.use_cases.social_housing import step as social_housing_step
from pipeline.use_cases.rent_burden import step as rent_burden_step
from pipeline.use_cases.survey import step as survey_step
from pipeline.shared.zensus import step as zensus_step
from pipeline.engine.steps import Context, check_order, producers
from pipeline.engine.store import Store

STEPS = [zensus_step.ZENSUS_STEP, zensus_step.ZENSUS_2011_STEP,
         ownership_cells_step.STEP,
         public_housing_step.STEP, coops_step.STEP, ownership_shares_step.STEP,
         ownership_history_step.STEP, new_construction_step.STEP, monitoring_step.STEP, survey_step.STEP, rent_burden_step.STEP, protection_step.STEP, land_step.STEP, flat_roofs_step.STEP, building_gaps_step.STEP, election_step.STEP, social_housing_step.STEP,
         housing_step.STEP, construction_year_step.STEP,
         assembly_step.STEP, candidates_step.STEP, checks_step.STEP, map_step.STEP]


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description='Builds the map "Sozialraum Frankfurt".')
    ap.add_argument("--step", choices=[s.name for s in STEPS], help="run only this step")
    args = ap.parse_args(argv)
    check_order(STEPS)
    ctx = Context(Store(config.INTERIM, producers(STEPS)), config)
    for step in STEPS:
        if args.step in (None, step.name):
            print(f"\n== {step.name}")
            step.run(ctx)


if __name__ == "__main__":
    main()
