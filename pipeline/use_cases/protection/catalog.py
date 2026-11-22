"""Title and ⓘ of the coverage with Milieuschutz, and the ⓘ of the statute overlays (texts.<lang>.yaml). Pure module."""
from __future__ import annotations

from pipeline.shared.core.indicator import BOTH, Indicator, Source
from pipeline.shared.core.texts import Texts, package_texts, per_language

T: dict[str, Texts] = package_texts(__file__)
OVERLAY_NAMES = ("social_preservation", "social_preservation_pending", "townscape", "townscape_pending")


def _sources(t: Texts) -> list[Source]:
    return [Source(**t.tree("sources.plan_as"))]


def _indicators(t: Texts) -> list[Indicator]:
    return [Indicator("PROT_SOCIAL", t["PROT_SOCIAL.title"], t["core.groups.planning"], "%", BOTH,
                      t["PROT_SOCIAL.source"], t["PROT_SOCIAL.as_of"], t["PROT_SOCIAL.calc"], "teal", 0, layer=False,
                      rule=t["PROT_SOCIAL.rule"], section="planning")]


SOURCES: dict[str, list[Source]] = per_language(_sources, T)
INDICATORS: dict[str, list[Indicator]] = per_language(_indicators, T)
OVERLAYS: dict[str, dict[str, dict]] = per_language(
    lambda t: {name: t.tree(f"overlays.{name}") for name in OVERLAY_NAMES}, T)
