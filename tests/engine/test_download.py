import datetime as dt
import json
import os
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from pipeline import config
from pipeline.engine import download as dl
from pipeline.engine.download import (boris_value, download, download_boris, download_boris_values, download_table,
                                      fetch_url, table_url)


def test_download_only_when_needed(tmp_path):
    calls = []

    def fake(url):
        calls.append(url)
        return b"content"

    target = tmp_path / "a.csv"
    assert download("u", target, fetch=fake) is True
    assert download("u", target, fetch=fake) is False
    assert download("u", target, refresh=True, fetch=fake) is True
    assert len(calls) == 2 and target.read_bytes() == b"content"


def test_download_detects_an_error_page(tmp_path):
    with pytest.raises(RuntimeError, match="HTML page instead of data"):
        download("u", tmp_path / "x", fetch=lambda u: b"<html><title>404 Nicht gefunden</title>")
    assert not (tmp_path / "x").exists()


def test_download_boris_pages_to_the_last_page(tmp_path):
    pages = [b'<x numberReturned="500">', b'<x numberReturned="500">', b'<x numberReturned="12">']
    urls = []

    def fake(url):
        urls.append(url)
        return pages[len(urls) - 1]

    paths = download_boris(tmp_path, "u", 500, fetch=fake)
    assert len(paths) == 3 and "STARTINDEX=1000" in urls[2]
    assert download_boris(tmp_path, "u", 500, fetch=lambda u: pytest.fail("second download")) == paths


def test_fetch_url_reports_curl_errors(monkeypatch):
    run = Mock(return_value=Mock(returncode=22, stderr=b"HTTP error 404"))
    monkeypatch.setattr(dl.subprocess, "run", run)
    monkeypatch.setattr(dl.time, "sleep", lambda seconds: None)
    with pytest.raises(RuntimeError, match="download failed.*https://example.com/test"):
        fetch_url("https://example.com/test")
    assert run.call_count == dl.ATTEMPTS


def test_fetch_url_tries_again_after_a_transient_error(monkeypatch):
    run = Mock(side_effect=[Mock(returncode=56, stderr=b"bad decrypt"), Mock(returncode=0, stdout=b"data")])
    monkeypatch.setattr(dl.subprocess, "run", run)
    monkeypatch.setattr(dl.time, "sleep", lambda seconds: None)
    assert fetch_url("https://example.com/test") == b"data"


def test_download_boris_tries_again_after_an_abort(tmp_path):
    pages = [b'<x numberReturned="500">', b'<x numberReturned="500">', b'<x numberReturned="12">']
    download_boris(tmp_path, "u", 500, fetch=lambda u: pages[len(list(tmp_path.glob("boris_*.gml")))])
    calls = []

    def failing(url):
        calls.append(url)
        if len(calls) <= 1:
            return b'<x numberReturned="500">'
        raise RuntimeError("error on page 2")

    with pytest.raises(RuntimeError):
        download_boris(tmp_path, "u", 500, refresh=True, fetch=failing)
    third = []

    def ok(url):
        third.append(url)
        return pages[len(third) - 1]

    download_boris(tmp_path, "u", 500, fetch=ok)
    assert third, "the done marker was stale, the download must run again"


def test_fetch_day_is_the_oldest_date_of_the_files(tmp_path):
    csv = tmp_path / "fetched.csv"
    csv.write_text("file,url,fetched\nf/a.gml,u,2026-10-08\nf/b.gml,u,2026-10-06\nz/c.csv,u,2026-01-01\n")
    assert dl.fetch_day(csv, (tmp_path / "f/a.gml", tmp_path / "f/b.gml"), tmp_path) == dt.date(2026, 10, 6)


def test_fetch_day_stops_on_a_file_without_a_row(tmp_path):
    csv = tmp_path / "fetched.csv"
    csv.write_text("file,url,fetched\nf/a.gml,u,2026-10-08\n")
    with pytest.raises(ValueError, match="f/b.gml"):
        dl.fetch_day(csv, (tmp_path / "f/a.gml", tmp_path / "f/b.gml"), tmp_path)


@pytest.mark.parametrize("cell", ["", "8.10.2026"])
def test_fetch_day_stops_on_an_empty_or_malformed_date(tmp_path, cell):
    csv = tmp_path / "fetched.csv"
    csv.write_text(f"file,url,fetched\nf/a.gml,u,2026-10-08\nf/b.gml,u,{cell}\n")
    with pytest.raises(ValueError, match=r"fetched\.csv.*f/b\.gml"):
        dl.fetch_day(csv, (tmp_path / "f/a.gml", tmp_path / "f/b.gml"), tmp_path)


ANSWER = """GetFeatureInfo results:

Layer 'hboris_feature'
  Feature 20031:
    WNUM = '43391089'
    BRW = '3100 EUR/m²'
    STAG = '01.01.2026'
  Feature 20032:
    WNUM = '43391012'
    BRW = '0,01 EUR/m²'
    STAG = '01.01.2026'
"""


