"""Compares a build with a golden master: all interim data, the local exports, the data of the map and the numbers of
every check.

  python -I tests/compare_build.py capture --interim DIR --output DIR --map NAME --dest DIR
  python -I tests/compare_build.py compare --golden DIR --interim DIR --output DIR --map NAME
  python -I tests/compare_build.py ui --golden FILE --current FILE

`compare` and `ui` print changed values (exit code 1), then removed and added files, columns, keys and checks (exit
code 0 when nothing changed). Key and column order carry no meaning; the order of a list does, except in the check
results of a step (`*_checks.json`), which compare by check name.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

PAYLOAD = re.compile(r'<script type="application/json" id="data">(.*?)</script>', re.S)
CHECK_ROW = re.compile(r"^\| (OK|WARN|FAIL) \| (.+?) \| ")
NUMBER = re.compile(r"\d+(?:[.,]\d+)*")
BUILD_START = ".build-start"
REPORT = "check_report.md"
EXPORTS = "data"
DATA_SUFFIXES = (".csv", ".json", ".geojson")
CHECKS_SUFFIX = "_checks.json"  # the check results of a step, a list of {name, status, text}
SHOWN = 50  # changed lines printed at most


@dataclass
class Diff:
    changed: list[str] = field(default_factory=list)
    removed: list[str] = field(default_factory=list)
    added: list[str] = field(default_factory=list)

    def lines(self) -> list[str]:
        """Changed values, then removed and added paths; list positions collapse to [*]."""
        def once(paths: list[str]) -> list[str]:
            out: list[str] = []
            for p in paths:
                q = re.sub(r"\[\d+\]", "[*]", p)
                if q not in out:
                    out.append(q)
            return out
        return ([f"changed: {x}" for x in self.changed] + [f"removed: {x}" for x in once(self.removed)]
                + [f"added: {x}" for x in once(self.added)])


def payload(html: str) -> dict:
    match = PAYLOAD.search(html)
    if not match:
        raise ValueError("no data script in the map")
    data = json.loads(match.group(1))
    data.pop("created", None)
    return data


def checks(report: str) -> dict[str, dict]:
    """Status and numbers of the result per check; numbers as digit strings, so 53.739,13 equals 53,739.13."""
    out = {}
    for line in report.splitlines():
        m = CHECK_ROW.match(line)
        if m:
            numbers = sorted(re.sub(r"[.,]", "", n) for n in NUMBER.findall(line[m.end():]))
            out[m.group(2)] = {"status": m.group(1), "numbers": numbers}
    return out


def capture(interim: Path, output: Path, map_name: str, dest: Path) -> None:
    if dest.exists():
        raise FileExistsError(f"{dest} exists; delete it first")
    (dest / "interim").mkdir(parents=True)
    for path in sorted(interim.iterdir()):
        if path.suffix in DATA_SUFFIXES:
            shutil.copy2(path, dest / "interim" / path.name)
    shutil.copytree(output / EXPORTS, dest / "exports")
    data = payload((output / map_name).read_text(encoding="utf-8"))
    (dest / "payload.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    report = checks((interim / REPORT).read_text(encoding="utf-8"))
    (dest / "checks.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")


def diff_json(a, b, where: str, d: Diff) -> None:
    if isinstance(a, dict) and isinstance(b, dict):
        d.removed += [f"{where}.{k}" for k in a if k not in b]
        d.added += [f"{where}.{k}" for k in b if k not in a]
        for k in a:
            if k in b:
                diff_json(a[k], b[k], f"{where}.{k}", d)
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            d.changed.append(f"{where}: length {len(a)} != {len(b)}")
            return
        for i, (x, y) in enumerate(zip(a, b)):
            diff_json(x, y, f"{where}[{i}]", d)
    elif type(a) is not type(b) or a != b:
        d.changed.append(f"{where}: {a!r} != {b!r}")


def compare_csv(old: Path, new: Path, name: str, d: Diff) -> None:
    a = pd.read_csv(old, dtype=str, keep_default_na=False)
    b = pd.read_csv(new, dtype=str, keep_default_na=False)
    d.removed += [f"{name}:{c}" for c in a.columns if c not in b.columns]
    d.added += [f"{name}:{c}" for c in b.columns if c not in a.columns]
    if len(a) != len(b):
        d.changed.append(f"{name}: {len(a)} rows != {len(b)}")
        return
    for c in [c for c in a.columns if c in b.columns]:
        for i in (a[c] != b[c]).to_numpy().nonzero()[0][:3]:
            d.changed.append(f"{name} row {i} column {c}: {a[c].iloc[i]!r} != {b[c].iloc[i]!r}")


def compare_folder(golden: Path, current: Path, prefix: str, d: Diff) -> None:
    old = {p.name: p for p in golden.iterdir() if p.suffix in DATA_SUFFIXES}
    new = {p.name: p for p in current.iterdir() if p.suffix in DATA_SUFFIXES}
    d.removed += [prefix + n for n in sorted(set(old) - set(new))]
    d.added += [prefix + n for n in sorted(set(new) - set(old))]
    for n in sorted(set(old) & set(new)):
        if n.endswith(".csv"):
            compare_csv(old[n], new[n], prefix + n, d)
        else:
            a, b = (json.loads(p.read_text(encoding="utf-8")) for p in (old[n], new[n]))
            if n.endswith(CHECKS_SUFFIX):  # a language adds checks to the list: compare them by name
                a, b = ({c["name"]: c for c in x} for x in (a, b))
            diff_json(a, b, prefix + n, d)


def stale(current: Path, prefix: str, since: float | None) -> list[str]:
    """Data files older than the build start were not written by the last build."""
    if since is None:
        return []
    return [f"{prefix}{p.name} is older than the build start" for p in sorted(current.iterdir())
            if p.suffix in DATA_SUFFIXES and p.stat().st_mtime < since]


def compare(golden: Path, interim: Path, output: Path, map_name: str) -> Diff:
    d = Diff()
    start = interim / BUILD_START
    since = start.stat().st_mtime if start.exists() else None
    d.changed += stale(interim, "", since) + stale(output / EXPORTS, "exports/", since)
    compare_folder(golden / "interim", interim, "", d)
    compare_folder(golden / "exports", output / EXPORTS, "exports/", d)
    diff_json(json.loads((golden / "payload.json").read_text(encoding="utf-8")),
              payload((output / map_name).read_text(encoding="utf-8")), "payload", d)
    diff_json(json.loads((golden / "checks.json").read_text(encoding="utf-8")),
              checks((interim / REPORT).read_text(encoding="utf-8")), "checks", d)
    return d


def compare_ui(golden: Path, current: Path) -> Diff:
    d = Diff()
    diff_json(json.loads(golden.read_text(encoding="utf-8")), json.loads(current.read_text(encoding="utf-8")), "ui", d)
    return d


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="command", required=True)
    cap, cmp_ = sub.add_parser("capture"), sub.add_parser("compare")
    for p in (cap, cmp_):
        p.add_argument("--interim", type=Path, required=True)
        p.add_argument("--output", type=Path, required=True)
        p.add_argument("--map", required=True)
    cap.add_argument("--dest", type=Path, required=True)
    cmp_.add_argument("--golden", type=Path, required=True)
    ui = sub.add_parser("ui")
    ui.add_argument("--golden", type=Path, required=True)
    ui.add_argument("--current", type=Path, required=True)
    args = ap.parse_args(argv)
    if args.command == "capture":
        capture(args.interim, args.output, args.map, args.dest)
        print(f"golden master in {args.dest}")
        return 0
    d = (compare(args.golden, args.interim, args.output, args.map) if args.command == "compare"
         else compare_ui(args.golden, args.current))
    lines = d.lines()
    shown = [x for x in lines if x.startswith("changed:")][:SHOWN] + [x for x in lines if not x.startswith("changed:")]
    if len(d.changed) > SHOWN:
        shown.insert(SHOWN, f"… {len(d.changed) - SHOWN} more changed values")
    print("\n".join(shown) if shown else "identical")
    return 1 if d.changed else 0


if __name__ == "__main__":
    sys.exit(main())
