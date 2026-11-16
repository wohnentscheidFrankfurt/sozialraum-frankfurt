import datetime as dt
import json
import os

import pandas as pd
import pytest

from pipeline import config, update_sources
from pipeline.shared.readers.jsonstat import long_csv, long_rows


def test_fetched_rows_take_the_date_of_the_download(tmp_path):
    cache = tmp_path / "cache"
    cache.mkdir()
    (cache / "a.zip").write_bytes(b"x")
    t = dt.datetime(2026, 10, 8, 12).timestamp()
    os.utime(cache / "a.zip", (t, t))
    rows = update_sources.fetched_rows({"a.zip": "https://x/a.zip"}, {"a.zip": tmp_path / "sources" / "z" / "a.csv"},
                                       cache, tmp_path / "sources")
    assert rows == [{"file": "z/a.csv", "url": "https://x/a.zip", "fetched": "2026-10-08"}]


def test_merge_keeps_rows_of_other_files(tmp_path):
    old = pd.DataFrame([{"file": "b.gml", "url": "u", "fetched": "2026-10-01"},
                        {"file": "z/a.csv", "url": "u", "fetched": "2026-09-01"}])
    new = [{"file": "z/a.csv", "url": "u", "fetched": "2026-10-08"}]
    merged = update_sources.merge_fetched(old, new)
    assert merged.to_dict("records") == [{"file": "b.gml", "url": "u", "fetched": "2026-10-01"},
                                         {"file": "z/a.csv", "url": "u", "fetched": "2026-10-08"}]


def test_the_build_never_imports_the_tool():
    import pipeline.build
    assert "update_sources" not in open(pipeline.build.__file__, encoding="utf-8").read()


def table_answer(api, table, key):
    """A cached answer as download_table stores it: one content, two years, the region of the database."""
    region = "GEOGM4" if api == "https://z/" else "KREISE"
    dataset = {"id": ["statistic", "content", "JAHR", region], "size": [1, 1, 2, 1], "value": [7, 8],
               "dimension": {"statistic": {"category": {"index": ["S"]}}, "content": {"category": {"index": ["C$QMU"]}},
                             "JAHR": {"category": {"index": ["2024", "2023"]}}, region: {"category": {"index": ["06412"]}}}}
    return {"url": f"{api}{table}/data/{key.replace(' ', '%20')}", "structure": {"variableValues": {}},
            "data": {"data": [dataset]}}


def test_update_tables_downloads_again_when_the_key_changed(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "CACHE", tmp_path / "cache")
    monkeypatch.setattr(config, "SOURCES", tmp_path / "sources")
    cached = tmp_path / "cache" / "tables" / "Z.json"
    cached.parent.mkdir(parents=True)
    cached.write_text(json.dumps(table_answer("https://z/", "T1", "S1 OLD")))
    asked = []

    def fake_table(api, table, key, target, refresh=False):
        asked.append(refresh)
        if refresh:
            target.write_text(json.dumps(table_answer(api, table, key)))
        return refresh
    rows = update_sources.update_tables("https://z/", {tmp_path / "sources" / "zensus" / "Z.csv": ("T1", "S1 GEOGM4")},
                                        "06412", update_sources.ZENSUS_FORMAT, False, download=fake_table)
    assert asked == [False, True]
    assert rows[0]["url"] == "https://z/T1/data/S1%20GEOGM4"
    assert (tmp_path / "sources" / "zensus" / "Z.csv").exists()


ZONE_PAGE = ("<wfs:member><boris:BR_BodenrichtwertZonal><gml:Polygon><gml:exterior><gml:LinearRing><gml:posList>"
             "0 0 10 0 10 10 0 10 0 0</gml:posList></gml:LinearRing></gml:exterior></gml:Polygon>"
             "<boris:bodenrichtwertNummer>43391012</boris:bodenrichtwertNummer></boris:BR_BodenrichtwertZonal></wfs:member>")


