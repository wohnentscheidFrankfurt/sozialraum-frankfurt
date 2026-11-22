"""Titles and ⓘ of the monitoring indicators (texts.<lang>.yaml). Pure module."""
from __future__ import annotations

from pipeline.shared.core.indicator import BOTH, Indicator, Source
from pipeline.shared.core.texts import Texts, package_texts, per_language

T: dict[str, Texts] = package_texts(__file__)


def _sources(t: Texts) -> list[Source]:
    return [Source(**t.tree("sources.monitoring"))]


def _indicators(t: Texts) -> list[Indicator]:
    group = t["core.groups.situation"]
    return [
        Indicator("SOC_MIN_INCOME", t["SOC_MIN_INCOME.title"], group, "%", BOTH, t["SOC_MIN_INCOME.source"],
                  t["SOC_MIN_INCOME.as_of"], t["SOC_MIN_INCOME.calc"], "purple", rule=t["SOC_MIN_INCOME.rule"],
                  uncertainty=t["SOC_MIN_INCOME.uncertainty"], legend_note=t["SOC_MIN_INCOME.legend_note"],
                  section="situation"),
        Indicator("SOC_UNEMPLOYED", t["SOC_UNEMPLOYED.title"], group, "%", BOTH, t["SOC_UNEMPLOYED.source"],
                  t["SOC_UNEMPLOYED.as_of"], t["SOC_UNEMPLOYED.calc"], "purple", rule=t["SOC_UNEMPLOYED.rule"],
                  legend_note=t["SOC_UNEMPLOYED.legend_note"], section="situation"),
        Indicator("SOC_INDEX", t["SOC_INDEX.title"], group, "", ("district",), t["SOC_INDEX.source"],
                  t["SOC_INDEX.as_of"], t["SOC_INDEX.calc"], "purple", rule=t["SOC_INDEX.rule"],
                  legend_note=t["SOC_INDEX.legend_note"], decimals=0, rank=114, section="situation"),
    ]


SOURCES: dict[str, list[Source]] = per_language(_sources, T)
INDICATORS: dict[str, list[Indicator]] = per_language(_indicators, T)
