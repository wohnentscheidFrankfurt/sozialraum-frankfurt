import importlib.util
import json
import os
import sys
import time
from pathlib import Path

import pandas as pd
import pytest

_spec = importlib.util.spec_from_file_location("compare_build", Path(__file__).resolve().parent / "compare_build.py")
cb = importlib.util.module_from_spec(_spec)
sys.modules["compare_build"] = cb  # dataclasses look the module up
_spec.loader.exec_module(cb)

REPORT = "| Status | Check | Result |\n|---|---|---|\n| WARN | Grid: population | 1.234,5 of 2 |\n| OK | Election: sum | a |\n"


def test_payload_reads_the_data_script_and_drops_the_date():
    html = '<script type="application/json" id="data">{"created":"8.10.2026","x":1}</script>'
    assert cb.payload(html) == {"x": 1}


def test_payload_without_data_script_fails():
    with pytest.raises(ValueError, match="data script"):
        cb.payload("<html></html>")


def test_checks_reads_status_and_numbers_as_digits():
    assert cb.checks(REPORT) == {"Grid: population": {"status": "WARN", "numbers": ["12345", "2"]},
                                 "Election: sum": {"status": "OK", "numbers": []}}


def test_diff_json_lists_changed_removed_and_added_once_per_path():
    d = cb.Diff()
    cb.diff_json({"a": 1, "b": [{"x": 1, "y": 2}, {"x": 1, "y": 3}], "c": 0},
                 {"a": 2, "b": [{"x": 1}, {"x": 1}], "d": 0}, "p", d)
    assert d.changed == ["p.a: 1 != 2"]
    assert d.lines() == ["changed: p.a: 1 != 2", "removed: p.c", "removed: p.b[*].y", "added: p.d"]


def test_diff_json_reports_another_list_length_as_a_change():
    d = cb.Diff()
    cb.diff_json([1, 2], [1], "p", d)
    assert d.changed == ["p: length 2 != 1"]


def test_compare_csv_reports_values_and_columns(tmp_path):
    old, new = tmp_path / "old.csv", tmp_path / "new.csv"
    pd.DataFrame({"id": ["1", "2"], "v": [1.5, 2.0], "gone": [0, 0]}).to_csv(old, index=False)
    pd.DataFrame({"id": ["1", "2"], "v": [1.5, 2.5], "new": [0, 0]}).to_csv(new, index=False)
    d = cb.Diff()
    cb.compare_csv(old, new, "t.csv", d)
    assert d.changed == ["t.csv row 1 column v: '2.0' != '2.5'"]
    assert d.removed == ["t.csv:gone"] and d.added == ["t.csv:new"]


def _build(root: Path, value: float, column: str = "v") -> tuple[Path, Path]:
    interim, output = root / "interim", root / "output"
    (output / "data").mkdir(parents=True)
    interim.mkdir()
    pd.DataFrame({"id": ["1"], column: [value]}).to_csv(interim / "t.csv", index=False)
    (interim / "check_report.md").write_text(REPORT, encoding="utf-8")
    (output / "data" / "e.csv").write_text("a\n1\n", encoding="utf-8")
    (output / "m.html").write_text('<script type="application/json" id="data">{"k":1}</script>', encoding="utf-8")
    return interim, output


def test_identical_build_prints_identical(tmp_path, capsys):
    interim, output = _build(tmp_path / "a", 1.0)
    cb.capture(interim, output, "m.html", tmp_path / "golden")
    assert cb.main(["compare", "--golden", str(tmp_path / "golden"), "--interim", str(interim), "--output",
                    str(output), "--map", "m.html"]) == 0
    assert capsys.readouterr().out.strip() == "identical"


def test_changed_value_fails_and_removed_column_does_not(tmp_path):
    interim, output = _build(tmp_path / "a", 1.0)
    cb.capture(interim, output, "m.html", tmp_path / "golden")
    pd.DataFrame({"id": ["1"], "v": [2.0]}).to_csv(interim / "t.csv", index=False)
    assert cb.main(["compare", "--golden", str(tmp_path / "golden"), "--interim", str(interim), "--output",
                    str(output), "--map", "m.html"]) == 1
    pd.DataFrame({"id": ["1"]}).to_csv(interim / "t.csv", index=False)
    d = cb.compare(tmp_path / "golden", interim, output, "m.html")
    assert d.changed == [] and d.removed == ["t.csv:v"]


def test_file_older_than_the_build_start_is_a_change(tmp_path):
    interim, output = _build(tmp_path / "a", 1.0)
    cb.capture(interim, output, "m.html", tmp_path / "golden")
    (interim / ".build-start").write_text("")
    start, old = time.time() - 30, time.time() - 60
    os.utime(interim / ".build-start", (start, start))
    os.utime(interim / "t.csv", (old, old))
    assert cb.compare(tmp_path / "golden", interim, output, "m.html").changed == [
        "t.csv is older than the build start"]


def test_ui_compares_two_dumps(tmp_path):
    a, b = tmp_path / "a.json", tmp_path / "b.json"
    a.write_text(json.dumps({"start": {"legend": "x"}}), encoding="utf-8")
    b.write_text(json.dumps({"start": {"legend": "y"}}), encoding="utf-8")
    assert cb.compare_ui(a, b).changed == ["ui.start.legend: 'x' != 'y'"]
