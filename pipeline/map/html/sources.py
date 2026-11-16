"""Web assets in web/: template, CSS, JavaScript, Leaflet and fonts."""
from __future__ import annotations

import base64
from pathlib import Path


def fonts_css(folder: Path) -> str:
    """The fonts of the flyer, embedded. Archivo is one variable file: each family fixes one width (font-stretch),
    because the font shorthand of map.css resets the width (docs/design.md, Style)."""
    parts = []
    for file, family, weight, stretch in (("mulish-400-latin.woff2", "Mulish", "400", "100%"),
                                          ("mulish-700-latin.woff2", "Mulish", "700", "100%"),
                                          ("archivo-latin.woff2", "Archivo Tight", "700 900", "72%"),
                                          ("archivo-latin.woff2", "Archivo Wide", "700 900", "85%")):
        path = folder / file
        if path.exists():
            b64 = base64.b64encode(path.read_bytes()).decode()
            parts.append(f'@font-face{{font-family:"{family}";font-weight:{weight};font-stretch:{stretch};'
                         f'font-display:swap;src:url(data:font/woff2;base64,{b64}) format("woff2");}}')
    return "\n".join(parts)


def read_web(web: Path) -> tuple[str, dict[str, str]]:
    """The template and the parts for its markers, except the data."""
    js = "\n".join(p.read_text(encoding="utf-8") for p in sorted((web / "js").glob("*.js")))
    parts = {"/*__LEAFLET_CSS__*/": (web / "leaflet" / "leaflet.css").read_text(encoding="utf-8"),
             "/*__FONTS__*/": fonts_css(web / "fonts"),
             "/*__MAP_CSS__*/": (web / "map.css").read_text(encoding="utf-8"),
             "/*__LEAFLET_JS__*/": (web / "leaflet" / "leaflet.js").read_text(encoding="utf-8"),
             "/*__MAP_JS__*/": js}
    return (web / "map.html").read_text(encoding="utf-8"), parts
