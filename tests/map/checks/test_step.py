from pathlib import Path

import pandas as pd
import pytest

from pipeline.build import STEPS
from pipeline.map.checks import step
from pipeline.engine.datasets import (CELLS_2022, CHECK_REPORT, CHECK_RESULTS, INDICATORS_DISTRICTS,
                                      INDICATORS_QUARTERS, OWNERSHIP_CELLS)
from pipeline.engine.steps import Context


def test_checks_collects_every_check_file():
    made = {d.name for s in STEPS for d in s.makes if d.name.endswith("_checks")}
    checks_step = next(s for s in STEPS if s.name == "checks")
    assert made == {d.name for d in CHECK_RESULTS} and made <= {d.name for d in checks_step.needs}


class FakeStore:
    def __init__(self, data: dict):
        self.data, self.written = data, {}

    def read(self, dataset):
        return self.data[dataset.name]

    def write(self, dataset, value):
        self.written[dataset.name] = value

    def path(self, dataset):
        return Path("interim") / dataset.file


def _store(results: dict[str, list[dict]]) -> FakeStore:
    data = {d.name: results.get(d.name, []) for d in CHECK_RESULTS}
    data[OWNERSHIP_CELLS.name] = pd.DataFrame({"dw_unassigned": [1.0], "dw_from_2011": [0.0]})
    data[CELLS_2022.name] = pd.DataFrame({"edge": [0], "dwellings": [10]})
    data[INDICATORS_DISTRICTS.name] = pd.DataFrame()
    data[INDICATORS_QUARTERS.name] = pd.DataFrame()
    return FakeStore(data)


@pytest.fixture
def run_checks(monkeypatch):
    monkeypatch.setattr(step.m, "report_sections", lambda *args: ["## Sections\n"])
    logged = []

    def run(store):
        step.run(Context(store, None, log=logged.append))
    run.logged = logged
    return run


def test_checks_writes_the_report_and_stops_on_a_fail(run_checks):
    store = _store({CHECK_RESULTS[0].name: [{"name": "Grid: population", "status": "FAIL", "text": "is 1, expected 2"}],
                    CHECK_RESULTS[1].name: [{"name": "Own: total", "status": "OK", "text": "fits"}]})
    with pytest.raises(SystemExit, match=r"1 check\(s\) with FAIL, see interim/check_report.md"):
        run_checks(store)
    report = store.written[CHECK_REPORT.name]
    assert "| FAIL | Grid: population | is 1, expected 2 |" in report and "| OK | Own: total | fits |" in report
    assert report.index("FAIL | Grid: population") < report.index("OK | Own: total")  # FAIL first
    assert any("Grid: population" in line for line in run_checks.logged)


def test_checks_writes_the_report_and_goes_on_without_a_fail(run_checks):
    store = _store({CHECK_RESULTS[0].name: [{"name": "Grid: population", "status": "WARN", "text": "close"}]})
    run_checks(store)
    assert "| WARN | Grid: population | close |" in store.written[CHECK_REPORT.name]
