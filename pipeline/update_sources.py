"""By hand, never a step: downloads the raw sources into cache/ and writes what the build reads into sources/: the
Frankfurt extracts of the Zensus grids, unchanged copies of the election files, of the planAS WFS layers and of the
BORIS pages, the BORIS values of 2026 per zone, the two LoD2 extracts of the 3D building model, the ALKIS extracts and the cover classes of the building gap
candidates, the long CSV of the tables of the Zensus database and the Regionaldatenbank (sources/README.md), and sources/fetched.csv (file, URL, date of the download).

  .venv/bin/python -I -m pipeline.update_sources            # download what is missing, write every extract
  .venv/bin/python -I -m pipeline.update_sources --refresh  # download everything again

sources/fetched.csv is written at the end. A run that fails half way can leave newer snapshot files with the old
fetch date. A rerun repairs it.
"""
from __future__ import annotations

import argparse
import datetime as dt
import gzip
import json
import shutil
import urllib.parse
from pathlib import Path

import pandas as pd

from pipeline import config
from pipeline.engine.download import download, download_boris, download_boris_values, download_table, table_url
from pipeline.shared.readers.citygml import extract_package
from pipeline.shared.readers.gml import parse_features
from pipeline.shared.readers.jsonstat import long_csv, long_rows
from pipeline.shared.readers.nas import extract_package as extract_alkis
from pipeline.use_cases.building_gaps.sources import COVER_THRESHOLDS, candidates_for_cover, measure_cover
from pipeline.shared.zensus.sources import (FEATURES_2011_ALL, GRID_FILES, GRID_KM_COLUMNS, extract_grid_2011,
                                            extract_grid_2022, extract_grid_km_2022)

GRID_2011 = {"zensus2011_dwellings.zip": "dwellings", "zensus2011_buildings.zip": "buildings"}
# region variable, region column and row order of the long CSV of each database (sources/README.md)
ZENSUS_FORMAT = ("GEOGM4", "municipality", ())
REGIONAL_FORMAT = ("KREISE", "region", ("content", "JAHR", "GEBWH1"))


def fetched_rows(urls: dict[str, str], targets: dict[str, Path], cache: Path, sources: Path) -> list[dict]:
    """One row per target: its path below sources/, the URL and the date of the file in cache/."""
    return [{"file": targets[name].relative_to(sources).as_posix(), "url": urls[name],
             "fetched": dt.date.fromtimestamp((cache / name).stat().st_mtime).isoformat()} for name in targets]


def merge_fetched(old: pd.DataFrame, new: list[dict]) -> pd.DataFrame:
    """Rows of new replace the rows of the same file; the result is sorted by file."""
    new_frame = pd.DataFrame(new, columns=["file", "url", "fetched"])
    keep = old[~old["file"].isin(new_frame["file"])] if len(old) else old
    return pd.concat([keep, new_frame], ignore_index=True).sort_values("file").reset_index(drop=True)


def update_tables(api: str, tables: dict[Path, tuple[str, str]], region: str, table_format: tuple, refresh: bool,
                  download=None) -> list[dict]:
    """Downloads each table into cache/tables/ and writes its long CSV of the region into sources/. A cached answer
    of another key is downloaded again. Returns the rows of sources/fetched.csv: the URL of the data request and the
    date of the download."""
    region_var, region_column, order = table_format
    download = download or download_table
    cache = config.CACHE / "tables"
    rows = []
    for target, (table, key) in tables.items():
        cached, url = cache / f"{target.stem}.json", table_url(api, table, key)
        loaded = download(api, table, key, cached, refresh)
        answer = json.loads(cached.read_text(encoding="utf-8"))
        if answer.get("url") != url:  # the key changed since the download
            loaded = download(api, table, key, cached, True)
            answer = json.loads(cached.read_text(encoding="utf-8"))
        found = long_rows(answer["structure"], answer["data"], table, region_var, region, region_column)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(long_csv(found, order).encode("utf-8"))
        print(f"{'loaded' if loaded else 'cached'} {table}: {len(found)} rows -> {target.relative_to(config.SOURCES)}")
        rows += fetched_rows({cached.name: url}, {cached.name: target}, cache, config.SOURCES)
    return rows


