"""Preservation statutes from the planAS WFS: No. 2 (social preservation) and No. 1 only (townscape)."""
from __future__ import annotations

from pipeline.shared.core.geometry import Feature, Site

IN_FORCE = "inkrafttreten"  # date property of statutes in force
DECIDED = "aufstellungsbeschluss"  # date property of statutes in procedure


def is_social_preservation(props: dict[str, str]) -> bool:
    return props.get("paragraf_172_1_2") == "1" or "Nr. 2" in props.get("zusatz", "")


def is_townscape(props: dict[str, str]) -> bool:
    """No. 1 only (townscape). Statutes with No. 2 are social preservation and count there."""
    return props.get("paragraf_172_1_1") == "1" and not is_social_preservation(props)


def _sites(features: list[Feature], keep, date_field: str = "") -> list[Site]:
    return [Site(f.props.get("titel", ""), f.props.get("projekt_nr", ""), f.geom,
                 f.props.get(date_field, "") if date_field else "")
            for f in features if f.geom is not None and keep(f.props)]


def read_social_preservation(features: list[Feature]) -> list[Site]:
    return _sites(features, is_social_preservation)


def read_townscape(features: list[Feature], date_field: str) -> list[Site]:
    return _sites(features, is_townscape, date_field)
