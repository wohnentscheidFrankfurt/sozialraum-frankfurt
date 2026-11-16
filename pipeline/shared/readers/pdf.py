"""Text of PDF pages."""
from __future__ import annotations

from pathlib import Path


def page_texts(path: Path) -> list[str]:
    import pymupdf
    with pymupdf.open(path) as doc:
        return [page.get_text() for page in doc]
