"""The step of new_construction reads 23 PDFs. Its tests read each PDF once: the step through the patch,
the other tests through the fixture page_texts."""
from functools import cache

import pytest

from pipeline.shared.readers import pdf
from pipeline.use_cases.new_construction import step


@cache
def _pages(path, mtime_ns: int, size: int) -> tuple[str, ...]:
    return tuple(pdf.page_texts(path))


def cached_page_texts(path) -> list[str]:
    """page_texts with a cache; a changed file (time or size) is read again."""
    stat = path.stat()
    return list(_pages(path, stat.st_mtime_ns, stat.st_size))


@pytest.fixture(autouse=True, scope="module")
def read_each_pdf_once():
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(step, "page_texts", cached_page_texts)
        yield


@pytest.fixture(name="page_texts", scope="session")
def page_texts_fixture():
    return cached_page_texts
