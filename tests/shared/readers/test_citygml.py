import io
import zipfile
from pathlib import Path

import pytest

from pipeline.shared.readers.citygml import extract_package, read_buildings, read_meta

FIXTURE = Path(__file__).parent / "fixtures" / "lod2_sample.gml"


def buildings(text: bytes | None = None):
    return list(read_buildings(io.BytesIO(FIXTURE.read_bytes() if text is None else text)))


def test_reads_parts_with_roof_type_height_and_area():
    a, b, c = buildings()
    assert (a.id, a.function, a.created) == ("DEHE_A", "31001_1000", "2020-03-14")
    assert [(p.roof_type, p.height_m, round(p.ground_m2, 6)) for p in a.parts] == [("1000", 6.4, 50.0),
                                                                                  ("3100", 15.0, 32.0)]
    assert (b.id, b.function) == ("DEHE_B", "31001_2463")
    assert (c.id, c.function, c.created) == ("DEHE_C", "51009_1610", "")


def test_building_without_parts_is_one_part():
    _, b, _ = buildings()
    assert [(p.roof_type, p.height_m, round(p.ground_m2, 6)) for p in b.parts] == [("1000", 3.0, 18.0)]
    assert b.parts[0].rings == (((478100.0, 5550100.0), (478106.0, 5550100.0), (478106.0, 5550103.0),
                                 (478100.0, 5550103.0), (478100.0, 5550100.0)),)


def test_part_without_ground_or_height_is_kept_empty():
    xml = (b'<core:CityModel xmlns:bldg="http://www.opengis.net/citygml/building/1.0" '
           b'xmlns:gml="http://www.opengis.net/gml" xmlns:core="http://www.opengis.net/citygml/1.0">'
           b'<bldg:Building gml:id="X"><bldg:function>31001_1000</bldg:function></bldg:Building></core:CityModel>')
    (building,) = buildings(xml)
    assert building.parts == (type(building.parts[0])("", None, 0.0, ()),)


def test_read_meta():
    assert read_meta("Land: HE\nAnzahl der 3D-Gebäude: 1060\nKoordinaten: x\nLieferdatum: 2026-06-26\n") \
        == (1060, "2026-06-26")
    with pytest.raises(ValueError):
        read_meta("Land: HE\nLieferdatum: 2026-06-26\n")


def make_package(tmp_path: Path, gmls: dict[str, bytes], counts: dict[str, int] | None = None) -> Path:
    package = tmp_path / "package.zip"
    with zipfile.ZipFile(package, "w") as outer:
        for name, gml in gmls.items():
            inner = io.BytesIO()
            with zipfile.ZipFile(inner, "w") as z:
                z.writestr(f"{name}-LoD2.gml", gml)
                n = (counts or {}).get(name, gml.count(b"<bldg:Building "))
                z.writestr(f"{name}-LoD2.txt", f"Land: HE\nAnzahl der 3D-Gebäude: {n}\nLieferdatum: 2026-06-26\n")
            outer.writestr(f"{name}-LoD2.zip", inner.getvalue())
    return package


def test_extract_dedupes_identical_copies(tmp_path):
    gml = FIXTURE.read_bytes()
    rows, gemarkungen = extract_package(make_package(tmp_path, {"Alt": gml, "Neu": gml}))
    assert [(r["building"], r["gemarkung"], r["part"]) for r in rows] == [
        ("DEHE_A", "Alt", 0), ("DEHE_A", "Alt", 1), ("DEHE_B", "Alt", 0), ("DEHE_C", "Alt", 0)]
    assert gemarkungen == [{"gemarkung": "Alt", "buildings": 3, "parsed": 3, "delivered": "2026-06-26"},
                           {"gemarkung": "Neu", "buildings": 3, "parsed": 3, "delivered": "2026-06-26"}]
    first = rows[0]
    assert (first["function"], first["created"], first["roof_type"], first["height_m"], first["ground_m2"]) == (
        "31001_1000", "2020", "1000", 6.4, 50.0)
    assert rows[3]["created"] == ""


def test_extract_raises_on_differing_copies(tmp_path):
    gml = FIXTURE.read_bytes()
    other = gml.replace(b"15.0</bldg:measuredHeight>", b"15.5</bldg:measuredHeight>")
    with pytest.raises(ValueError, match="DEHE_A differs between Alt and Neu"):
        extract_package(make_package(tmp_path, {"Alt": gml, "Neu": other}))


def test_footprint_rounds_to_decimetres(tmp_path):
    rows, _ = extract_package(make_package(tmp_path, {"Alt": FIXTURE.read_bytes()}))
    assert rows[0]["footprint"] == "478000.0,5550000.1 478010.0,5550000.1 478010.0,5550005.1 " \
                                   "478000.0,5550005.1 478000.0,5550000.1"
    assert rows[1]["footprint"].startswith("478010.1,5550000.0 ")
