"""Visible text of a saved web page and the texts of the sources of the examples in the ⓘ."""
from __future__ import annotations

import html
import re
from pathlib import Path

from pipeline.shared.readers.pdf import page_texts


def html_text(path: Path) -> str:
    s = path.read_text(encoding="utf-8", errors="replace")
    s = re.sub(r"(?s)<!--.*?-->", " ", s)
    s = re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", s)
    return html.unescape(re.sub(r"<[^>]+>", " ", s)).replace("\xa0", " ")


def example_texts(config, examples: list[dict]) -> dict[str, str]:
    """Source key (a path in pipeline/config.py) -> text of the source: a PDF or a saved web page."""
    def text(path: Path) -> str:
        return " ".join(page_texts(path)) if path.suffix == ".pdf" else html_text(path)
    return {e["source"]: text(getattr(config, e["source"])) for e in examples}
