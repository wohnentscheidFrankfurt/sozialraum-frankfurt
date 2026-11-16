"""Colours derived from fixed colours, computed once in Python. Pure module.

The browser receives the finished colours: the ramps of the indicators and the text and line colours of the view
„Trend“. `palette.py` holds fixed colours, this module derives from them.
"""
from __future__ import annotations

import math
import re

NAMED = {
    "red": ["#fee5d9", "#fcae91", "#fb6a4a", "#de2d26", "#a50f15"],
    "blue": ["#eff3ff", "#bdd7e7", "#6baed6", "#3182bd", "#08519c"],
    "purple": ["#f2f0f7", "#cbc9e2", "#9e9ac8", "#756bb1", "#54278f"],
    "orange": ["#feedde", "#fdbe85", "#fd8d3c", "#e6550d", "#a63603"],
    "teal": ["#e6fafa", "#b3eeee", "#66dddd", "#16cccc", "#0e8080"],
}
FALLBACK = "teal"  # an unknown name or an invalid colour gets this ramp
LIGHT = 0.59  # a colour lighter than this (OKLab L) is darkened at the end of its ramp
READABLE = 0.57  # lightness of the last step of a darkened ramp
WEIGHTS = (0.88, 0.68, 0.46, 0.22, 0)  # share of white in steps 1 to 5
_COLOUR_NAME = re.compile(r"color:(#[0-9a-f]{6})", re.IGNORECASE)


def oklab_l(rgb: tuple[float, ...]) -> float:
    """Lightness L of an sRGB colour (0 to 255 per channel) in OKLab."""
    r, g, b = ((x / 255 / 12.92) if x / 255 <= 0.04045 else ((x / 255 + 0.055) / 1.055) ** 2.4 for x in rgb)
    long = math.cbrt(0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b)
    medium = math.cbrt(0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b)
    short = math.cbrt(0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b)
    return 0.2104542553 * long + 0.793617785 * medium - 0.0040720468 * short


def _darkened(rgb: list[float]) -> list[float]:
    """Scales a light colour towards black until its OKLab lightness is READABLE (bisection, 20 steps)."""
    low, high = 0.0, 1.0
    for _ in range(20):
        mid = (low + high) / 2
        if oklab_l([v * mid for v in rgb]) > READABLE:
            high = mid
        else:
            low = mid
    return [v * low for v in rgb]


def ramp(name: str) -> list[str]:
    """Five hex colours from almost white to the end colour. name: a key of NAMED or "color:#rrggbb" (party lists,
    owner groups). Light colours (for example FDP yellow) end darker than themselves. Anything else gets FALLBACK."""
    if name in NAMED:
        return list(NAMED[name])
    hit = _COLOUR_NAME.fullmatch(name)
    if not hit:
        return list(NAMED[FALLBACK])
    end = [float(int(hit.group(1)[i:i + 2], 16)) for i in (1, 3, 5)]
    if oklab_l(end) > LIGHT:
        end = _darkened(end)
    # floor(x + 0.5) is Math.round of the browser for the positive values here
    return ["#" + "".join(f"{math.floor(v + (255 - v) * w + 0.5):02x}" for v in end) for w in WEIGHTS]


def _linear(value: int) -> float:
    v = value / 255
    return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4


def luminance(colour: str) -> float:
    """Relative luminance of "#rrggbb" after WCAG 2."""
    r, g, b = (_linear(int(colour[i:i + 2], 16)) for i in (1, 3, 5))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a: str, b: str) -> float:
    """Contrast ratio of two "#rrggbb" colours after WCAG 2: 1 to 21."""
    la, lb = luminance(a), luminance(b)
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


def text_on(colour: str) -> str:
    """Dark or white text, whichever contrasts more with the fill."""
    return "#1a1a1a" if contrast(colour, "#1a1a1a") >= contrast(colour, "#ffffff") else "#ffffff"


def line_on(colour: str) -> str:
    """The same hue, darkened in steps of 5 % until it reaches 3:1 against white (WCAG non-text contrast)."""
    rgb, out = [int(colour[i:i + 2], 16) for i in (1, 3, 5)], colour
    while contrast(out, "#ffffff") < 3:
        rgb = [math.floor(v * 0.95) for v in rgb]
        out = "#" + "".join(f"{v:02x}" for v in rgb)
    return out
