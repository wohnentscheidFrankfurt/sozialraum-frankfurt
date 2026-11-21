"""Number formats of the map by language. Pure module."""
from __future__ import annotations


def format_number(value: float, decimals: int, unit: str = "", lang: str = "de") -> str:
    """Number with thousands separator, as the map shows it: de 18,4 %; 69.219; 1.200 €; en 18.4%; 69,219; €1,200."""
    text = f"{value:,.{decimals}f}"
    if lang == "de":
        text = text.replace(",", " ").replace(".", ",").replace(" ", ".")
        return f"{text} {unit}" if unit else text
    if unit == "%":
        return f"{text}%"
    if unit == "€":
        return f"€{text}"
    return f"{text} {unit}" if unit else text


def format_range(low: float, high: float, decimals: int = 1, lang: str = "de") -> str:
    """Smallest and largest half range: de „0,6 bis 8,8“, en „0.6 to 8.8“; one number where both round alike
    („3,5“); no trailing zero decimals."""
    point = "," if lang == "de" else "."
    a, b = (format_number(x, decimals, lang=lang).removesuffix(point + "0" * decimals) if decimals
            else format_number(x, 0, lang=lang) for x in (low, high))
    return a if a == b else f"{a} {'bis' if lang == 'de' else 'to'} {b}"
