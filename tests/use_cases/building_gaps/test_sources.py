import pandas as pd

from pipeline.use_cases.building_gaps import sources

X0, Y0 = 477000, 5550000


def wkt(w, h, x=0):
    x0, y0 = X0 + x, Y0
    return (f"MULTIPOLYGON((({x0} {y0},{x0 + w} {y0},{x0 + w} {y0 + h},{x0} {y0 + h},{x0} {y0})))")


def test_read_buildings_marks_minor_and_tiny_buildings(tmp_path):
    path = tmp_path / "buildings.csv.gz"
    pd.DataFrame({"gml_id": ["house", "garage", "shed", "bowtie"], "function": ["1000", "2460", "1000", "1000"],
                  "wkt": [wkt(10, 10), wkt(10, 10, 20), wkt(5, 5, 40),
                          f"MULTIPOLYGON((({X0} {Y0},{X0 + 10} {Y0 + 10},{X0} {Y0 + 10},{X0 + 10} {Y0},{X0} {Y0})))"]}
                 ).to_csv(path, index=False)
    out = sources.read_buildings(path).set_index("gml_id")
    assert out.main["house"] and not out.main["garage"] and not out.main["shed"]
    assert out.geometry["bowtie"].is_valid


def test_read_landuse_marks_housing_and_access(tmp_path):
    path = tmp_path / "landuse.csv.gz"
    rows = [("a", "Wohnbauflaeche", ""), ("b", "FlaecheGemischterNutzung", ""), ("c", "Strassenverkehr", "2312"),
            ("d", "Weg", ""), ("e", "Platz", "5310"), ("f", "Platz", "5320"), ("g", "Gehoelz", "")]
    pd.DataFrame({"gml_id": [r[0] for r in rows], "cls": [r[1] for r in rows], "function": [r[2] for r in rows],
                  "wkt": [wkt(10, 10)] * len(rows)}).to_csv(path, index=False)
    out = sources.read_landuse(path).set_index("gml_id")
    assert out.housing.to_dict() == dict(a=True, b=True, c=False, d=False, e=False, f=False, g=False)
    assert out.access.to_dict() == dict(a=False, b=False, c=True, d=True, e=False, f=True, g=False)


def test_read_parcels(tmp_path):
    path = tmp_path / "parcels.csv.gz"
    pd.DataFrame({"gml_id": ["p"], "kz": ["06051204200104______"], "official_m2": [100.5], "created": ["1990-01-01"],
                  "addresses": [2], "wkt": [wkt(10, 10)]}).to_csv(path, index=False)
    out = sources.read_parcels(path)
    assert list(out.columns) == ["gml_id", "kz", "official_m2", "created", "addresses", "geometry"]
    assert out.kz[0] == "06051204200104______" and out.addresses[0] == 2 and out.official_m2[0] == 100.5


def test_flight_date_reads_bildflug():
    text = "Layer 'he_dop_rgb_info'\n  Feature 1: \n    name = 'dop_478000_5550500'\n    bildflug = '19-08-2025'\n    aenderung = '12-10-2026'\n"
    assert sources.flight_date(text) == "2025-08-19"
    assert sources.flight_date("no feature") == ""


def test_urls():
    url = sources.getmap_url("http://w/ows", "he_dop20_cir", 10, 20, 15, 28)
    assert "CRS=EPSG:25832" in url and "BBOX=10,20,15,28" in url and "WIDTH=5" in url and "HEIGHT=8" in url
    assert "LAYERS=he_dop20_cir" in url and "FORMAT=image/png" in url and "VERSION=1.3.0" in url
    info = sources.info_url("http://w/ows", 10.5, 20.5)
    assert "INFO_FORMAT=text/plain" in info and "QUERY_LAYERS=he_dop_rgb_info" in info and "BBOX=-40,-30,60,70" in info and "I=50&J=49" in info
    assert sources.dom_name(477, 5550) == "DOM1_32_477_5550_1_he.tif"
    assert sources.dgm_name(477, 5550) == "DGM1_32_477_5550_1_he.tif"


def _zip(path, prefix, value):
    import io
    import zipfile

    import numpy as np
    import tifffile
    buf = io.BytesIO()
    tifffile.imwrite(buf, np.full((1000, 1000), value, dtype=np.float32))
    with zipfile.ZipFile(path, "w") as z:
        z.writestr(f"{prefix}_32_477_5550_1_he.tif", buf.getvalue())


