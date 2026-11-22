"""Downloads raw sources into cache/ (pipeline/update_sources.py) and the dates of the downloads."""
from __future__ import annotations

import csv
import datetime as dt
import json
import re
import subprocess
import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


ATTEMPTS = 3


def fetch_url(url: str) -> bytes:
    """Downloads with curl: the votemanager CDN blocks Python clients (security check, HTTP 503). Tries ATTEMPTS
    times: with several requests at once a service sometimes breaks the connection."""
    for attempt in range(ATTEMPTS):
        result = subprocess.run(["curl", "-sSL", "--fail", "--max-time", "300", "-A", "Mozilla/5.0 (Sozialraum Frankfurt)",
                                 url], capture_output=True, check=False)
        if result.returncode == 0:
            return result.stdout
        if attempt < ATTEMPTS - 1:
            time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"download failed ({result.returncode}): {url}: {result.stderr.decode(errors='replace').strip()}")


def download(url: str, target: Path, refresh: bool = False, fetch=fetch_url) -> bool:
    """Downloads url to target unless target exists and refresh is False. True means: downloaded."""
    if target.exists() and target.stat().st_size > 0 and not refresh:
        return False
    data = fetch(url)
    if data.lstrip()[:15].lower().startswith((b"<!doctype html", b"<html")):
        raise RuntimeError(f"HTML page instead of data from {url}")
    target.parent.mkdir(parents=True, exist_ok=True)
    part = target.with_name(target.name + ".teil")
    part.write_bytes(data)
    part.replace(target)
    return True


def table_url(api: str, table: str, key: str) -> str:
    """The data request of one table of a GENESIS web client. The key is the statistic code plus the variable codes of
    the selection, separated by spaces."""
    return f"{api}{table}/data/{urllib.parse.quote(key)}"


def download_table(api: str, table: str, key: str, target: Path, refresh: bool = False, fetch=fetch_url) -> bool:
    """Stores the structure, the data answer and the URL of the data request of one table as one JSON file, unless
    target exists and refresh is False. True means: downloaded. The open API of the web client needs no login. An
    answer without its parts (an error object, a changed API) stops the run and leaves the old file."""
    if target.exists() and target.stat().st_size > 0 and not refresh:
        return False
    answers = {"url": table_url(api, table, key)}
    for name, url, part in (("structure", f"{api}{table}/structure", "variableValues"), ("data", answers["url"], "data")):
        data = fetch(url)
        try:
            answers[name] = json.loads(data)
        except ValueError:
            raise RuntimeError(f"no JSON from {url}: {data[:80]!r}") from None
        if not isinstance(answers[name], dict) or part not in answers[name]:
            raise RuntimeError(f"no {part} in the answer of {url}: {data[:80]!r}")
    target.parent.mkdir(parents=True, exist_ok=True)
    part = target.with_name(target.name + ".teil")
    part.write_text(json.dumps(answers, ensure_ascii=False), encoding="utf-8")
    part.replace(target)
    return True


def download_boris(folder: Path, url: str, page_size: int, refresh: bool = False, fetch=fetch_url) -> list[Path]:
    """Pages through the BORIS WFS and stores each page as boris_NN.gml."""
    done = folder / "done.txt"
    if done.exists() and not refresh:
        return sorted(folder.glob("boris_*.gml"))
    folder.mkdir(parents=True, exist_ok=True)
    done.unlink(missing_ok=True)
    for old in folder.glob("boris_*.gml"):
        old.unlink()
    paths: list[Path] = []
    start = 0
    while True:
        data = fetch(f"{url}&COUNT={page_size}&STARTINDEX={start}")
        m = re.search(rb'numberReturned="(\d+)"', data)
        if not m:
            raise RuntimeError(f"BORIS response without numberReturned at STARTINDEX={start}")
        path = folder / f"boris_{len(paths):02d}.gml"
        path.write_bytes(data)
        paths.append(path)
        if int(m.group(1)) < page_size:
            break
        start += page_size
    done.write_text(str(len(paths)))
    return paths


def boris_value(text: str, number: str) -> tuple[str, str]:
    """Value in €/m² and Stichtag of the zone `number` in a text/plain GetFeatureInfo answer of the BORIS WMS;
    ("", "") if no zone there has this number, an empty value if the zone has no single value in €/m²."""
    for part in text.split("Feature ")[1:]:
        fields = dict(re.findall(r"(\w+) = '([^']*)'", part))
        if fields.get("WNUM") == number:
            value = re.fullmatch(r"(\d+(?:,\d+)?) EUR/m²", fields.get("BRW", ""))  # farmland lists several uses
            return (value.group(1).replace(",", ".") if value else ""), fields.get("STAG", "")
    return "", ""


def download_boris_values(points: list[tuple[str, float, float]], url: str, target: Path, refresh: bool = False,
                          fetch=fetch_url, attempts: int = 3, pause: float = 2.0, pages_time: float = 0.0) -> bool:
    """Asks the BORIS WMS at the point (number, x, y) of each zone for the value of the zone with the same number and
    writes number, value, as_of to target (empty where the number does not hold there). url holds {x0},{y0},{x1},{y1}
    for a box of 1 m around the point. A table older than pages_time (the time of the pages) is loaded again. An
    answer that is no GetFeatureInfo result counts as an error, so it never reads as a dropped zone. True means:
    downloaded."""
    if target.exists() and target.stat().st_size > 0 and not refresh and target.stat().st_mtime >= pages_time:
        return False

    def ask(point):
        number, x, y = point
        for attempt in range(attempts):
            try:
                text = fetch(url.format(x0=x - 0.5, y0=y - 0.5, x1=x + 0.5, y1=y + 0.5)).decode("utf-8", "replace")
                if not text.startswith("GetFeatureInfo results"):
                    raise RuntimeError(f"no GetFeatureInfo answer for zone {number}: {text[:80]!r}")
                return (number, *boris_value(text, number))
            except RuntimeError:
                if attempt == attempts - 1:
                    raise
                time.sleep(pause)

    with ThreadPoolExecutor(4) as pool:  # four at a time; the WMS answers one point in about 0.2 s
        rows = list(pool.map(ask, points))
    target.parent.mkdir(parents=True, exist_ok=True)
    part = target.with_name(target.name + ".teil")
    with part.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(("number", "value", "as_of"))
        writer.writerows(rows)
    part.replace(target)
    return True


def fetch_date(fetched_csv: Path, files, sources: Path) -> str:
    """The fetch day in German form ("6.10.2026")."""
    return fetch_day(fetched_csv, files, sources).strftime("%-d.%-m.%Y")


def fetch_day(fetched_csv: Path, files, sources: Path) -> dt.date:
    """Download date of WFS data (statutes, plans): the oldest date of the files in sources/fetched.csv. The build
    writes it per language (Texts.date)."""
    with fetched_csv.open(encoding="utf-8", newline="") as f:  # csv: a URL may hold a comma and come quoted
        dates = {r["file"]: r["fetched"] for r in csv.DictReader(f)}
    names = [Path(f).relative_to(sources).as_posix() for f in files]
    missing = [n for n in names if n not in dates]
    if missing:
        raise ValueError(f"{fetched_csv.name} has no row for {missing}; run pipeline/update_sources.py")
    parsed = []
    for n in names:
        try:
            parsed.append(dt.date.fromisoformat(dates[n]))
        except (TypeError, ValueError):
            raise ValueError(f"{fetched_csv.name}: the date of {n} is {dates[n]!r}, expected YYYY-MM-DD; "
                             "run pipeline/update_sources.py") from None
    return min(parsed)