def test_boris_value_takes_the_zone_with_the_same_number():
    assert boris_value(ANSWER, "43391089") == ("3100", "01.01.2026")
    assert boris_value(ANSWER, "43391012") == ("0.01", "01.01.2026")
    assert boris_value(ANSWER, "49999999") == ("", "")
    farmland = "Feature 1:\n    WNUM = '05480951'\n    BRW = 'landwirtschaftliche Fläche: 5 EUR/m²'\n    STAG = '01.01.2026'\n"
    assert boris_value(farmland, "05480951") == ("", "01.01.2026")  # no single value in €/m²
    assert boris_value("GetFeatureInfo results:\n\nSearch returned no results.", "1") == ("", "")


def test_download_boris_values_asks_each_point_once_and_writes_the_table(tmp_path):
    urls = []

    def fake(url):
        urls.append(url)
        return ANSWER.encode()

    target = tmp_path / "values.csv"
    points = [("43391089", 100.0, 200.0), ("49999999", 300.0, 400.0)]
    assert download_boris_values(points, "u?BBOX={x0},{y0},{x1},{y1}", target, fetch=fake) is True
    assert sorted(urls) == ["u?BBOX=299.5,399.5,300.5,400.5", "u?BBOX=99.5,199.5,100.5,200.5"]
    assert target.read_text().splitlines() == ["number,value,as_of", "43391089,3100,01.01.2026", "49999999,,"]
    assert download_boris_values(points, "u", target, fetch=lambda u: pytest.fail("second download")) is False


def test_download_boris_values_keeps_no_half_table(tmp_path):
    def failing(url):
        raise RuntimeError("timeout")

    with pytest.raises(RuntimeError):
        download_boris_values([("1", 0.0, 0.0)], "u{x0}{y0}{x1}{y1}", tmp_path / "v.csv", fetch=failing,
                              pause=0)
    assert not (tmp_path / "v.csv").exists()


def test_download_boris_values_retries_and_stops_on_an_answer_that_is_no_feature_info(tmp_path):
    calls = []

    def flaky(url):
        calls.append(url)
        return ANSWER.encode() if len(calls) == 3 else b"<ServiceExceptionReport>busy</ServiceExceptionReport>"

    target = tmp_path / "v.csv"
    assert download_boris_values([("43391089", 0.0, 0.0)], "u{x0}{y0}{x1}{y1}", target, fetch=flaky, pause=0)
    assert len(calls) == 3 and target.read_text().splitlines()[1] == "43391089,3100,01.01.2026"
    with pytest.raises(RuntimeError, match="no GetFeatureInfo answer"):
        download_boris_values([("1", 0.0, 0.0)], "u{x0}{y0}{x1}{y1}", tmp_path / "w.csv",
                              fetch=lambda u: b"", pause=0)
    assert not (tmp_path / "w.csv").exists()


def test_download_boris_values_loads_again_when_the_pages_are_newer(tmp_path):
    target = tmp_path / "v.csv"
    target.write_text("number,value,as_of\n")
    os.utime(target, (1000, 1000))
    fetched = download_boris_values([("43391089", 0.0, 0.0)], "u{x0}{y0}{x1}{y1}", target,
                                    fetch=lambda u: ANSWER.encode(), pages_time=2000)
    assert fetched and "43391089" in target.read_text()


def test_table_url_quotes_the_key():
    assert table_url("https://x/tables/", "4000W-1011", "4000W GEBEG1 GEOGM4") == \
        "https://x/tables/4000W-1011/data/4000W%20GEBEG1%20GEOGM4"


def test_download_table_stores_structure_and_answer_once(tmp_path):
    answers = {"https://x/T/structure": b'{"variableValues": {}}', "https://x/T/data/S%20K": b'{"data": []}'}
    fetch = Mock(side_effect=lambda url: answers[url])
    target = tmp_path / "tables" / "t.json"
    assert download_table("https://x/", "T", "S K", target, fetch=fetch) is True
    assert json.loads(target.read_text(encoding="utf-8")) == {"url": "https://x/T/data/S%20K",
                                                              "structure": {"variableValues": {}}, "data": {"data": []}}
    assert download_table("https://x/", "T", "S K", target, fetch=fetch) is False
    assert fetch.call_count == 2
    assert download_table("https://x/", "T", "S K", target, refresh=True, fetch=fetch) is True
    assert fetch.call_count == 4


@pytest.mark.parametrize("answers, message", [
    ({"structure": b"<html>error</html>"}, "no JSON from https://x/T/structure"),
    ({"structure": b'{"status": {"code": 104}}'}, "no variableValues in the answer of https://x/T/structure"),
    ({"structure": b'{"variableValues": {}}', "data": b'{"status": {"code": 104}}'},
     "no data in the answer of https://x/T/data/S%20K"),
    ({"structure": b'{"variableValues": {}}', "data": b"[]"}, "no data in the answer")], ids=["html", "error", "data",
                                                                                            "list"])
def test_download_table_keeps_the_old_file_on_an_error_answer(tmp_path, answers, message):
    target = tmp_path / "t.json"
    target.write_text("old")

    def fetch(url):
        return answers["structure" if url.endswith("/structure") else "data"]
    with pytest.raises(RuntimeError, match=message):
        download_table("https://x/", "T", "S K", target, refresh=True, fetch=fetch)
    assert target.read_text() == "old"
    assert [p.name for p in tmp_path.iterdir()] == ["t.json"]