def test_measure_cover_uses_the_cache_and_the_fake_download(tmp_path):
    import numpy as np
    import pymupdf
    import shapely
    from pipeline.use_cases.building_gaps.model import Gap
    _zip(tmp_path / "dom.zip", "DOM1", 100.0)
    _zip(tmp_path / "dgm.zip", "DGM1", 98.0)  # nDOM 2 m: below HIGH_M
    calls = []

    def fake(url, target, refresh=False):
        if target.exists() and not refresh:
            return False
        calls.append(target.name)
        if target.name.endswith(".png"):
            samples = np.zeros((15, 15, 3), dtype=np.uint8)
            samples[..., 0], samples[..., 1] = 200, 100  # NDVI 1/3: green
            target.write_bytes(pymupdf.Pixmap(pymupdf.csRGB, 15, 15, samples.tobytes(), False).tobytes("png"))
        else:
            target.write_text("    bildflug = '19-08-2025'\n")
        return True

    def gap(gid, x):
        g = shapely.box(X0 + x, Y0 + 5, X0 + x + 10, Y0 + 15)
        return Gap(gid, gid, 100.0, 10, 0, "free", "", 1, g, X0 + x + 5, Y0 + 10)

    gaps = [gap("b", 0), gap("a", 0)]
    cache = tmp_path / "cache"
    for _ in range(2):
        out = sources.measure_cover(gaps, tmp_path / "dom.zip", tmp_path / "dgm.zip", "http://w/ows", cache, False, fake)
    assert list(out.columns) == ["gml_id", "px", "building", "tree", "green", "open", "nan_share", "flight"]
    assert out.gml_id.tolist() == ["a", "b"]
    assert out.px.tolist() == [100, 100] and out.green.tolist() == [1.0, 1.0] and out.flight[0] == "2025-08-19"
    assert len(calls) == 4  # the second call hits the cache


def test_cache_stems_differ_for_ids_that_differ_only_in_case():
    """A case-insensitive file system (macOS) must not give two gml_ids the same cache file."""
    stems = {sources.cache_stem(i) for i in ("DEHE06200001eOaZ", "DEHE06200001eOaz")}
    assert len(stems) == 2 and all(s == s.lower() for s in stems)


def test_kz_parts_with_and_without_nenner():
    assert sources.kz_parts("060503024000420001__") == {"gemarkung": "0503", "flur": "24", "number": "42/1"}
    assert sources.kz_parts("06051204200104______") == {"gemarkung": "0512", "flur": "42", "number": "104"}


def test_read_cover_indexes_by_gml_id(tmp_path):
    path = tmp_path / "cover.csv"
    path.write_text("gml_id,px,building,tree,green,open,nan_share,flight\nA,10,0.1,0.2,0.3,0.4,0.0,2025-08-19\n")
    out = sources.read_cover(path)
    assert out.index.name == "gml_id" and out.loc["A", "open"] == 0.4 and out.loc["A", "flight"] == "2025-08-19"


def test_read_verdicts_accepts_a_header_only_file(tmp_path):
    path = tmp_path / "v.csv"
    path.write_text("gml_id,kz,verdict,reason,note,checked,by\n")
    out = sources.read_verdicts(path)
    assert out.columns.tolist() == ["gml_id", "kz", "verdict", "reason", "note", "checked", "by"] and out.empty
    path.write_text("gml_id,kz,verdict,reason,note,checked,by\nA,k,not,green,,2026-11-15,aerial\n")
    assert sources.read_verdicts(path).loc[0, "note"] == ""


def test_read_zones_equals_flat_roofs():
    import pytest
    from pipeline import config
    from pipeline.use_cases.flat_roofs import sources as flat_roofs
    if not list(config.BORIS_DIR.glob("boris_*.gml")):
        pytest.skip("BORIS pages missing")
    ours = sorted(z.wkb_hex for z in sources.read_zones(config.BORIS_DIR))
    theirs = sorted(z.wkb_hex for z in flat_roofs.read_zones(config.BORIS_DIR))
    assert ours == theirs and len(ours) > 100


def test_read_meta(tmp_path):
    from pipeline.use_cases.building_gaps.sources import read_meta
    path = tmp_path / "meta.csv"
    path.write_text("key,value\nportion_date,2026-11-04\nparcels,174650\n", encoding="utf-8")
    assert read_meta(path) == {"portion_date": "2026-11-04", "parcels": "174650"}