def test_main_copies_snapshots_and_boris_pages_and_writes_their_rows(tmp_path, monkeypatch):
    from pipeline import config
    cache, sources = tmp_path / "cache", tmp_path / "sources"
    monkeypatch.setattr(config, "CACHE", cache)
    monkeypatch.setattr(config, "SOURCES", sources)
    monkeypatch.setattr(config, "GRID_EXTRACTS", {})
    monkeypatch.setattr(config, "GRID_KM_EXTRACTS", {})
    monkeypatch.setattr(config, "DOWNLOADS", {"a.gml": "https://x/a"})
    monkeypatch.setattr(config, "SNAPSHOTS", {"a.gml": sources / "city" / "planAS_a.gml"})
    monkeypatch.setattr(config, "BORIS_DIR", sources / "hessen" / "boris")
    monkeypatch.setattr(config, "BORIS_URL", "https://x/boris")
    monkeypatch.setattr(config, "BORIS_VALUES_URL", "https://x/wms?BBOX={x0},{y0},{x1},{y1}")
    monkeypatch.setattr(config, "BORIS_VALUES_CSV", sources / "hessen" / "boris" / "values_2026.csv")
    monkeypatch.setattr(config, "FETCHED_CSV", sources / "fetched.csv")
    monkeypatch.setattr(config, "ZENSUS_API", "https://z/")
    monkeypatch.setattr(config, "ZENSUS_REGION", "06412")
    monkeypatch.setattr(config, "ZENSUS_TABLES", {sources / "zensus" / "Z.csv": ("T1", "S1 GEOGM4")})
    monkeypatch.setattr(config, "REGIONAL_API", "https://r/")
    monkeypatch.setattr(config, "REGIONAL_REGION", "06412")
    monkeypatch.setattr(config, "REGIONAL_TABLES", {sources / "regionalstatistik" / "R.csv": ("T2", "S2 KREISE")})

    tables_asked = []

    def fake_table(api, table, key, target, refresh=False):
        tables_asked.append((table, target.relative_to(cache).as_posix(), refresh))
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(table_answer(api, table, key)))
        return True
    monkeypatch.setattr(update_sources, "download_table", fake_table)

    def fake_download(url, target, refresh=False):
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(url)
        return True

    def fake_boris(folder, url, page_size, refresh=False):
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "boris_00.gml").write_text(ZONE_PAGE)
        (folder / "done.txt").write_text("1")
        return [folder / "boris_00.gml"]
    (sources / "hessen" / "boris").mkdir(parents=True)
    (sources / "hessen" / "boris" / "boris_07.gml").write_text("old page")
    (sources / "fetched.csv").write_text("file,url,fetched\nhessen/boris/boris_07.gml,https://x/boris,2026-01-01\n")
    monkeypatch.setattr(update_sources, "download", fake_download)
    monkeypatch.setattr(update_sources, "download_boris", fake_boris)
    asked = []

    def fake_values(points, url, target, refresh=False, pages_time=0.0):
        asked.extend(points)
        target.write_text("number,value,as_of\n")
        return True
    monkeypatch.setattr(update_sources, "download_boris_values", fake_values)
    lod2_asked = []
    monkeypatch.setattr(update_sources, "update_lod2", lambda refresh: lod2_asked.append(refresh) or [
        {"file": "hessen/lod2/p.csv.gz", "url": "https://x/lod2.zip", "fetched": "2026-11-10"}])
    alkis_asked = []
    monkeypatch.setattr(update_sources, "update_alkis", lambda refresh: alkis_asked.append(refresh) or [
        {"file": "hessen/alkis/a.csv.gz", "url": "https://x/alkis.zip", "fetched": "2026-11-15"}])
    update_sources.main([])
    assert lod2_asked == [False] and alkis_asked == [False]
    assert [(n, round(x), round(y)) for n, x, y in asked] == [("43391012", 5, 5)]  # the inner point of the zone
    assert (sources / "city" / "planAS_a.gml").read_text() == "https://x/a"
    assert sorted(p.name for p in (sources / "hessen" / "boris").iterdir()) == ["boris_00.gml", "values_2026.csv"]
    rows = pd.read_csv(sources / "fetched.csv", dtype=str)
    assert rows[["file", "url"]].to_dict("records") == [
        {"file": "city/planAS_a.gml", "url": "https://x/a"},
        {"file": "hessen/alkis/a.csv.gz", "url": "https://x/alkis.zip"},
        {"file": "hessen/boris/boris_00.gml", "url": "https://x/boris"},
        {"file": "hessen/boris/values_2026.csv", "url": "https://x/wms?BBOX={x0},{y0},{x1},{y1}"},
        {"file": "hessen/lod2/p.csv.gz", "url": "https://x/lod2.zip"},
        {"file": "regionalstatistik/R.csv", "url": "https://r/T2/data/S2%20KREISE"},
        {"file": "zensus/Z.csv", "url": "https://z/T1/data/S1%20GEOGM4"}]
    assert tables_asked == [("T1", "tables/Z.json", False), ("T2", "tables/R.json", False)]
    assert (sources / "zensus" / "Z.csv").read_text().splitlines() == [
        "table;municipality;content;content_label;JAHR;JAHR_label;value;quality", "T1;06412;C$QMU;;2024;;7;",
        "T1;06412;C$QMU;;2023;;8;"]  # the order of the answer
    assert (sources / "regionalstatistik" / "R.csv").read_text().splitlines() == [
        "table;region;content;content_label;JAHR;JAHR_label;value;quality", "T2;06412;C$QMU;;2023;;8;",
        "T2;06412;C$QMU;;2024;;7;"]  # sorted by year


