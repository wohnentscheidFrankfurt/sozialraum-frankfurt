"""Step election: shares per Stadtteil, the lists shown in the map, the city values and the checks."""
from __future__ import annotations

import json

from pipeline.shared.core.areas import city_rows
from pipeline.shared.core.stats import STORED_DECIMALS
from pipeline.engine.datasets import ELECTION_BY_QUARTER, ELECTION_CHECKS, ELECTION_CITY, ELECTION_LISTS
from pipeline.use_cases.election.checks import check_election_sums, check_gazette
from pipeline.use_cases.election.model import shares
from pipeline.use_cases.election.sources import lists, read_gazette_text, read_party_colors, read_results
from pipeline.engine.steps import Context, Step, write_checks


def run(ctx: Context) -> None:
    c = ctx.config
    all_lists = lists(json.loads(c.ELECTION_RESULT_JSON.read_text(encoding="utf-8")),
                      read_party_colors(c.PARTY_COLORS_CSV))
    city = read_results(c.ELECTION_CITY_CSV)[0]
    areas = read_results(c.ELECTION_QUARTERS_CSV)
    quarters, shown = shares(areas, city, all_lists)
    ctx.store.write(ELECTION_BY_QUARTER, quarters.rename(columns={"quarter": "id"}))
    city_values = {l["key"]: l["city_share"] for l in shown}
    city_values["ELEC_TURNOUT"] = round(100 * city["voters"] / city["eligible"], STORED_DECIMALS)
    ctx.store.write(ELECTION_LISTS, {"lists": shown, "all": all_lists, "city": city_values})
    ctx.store.write(ELECTION_CITY, city_rows(city_values, kind="published"))
    write_checks(ctx.store, ELECTION_CHECKS, [check_election_sums(areas, city),
                                              check_gazette(city, read_gazette_text(c.GAZETTE_PDF), c.GAZETTE_PDF)])
    ctx.log(", ".join(f"{l['name']} {l['city_share']} %" for l in shown))


STEP = Step("election", run, makes=(ELECTION_BY_QUARTER, ELECTION_LISTS, ELECTION_CITY, ELECTION_CHECKS))