def update_lod2(refresh: bool) -> list[dict]:
    """Asks the download center of the HVBG for the package of the LoD2 of Frankfurt, downloads it into cache/lod2/
    and writes the two extracts of the reader into sources/hessen/lod2/. The same input gives the same bytes: the
    gzip header holds no time. Returns the rows of sources/fetched.csv: the URL of the package for both files."""
    download(config.LOD2_API, config.LOD2_LISTING, refresh)
    uri = json.loads(config.LOD2_LISTING.read_text(encoding="utf-8"))["searchresult"]["packages"][0]["downloadLink"]["uri"]
    url = config.LOD2_HOST + urllib.parse.quote(uri)
    loaded = download(url, config.LOD2_PACKAGE, refresh)
    parts, gemarkungen = extract_package(config.LOD2_PACKAGE)
    config.LOD2_DIR.mkdir(parents=True, exist_ok=True)
    parts_csv = pd.DataFrame(parts).to_csv(index=False, lineterminator="\n")
    config.LOD2_PARTS_CSV.write_bytes(gzip.compress(parts_csv.encode("utf-8"), mtime=0))
    pd.DataFrame(gemarkungen).to_csv(config.LOD2_GEMARKUNGEN_CSV, index=False, lineterminator="\n")
    print(f"{'loaded' if loaded else 'cached'} LoD2: {len({r['building'] for r in parts})} buildings, {len(parts)} parts, "
          f"{len(gemarkungen)} Gemarkungen -> {config.LOD2_DIR.relative_to(config.SOURCES)}")
    name = config.LOD2_PACKAGE.name
    return fetched_rows({name: url}, {name: config.LOD2_PARTS_CSV}, config.LOD2_PACKAGE.parent, config.SOURCES) \
        + fetched_rows({name: url}, {name: config.LOD2_GEMARKUNGEN_CSV}, config.LOD2_PACKAGE.parent, config.SOURCES)


def package_url(api: str, listing: Path, refresh: bool) -> str:
    """Asks the download center for the file of a folder and returns its URL. The answer lists the file under
    `downloads` (type "File": the ZIP with the XML or the tiles at its root). ALKIS and DGM1 also list a package
    "Alle Dateien …" under `packages`: a ZIP that holds the file's ZIP. It is not taken."""
    download(api, listing, refresh)
    result = json.loads(listing.read_text(encoding="utf-8"))["searchresult"]
    files = [d for d in result.get("downloads") or [] if d.get("downloadType") == "File"]
    if len(files) != 1:
        raise ValueError(f"{listing}: {len(files)} files of type File, expected 1")
    return config.LOD2_HOST + urllib.parse.quote(files[0]["downloadLink"]["uri"])


def _gzip_csv(frame: pd.DataFrame, target: Path) -> None:
    target.write_bytes(gzip.compress(frame.to_csv(index=False, lineterminator="\n").encode("utf-8"), mtime=0))


