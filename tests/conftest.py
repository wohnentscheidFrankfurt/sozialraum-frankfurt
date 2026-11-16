from types import SimpleNamespace

import pytest

from pipeline.engine.steps import Context
from pipeline.engine.store import Store


def run_step(tmp_path, step, tables: dict, **cfg):
    """Runs one step on a fake store: tables maps Dataset -> data. Returns the store and the log lines."""
    store, logs = Store(tmp_path / "interim"), []
    for dataset, data in tables.items():
        store.write(dataset, data)
    step.run(Context(store, SimpleNamespace(**cfg), log=logs.append))
    return store, logs


@pytest.fixture(name="run_step", scope="session")
def run_step_fixture():
    """run_step for the tests: with --import-mode=importlib a test module cannot import conftest."""
    return run_step


# Terms that no map text of a view uses (docs/texts.md): working words of the build, the short name of a group
BANNED_TERMS = ("Rücktest", "Lücke", "Geheimhaltung", "Maß:", "Rechenweg", "Zelle", "Spanne", "Abgleich", "NH")


@pytest.fixture(name="banned", scope="session")
def banned_fixture():
    """BANNED_TERMS for the catalog tests of the views: with --import-mode=importlib a test module cannot import
    conftest or another test module."""
    return BANNED_TERMS