def test_update_lod2_writes_the_extracts_with_the_same_bytes_on_a_rerun(tmp_path, monkeypatch):
    from tests.shared.readers.test_citygml import FIXTURE, make_package
    cache, sources = tmp_path / "cache", tmp_path / "sources"
    for name, value in {"LOD2_API": "https://h/api", "LOD2_HOST": "https://h", "LOD2_DIR": sources / "lod2",
                        "LOD2_PARTS_CSV": sources / "lod2" / "parts.csv.gz",
                        "LOD2_GEMARKUNGEN_CSV": sources / "lod2" / "gem.csv", "SOURCES": sources,
                        "LOD2_PACKAGE": cache / "lod2" / "pkg.zip", "LOD2_LISTING": cache / "lod2" / "listing.json"
                        }.items():
        monkeypatch.setattr(config, name, value)
    package = make_package(tmp_path, {"Alt": FIXTURE.read_bytes()})
    asked = []

    def fake_download(url, target, refresh=False):
        asked.append((url, refresh))
        target.parent.mkdir(parents=True, exist_ok=True)
        if url == "https://h/api":
            target.write_text(json.dumps({"searchresult": {"packages": [
                {"downloadLink": {"uri": "/downloadcenter/2026 11/ä.zip"}}]}}))
        else:
            target.write_bytes(package.read_bytes())
        return True
    monkeypatch.setattr(update_sources, "download", fake_download)
    rows = update_sources.update_lod2(True)
    url = "https://h/downloadcenter/2026%2011/%C3%A4.zip"
    assert asked == [("https://h/api", True), (url, True)]
    assert [(r["file"], r["url"]) for r in rows] == [("lod2/parts.csv.gz", url), ("lod2/gem.csv", url)]
    first = (sources / "lod2" / "parts.csv.gz").read_bytes()
    assert (sources / "lod2" / "gem.csv").read_text().splitlines() == [
        "gemarkung,buildings,parsed,delivered", "Alt,3,3,2026-06-26"]
    update_sources.update_lod2(False)
    assert (sources / "lod2" / "parts.csv.gz").read_bytes() == first
    table = pd.read_csv(sources / "lod2" / "parts.csv.gz", dtype={"roof_type": str, "created": str})
    assert len(table) == 4 and table["building"].nunique() == 3


