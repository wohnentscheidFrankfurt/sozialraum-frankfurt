"""Titles and ⓘ of the election indicators; the list shares follow the lists of the build (texts.<lang>.yaml).
Pure module."""
from __future__ import annotations

import datetime

from pipeline.shared.core.indicator import QUARTERS_ONLY, Indicator, Source
from pipeline.shared.core.texts import Texts, package_texts, per_language
from pipeline.use_cases.election.model import THRESHOLD

T: dict[str, Texts] = package_texts(__file__)
ELECTION_DAY = "15.3.2026"  # as the texts of the map name it (cover note); a test ties it to ELECTION_DATE
ELECTION_DATE = datetime.date(2026, 3, 15)
ELECTION_LAYERS = ("ELEC_STRONGEST", "ELEC_TURNOUT")  # the layers besides the share of a list; the browser lists them first


def _values(t: Texts) -> dict[str, str]:
    return {"election_day": t.date(ELECTION_DATE), "election_year": str(ELECTION_DATE.year),
            "threshold": t.number(THRESHOLD, 0)}


def _sources(t: Texts) -> list[Source]:
    values = _values(t)
    return [Source(**{k: t.fill(f"sources.election.{k}", **values) for k in ("title", "as_of", "license")})]


def election_indicators(lists: list[dict], t: Texts) -> list[Indicator]:
    values = _values(t)

    def text(key: str, **extra: str) -> str:
        return t.fill(key, **values, **extra)

    source, group, day = t["source"], t["core.groups.election"], text("sources.election.as_of")
    ks = [Indicator(ELECTION_LAYERS[0], text("ELEC_STRONGEST.title"), group, "", QUARTERS_ONLY, source, day,
                    text("ELEC_STRONGEST.calc"), type="category",
                    legend_note=text("ELEC_STRONGEST.legend_note"), section="election"),
          Indicator(ELECTION_LAYERS[1], text("ELEC_TURNOUT.title"), group, "%", QUARTERS_ONLY, source, day,
                    text("ELEC_TURNOUT.calc"), "teal",
                    legend_note=text("ELEC_TURNOUT.legend_note"), section="election"),
          Indicator("ELEC_VOTERS", text("ELEC_VOTERS.title"), group, text("ELEC_VOTERS.unit"), QUARTERS_ONLY, source,
                    day, text("ELEC_VOTERS.calc"), decimals=0, layer=False, criterion=False,
                    count_of=ELECTION_LAYERS[1], count_total="ELEC_ELIGIBLE", section="election")]
    return ks + [Indicator(l["key"], text("list_share.title", name=l["name"]), group, "%", QUARTERS_ONLY, source, day,
                           text("other_share.calc" if l["key"] == "ELEC_OTHER" else "list_share.calc"),
                           f"color:{l['color']}", legend_note=text("list_share.legend_note"), section="election")
                 for l in lists]


SOURCES: dict[str, list[Source]] = per_language(_sources, T)
INDICATORS: dict[str, list[Indicator]] = per_language(lambda t: election_indicators([], t), T)
