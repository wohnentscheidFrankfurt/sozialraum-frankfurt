import pandas as pd
import pytest
import shapely

from pipeline import config
from pipeline.use_cases.flat_roofs import sources
from pipeline.use_cases.flat_roofs.model import find_roofs

POLY = ("<gml:Polygon><gml:exterior><gml:LinearRing><gml:posList>{c}</gml:posList></gml:LinearRing></gml:exterior>"
        "</gml:Polygon>")


def zone(art, city="Frankfurt am Main", state="B", x=0):
    ring = f"{x} 0 {x + 10} 0 {x + 10} 10 {x} 10 {x} 0"
    return (f"<wfs:member><boris:BR_BodenrichtwertZonal><adv:position>{POLY.format(c=ring)}</adv:position>"
            f"<boris:gemeinde><boris:BR_Gemeinde><boris:name>{city}</boris:name></boris:BR_Gemeinde></boris:gemeinde>"
            f"<boris:entwicklungszustand>{state}</boris:entwicklungszustand>"
            f"<boris:nutzung><boris:BR_Nutzung><boris:art>{art}</boris:art></boris:BR_Nutzung></boris:nutzung>"
            f"</boris:BR_BodenrichtwertZonal></wfs:member>")


def test_read_zones_keeps_housing_zones_of_frankfurt(tmp_path):
    text = "<wfs:FeatureCollection>" + "".join([
        zone("W", x=0), zone("MI", x=20), zone("GE", x=40), zone("SO", x=60), zone("W", city="Kriftel", x=80),
        zone("W", state="E", x=100)]) + "</wfs:FeatureCollection>"
    (tmp_path / "boris_1.gml").write_text(text, encoding="utf-8")
    zones = sources.read_zones(tmp_path)
    assert sorted(z.bounds[0] for z in zones) == [0.0, 20.0]


def test_read_parts_columns_and_geometry(tmp_path):
    path = tmp_path / "p.csv.gz"
    pd.DataFrame([
        {"building": "a", "function": "31001_2000", "gemarkung": "G", "created": 2020, "part": 0, "roof_type": "1000",
         "height_m": 4.5, "ground_m2": 100.0, "footprint": "0,0 10,0 10,10 0,10 0,0"},
        {"building": "b", "function": "31001_2740", "gemarkung": "G", "created": 2020, "part": 0, "roof_type": "3100",
         "height_m": None, "ground_m2": 4.0, "footprint": "0,0 2,0 2,2 0,2 0,0;5,5 7,5 7,7 5,7 5,5"},
    ]).to_csv(path, index=False)
    parts = sources.read_parts(path)
    assert list(parts.columns) == ["building", "use", "excluded", "flat", "height_m", "ground_m2", "gemarkung",
                                   "created", "geometry"]
    a, b = parts.iloc[0], parts.iloc[1]
    assert a.flat and not a.excluded and a.geometry.area == 100.0 and a.use == "31001_2000"
    assert not b.flat and b.excluded and pd.isna(b.height_m) and b.geometry.area == 8.0


def test_read_parts_makes_a_bow_tie_a_polygon(tmp_path):
    # a self-intersecting footprint: make_valid gives a MultiPolygon, plus a line where the ring touches itself
    path = tmp_path / "p.csv.gz"
    pd.DataFrame([
        {"building": "a", "function": "31001_2000", "gemarkung": "G", "created": 2020, "part": 0, "roof_type": "1000",
         "height_m": 4.5, "ground_m2": 50.0, "footprint": "0,0 10,10 10,0 0,10 0,0"},
        {"building": "b", "function": "31001_2000", "gemarkung": "G", "created": 2020, "part": 0, "roof_type": "1000",
         "height_m": 4.5, "ground_m2": 10.0, "footprint": "0,0 10,0 10,10 0,0 5,0 5,5 0,0"},
    ]).to_csv(path, index=False)
    parts = sources.read_parts(path)
    assert {g.geom_type for g in parts["geometry"]} <= {"Polygon", "MultiPolygon"}
    assert parts.geometry.iloc[0].area == pytest.approx(50.0)


def test_polygonal_drops_lines_and_points():
    mixed = shapely.GeometryCollection([shapely.box(0, 0, 2, 2), shapely.LineString([(5, 5), (6, 6)]), shapely.Point(9, 9)])
    assert sources._polygonal(mixed).equals(shapely.box(0, 0, 2, 2))


def test_source_codes():
    assert sources.FLAT_ROOF == "1000"
    assert "31001_2740" in sources.EXCLUDED


CHECKS = {"DEHE06200001dzaY": ("31001_2000", 3084.6, 7.7), "DEHE06200001dyco": (None, 2381.3, 7.3),
          "DEHE06200001c4ew": ("31001_2000", 475.2, 6.4)}


def test_real_extract_keeps_the_check_values():
    if not config.LOD2_PARTS_CSV.exists():
        pytest.skip("LoD2 extract missing")
    parts = sources.read_parts(config.LOD2_PARTS_CSV)
    parts = parts[parts.building.isin(CHECKS)]
    roofs = {r.building: r for r in find_roofs(parts, [])}
    assert set(roofs) == set(CHECKS)
    for building, (use, area, height) in CHECKS.items():
        r = roofs[building]
        assert r.area_m2 == pytest.approx(area, abs=1) and r.height_m == pytest.approx(height, abs=0.1)
        if use:
            assert r.use == use


def test_read_zones_matches_land():
    from pipeline.use_cases.land import sources as land
    if not list(config.BORIS_DIR.glob("boris_*.gml")):
        pytest.skip("BORIS pages missing")
    ours = sorted(z.wkb_hex for z in sources.read_zones(config.BORIS_DIR))
    theirs = sorted(z.geom.wkb_hex for z in land.read_zones(config.BORIS_DIR))
    assert ours == theirs and len(ours) > 100


def test_real_extract_has_no_geometry_collection():
    if not config.LOD2_PARTS_CSV.exists():
        pytest.skip("LoD2 extract missing")
    parts = sources.read_parts(config.LOD2_PARTS_CSV)
    assert {g.geom_type for g in parts["geometry"]} <= {"Polygon", "MultiPolygon"}


def test_read_building_code_reads_the_synopsis_of_baupaket_i():
    from pipeline.use_cases.flat_roofs.checks import check_building_code
    pages = sources.read_building_code(config.HBO_SYNOPSIS_PDF)
    assert len(pages) == 14 and "Baupaket I" in pages[0] and "22.10.2025" in pages[0]
    assert check_building_code(pages).status == "OK"