def test_update_alkis_writes_the_extracts_with_the_same_bytes_on_a_rerun(tmp_path, monkeypatch):
    import zipfile
    from tests.shared.readers.test_nas import FIXTURE
    cache, sources = tmp_path / "cache", tmp_path / "sources"
    alkis = sources / "alkis"
    values = {"LOD2_HOST": "https://h", "ALKIS_API": "https://h/alkis", "DOM_API": "https://h/dom",
              "DGM_API": "https://h/dgm", "SOURCES": sources, "ALKIS_DIR": alkis,
              "ALKIS_PARCELS_CSV": alkis / "p.csv.gz", "ALKIS_BUILDINGS_CSV": alkis / "b.csv.gz",
              "ALKIS_LANDUSE_CSV": alkis / "l.csv.gz", "ALKIS_META_CSV": alkis / "meta.csv",
              "BUILDING_GAPS_COVER_CSV": alkis / "cover.csv", "DOP_WMS": "https://w/ows", "DOP_CACHE": cache / "dop"}
    for key in ("ALKIS", "DOM", "DGM"):
        values[f"{key}_PACKAGE"] = cache / key.lower() / "pkg.zip"
        values[f"{key}_LISTING"] = cache / key.lower() / "listing.json"
    for name, value in values.items():
        monkeypatch.setattr(config, name, value)
    asked = []

    def fake_download(url, target, refresh=False):
        asked.append((url, refresh))
        target.parent.mkdir(parents=True, exist_ok=True)
        if url.startswith("https://h/") and "/" not in url[len("https://h/"):]:
            folder = url[len("https://h/"):]
            # as the real answers: every folder lists its one file under "downloads" (type File); ALKIS and DGM1 also
            # list a package "Alle Dateien …" (type Package, a ZIP holding the file's ZIP), DOM1 an empty "packages"
            file = [{"downloadType": "File", "downloadLink": {"uri": f"/dc/{folder} ä.zip"}}]
            package = [{"downloadType": "Package", "downloadLink": {"uri": f"/dc/PKT_{folder}.zip"}}]
            answer = {"packages": [] if folder == "dom" else package, "downloads": file}
            target.write_text(json.dumps({"searchresult": answer}))
        elif "alkis" in url:
            with zipfile.ZipFile(target, "w") as z:
                z.write(FIXTURE, "frankfurt.xml")
        else:
            target.write_bytes(b"zip")
        return True
    seen = {}

    def fake_candidates(parcels, buildings, landuse):
        seen["files"] = [pd.read_csv(p, dtype=str).shape for p in (parcels, buildings, landuse)]
        return ["gap"]

    def fake_measure(gaps, dom, dgm, wms, cache_dir, refresh):
        seen["measure"] = (gaps, dom, dgm, wms, cache_dir, refresh)
        return pd.DataFrame([{"gml_id": "g1", "px": 9, "building": 0.0, "tree": 0.1, "green": 0.2, "open": 0.7,
                              "nan_share": 0.0, "flight": "2025-08-19"}])
    monkeypatch.setattr(update_sources, "download", fake_download)
    monkeypatch.setattr(update_sources, "candidates_for_cover", fake_candidates)
    monkeypatch.setattr(update_sources, "measure_cover", fake_measure)
    rows = update_sources.update_alkis(True)
    url = "https://h/dc/alkis%20%C3%A4.zip"
    assert [a for a in asked if a[0].count("/") == 3] == [("https://h/alkis", True), ("https://h/dom", True),
                                                          ("https://h/dgm", True)]
    assert (url, True) in asked and ("https://h/dc/dom%20%C3%A4.zip", True) in asked
    assert ("https://h/dc/dgm%20%C3%A4.zip", True) in asked and not [a for a in asked if "PKT_" in a[0]]
    assert [(r["file"], r["url"]) for r in rows[:4]] == [(f"alkis/{n}", url) for n in
                                                         ("p.csv.gz", "b.csv.gz", "l.csv.gz", "meta.csv")]
    assert rows[4]["file"] == "alkis/cover.csv" and "https://w/ows" in rows[4]["url"]
    assert (alkis / "meta.csv").read_text().splitlines() == [
        "key,value", "portion_date,2026-11-04", "parcels,1", "buildings,1", "landuse,3", "cover_high_m,2.5",
        "cover_ndvi_green,0.2"]  # the thresholds the cover file was measured with (the check compares them)
    assert [shape[0] for shape in seen["files"]] == [1, 1, 3]
    assert seen["measure"][1:] == (config.DOM_PACKAGE, config.DGM_PACKAGE, "https://w/ows", cache / "dop", True)
    assert (alkis / "cover.csv").read_text().splitlines()[1] == "g1,9,0.0,0.1,0.2,0.7,0.0,2025-08-19"
    first = {p.name: p.read_bytes() for p in alkis.iterdir()}
    update_sources.update_alkis(False)
    assert {p.name: p.read_bytes() for p in alkis.iterdir()} == first


@pytest.mark.skipif(not (config.CACHE / "tables").is_dir(), reason="no cached answers in cache/tables/")
@pytest.mark.parametrize("tables, region, table_format", [
    (config.ZENSUS_TABLES, config.ZENSUS_REGION, update_sources.ZENSUS_FORMAT),
    (config.REGIONAL_TABLES, config.REGIONAL_REGION, update_sources.REGIONAL_FORMAT)], ids=["zensus", "regional"])
def test_cached_answers_give_the_extracts_in_sources_byte_for_byte(tables, region, table_format):
    """The extracts in sources/ are what the cached answers give; a change of the reader shows here."""
    region_var, region_column, order = table_format
    different = []
    for target, (table, _key) in tables.items():
        cached = config.CACHE / "tables" / f"{target.stem}.json"
        if not cached.exists():
            continue
        answer = json.loads(cached.read_text(encoding="utf-8"))
        rows = long_rows(answer["structure"], answer["data"], table, region_var, region, region_column)
        if long_csv(rows, order).encode("utf-8") != target.read_bytes():
            different.append(target.name)
    assert not different, different
