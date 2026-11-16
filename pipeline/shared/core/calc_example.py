"""A worked example as a written sum: rows with an operator, a rounded number and its meaning. Pure module."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable


@dataclass(frozen=True)
class Row:
    """op: "", "×", "+", "−" or "÷". number: already rounded. total: a line stands above the row. estimate: the browser
    writes "~". unit: "%" on the last row only, or "€" on the rows of an example in euros (survey)."""
    op: str
    number: float
    decimals: int
    text: str
    total: bool = False
    estimate: bool = False
    unit: str = ""


@dataclass(frozen=True)
class CalcExample:
    # the browser writes „Rechnung am Beispiel <area>“: the Stadtteil, or a phrase („einer alleinlebenden Person“)
    area: str
    rows: tuple[Row, ...]
    # the whole label instead: where an ⓘ has more than one sum (view Miete), and for the sum of the whole city
    # („Rechnung für ganz Frankfurt“, ROOF_FLAT)
    label: str = ""


def example_payload(e: CalcExample) -> dict:
    return asdict(e)


def require_example_quarters(quarters: Iterable[str], wanted: dict[str, str]) -> None:
    known = set(quarters)
    for group, name in wanted.items():
        if name not in known:
            raise ValueError(f"no Stadtteil {name} for the example of {group}")