def update_alkis(refresh: bool) -> list[dict]:
    """Downloads the packages of ALKIS (NAS), DOM1 and DGM1 into cache/ and writes into sources/hessen/alkis/ the
    three ALKIS extracts, their meta file and the cover classes of the geometry candidates of building gaps (height
    model and orthophoto enter only that file). The same input gives the same bytes. Returns the rows of
    sources/fetched.csv."""
    alkis_url = package_url(config.ALKIS_API, config.ALKIS_LISTING, refresh)
    dom_url = package_url(config.DOM_API, config.DOM_LISTING, refresh)
    dgm_url = package_url(config.DGM_API, config.DGM_LISTING, refresh)
    loaded = download(alkis_url, config.ALKIS_PACKAGE, refresh)
    download(dom_url, config.DOM_PACKAGE, refresh)
    download(dgm_url, config.DGM_PACKAGE, refresh)
    extract = extract_alkis(config.ALKIS_PACKAGE)
    config.ALKIS_DIR.mkdir(parents=True, exist_ok=True)
    _gzip_csv(extract.parcels, config.ALKIS_PARCELS_CSV)
    _gzip_csv(extract.buildings, config.ALKIS_BUILDINGS_CSV)
    _gzip_csv(extract.landuse, config.ALKIS_LANDUSE_CSV)
    meta = {"portion_date": extract.portion_date, "parcels": len(extract.parcels),
            "buildings": len(extract.buildings), "landuse": len(extract.landuse), **COVER_THRESHOLDS}
    pd.DataFrame({"key": list(meta), "value": list(meta.values())}).to_csv(config.ALKIS_META_CSV, index=False,
                                                                           lineterminator="\n")
    gaps = candidates_for_cover(config.ALKIS_PARCELS_CSV, config.ALKIS_BUILDINGS_CSV, config.ALKIS_LANDUSE_CSV)
    cover = measure_cover(gaps, config.DOM_PACKAGE, config.DGM_PACKAGE, config.DOP_WMS, config.DOP_CACHE, refresh)
    cover.to_csv(config.BUILDING_GAPS_COVER_CSV, index=False, lineterminator="\n")
    print(f"{'loaded' if loaded else 'cached'} ALKIS {extract.portion_date}: {len(extract.parcels)} parcels, "
          f"{len(extract.buildings)} buildings, {len(extract.landuse)} land use areas, {len(cover)} candidates "
          f"-> {config.ALKIS_DIR.relative_to(config.SOURCES)}")
    name = config.ALKIS_PACKAGE.name
    package = config.ALKIS_PACKAGE.parent
    rows = []
    for target in (config.ALKIS_PARCELS_CSV, config.ALKIS_BUILDINGS_CSV, config.ALKIS_LANDUSE_CSV,
                   config.ALKIS_META_CSV):
        rows += fetched_rows({name: alkis_url}, {name: target}, package, config.SOURCES)
    # the cover file comes from the three packages and the orthophoto service; its date is the date of this run
    rows.append({"file": config.BUILDING_GAPS_COVER_CSV.relative_to(config.SOURCES).as_posix(),
                 "url": f"{dom_url} {dgm_url} {config.DOP_WMS}", "fetched": dt.date.today().isoformat()})
    return rows


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--refresh", action="store_true", help="download everything again")
    args = ap.parse_args(argv)
    for name, target in config.GRID_EXTRACTS.items():
        loaded = download(config.DOWNLOADS[name], config.CACHE / name, args.refresh)
        zip_path = config.CACHE / name
        rows = (extract_grid_2011(zip_path, target, FEATURES_2011_ALL[GRID_2011[name]]) if name in GRID_2011
                else extract_grid_2022(zip_path, target, GRID_FILES[name]))
        print(f"{'loaded' if loaded else 'cached'} {name}: {rows} rows -> {target.relative_to(config.SOURCES)}")
    for name, target in config.GRID_KM_EXTRACTS.items():
        loaded = download(config.DOWNLOADS[name], config.CACHE / name, args.refresh)
        rows = extract_grid_km_2022(config.CACHE / name, target, GRID_KM_COLUMNS[name])
        print(f"{'loaded' if loaded else 'cached'} {name}: {rows} rows -> {target.relative_to(config.SOURCES)}")
    for name, target in config.SNAPSHOTS.items():
        loaded = download(config.DOWNLOADS[name], config.CACHE / name, args.refresh)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(config.CACHE / name, target)  # copy2 keeps the file time
        print(f"{'loaded' if loaded else 'cached'} {name} -> {target.relative_to(config.SOURCES)}")
    pages = download_boris(config.CACHE / "boris", config.BORIS_URL, config.BORIS_PAGE_SIZE, args.refresh)
    config.BORIS_DIR.mkdir(parents=True, exist_ok=True)
    for old_page in config.BORIS_DIR.glob("boris_*.gml"):
        old_page.unlink()
    for page in pages:
        shutil.copy2(page, config.BORIS_DIR / page.name)
    print(f"BORIS: {len(pages)} pages -> {config.BORIS_DIR.relative_to(config.SOURCES)}")
    points = [(f.props["bodenrichtwertNummer"], *f.geom.representative_point().coords[0])
              for page in pages for f in parse_features(page.read_text(encoding="utf-8")) if f.geom is not None]
    cached = config.CACHE / "boris" / config.BORIS_VALUES_CSV.name
    pages_time = (config.CACHE / "boris" / "done.txt").stat().st_mtime  # new pages: ask for their values again
    loaded = download_boris_values(points, config.BORIS_VALUES_URL, cached, args.refresh, pages_time=pages_time)
    shutil.copy2(cached, config.BORIS_VALUES_CSV)
    print(f"{'loaded' if loaded else 'cached'} BORIS values of {len(points)} zones -> "
          f"{config.BORIS_VALUES_CSV.relative_to(config.SOURCES)}")
    tables = update_tables(config.ZENSUS_API, config.ZENSUS_TABLES, config.ZENSUS_REGION, ZENSUS_FORMAT, args.refresh)
    tables += update_tables(config.REGIONAL_API, config.REGIONAL_TABLES, config.REGIONAL_REGION, REGIONAL_FORMAT,
                            args.refresh)
    old = (pd.read_csv(config.FETCHED_CSV, dtype=str) if config.FETCHED_CSV.exists()
           else pd.DataFrame(columns=["file", "url", "fetched"]))
    boris = config.BORIS_DIR.relative_to(config.SOURCES).as_posix() + "/"
    old = old[~old["file"].str.startswith(boris)]  # the pages of the last run replace all earlier pages
    rows = fetched_rows(config.DOWNLOADS, config.GRID_EXTRACTS | config.SNAPSHOTS, config.CACHE, config.SOURCES)
    rows += fetched_rows(config.DOWNLOADS, config.GRID_KM_EXTRACTS, config.CACHE, config.SOURCES)  # same ZIPs as above
    boris_date = dt.date.fromtimestamp((config.CACHE / "boris" / "done.txt").stat().st_mtime).isoformat()
    rows += [{"file": (config.BORIS_DIR / p.name).relative_to(config.SOURCES).as_posix(), "url": config.BORIS_URL,
              "fetched": boris_date} for p in pages]
    rows += fetched_rows({cached.name: config.BORIS_VALUES_URL}, {cached.name: config.BORIS_VALUES_CSV},
                         cached.parent, config.SOURCES)
    new = rows + tables + update_lod2(args.refresh) + update_alkis(args.refresh)
    merge_fetched(old, new).to_csv(config.FETCHED_CSV, index=False)


if __name__ == "__main__":
    main()
