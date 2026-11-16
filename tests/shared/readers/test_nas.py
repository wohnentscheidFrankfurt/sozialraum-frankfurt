import zipfile
from pathlib import Path

import pytest
from shapely import wkt

from pipeline.shared.readers.nas import LANDUSE_CLASSES, extract_package, read_nas

FIXTURE = Path(__file__).parent / "fixtures" / "nas_small.xml"


def _read():
    with FIXTURE.open("rb") as stream:
        return read_nas(stream)


def test_reads_parcels_buildings_and_landuse_of_the_fixture():
    extract = _read()
    assert (len(extract.parcels), len(extract.buildings), len(extract.landuse)) == (1, 1, 3)
    parcel = extract.parcels.iloc[0]
    assert parcel["kz"] == "060498007003350049__"
    assert parcel["official_m2"] == 1100.0
    assert parcel["created"] == "2019-05-02"
    assert parcel["addresses"] == 2
    assert extract.buildings.iloc[0]["function"] == "1313"
    platz = extract.landuse[extract.landuse["cls"] == "Platz"].iloc[0]
    assert platz["function"] == "5310"
    wald = extract.landuse[extract.landuse["cls"] == "Wald"].iloc[0]
    assert wald["function"] == ""
    assert {"Wald", "Platz"} <= LANDUSE_CLASSES and len(LANDUSE_CLASSES) == 22


def test_ring_keeps_segment_order_and_closes():
    platz = _read().landuse.query("cls == 'Platz'").iloc[0]
    geometry = wkt.loads(platz["wkt"])
    assert geometry.geom_type == "MultiPolygon"
    assert abs(geometry.area - 20 * 5) < 0.01
    ring = list(geometry.geoms[0].exterior.coords)
    assert ring[0] == ring[-1] and len(ring) == 5


def test_interior_ring_is_a_hole():
    geometry = wkt.loads(_read().parcels.iloc[0]["wkt"])
    assert abs(geometry.area - (40 * 30 - 10 * 10)) < 0.01
    assert len(geometry.geoms[0].interiors) == 1


def test_portion_date_is_iso():
    assert _read().portion_date == "2026-11-04"


def test_extract_package_reads_the_xml_inside_the_zip(tmp_path):
    package = tmp_path / "alkis.zip"
    with zipfile.ZipFile(package, "w") as z:
        z.write(FIXTURE, "frankfurt.xml")
    extract = extract_package(package)
    assert len(extract.parcels) == 1 and extract.portion_date == "2026-11-04"


def test_arc_becomes_a_dense_half_circle():
    weg = _read().landuse.query("cls == 'Weg'").iloc[0]
    geometry = wkt.loads(weg["wkt"])
    assert abs(geometry.area - 3.141592653589793 * 100 / 2) < 0.5
    assert geometry.is_valid and len(geometry.geoms[0].exterior.coords) > 30
    assert geometry.bounds[3] - geometry.bounds[1] > 9.9  # bulges to the mid point, not to the other side


def test_collinear_arc_stays_straight():
    from pipeline.shared.readers.nas import _densify_arc
    assert _densify_arc((0.0, 0.0), (5.0, 0.0), (10.0, 0.0)) == [(0.0, 0.0), (5.0, 0.0), (10.0, 0.0)]


@pytest.mark.parametrize("names", [[], ["a.xml", "b.xml"]])
def test_extract_package_needs_exactly_one_xml(tmp_path, names):
    package = tmp_path / "alkis.zip"
    with zipfile.ZipFile(package, "w") as z:
        z.writestr("inner.zip", b"zip")  # the package "Alle Dateien" holds a ZIP, no XML
        for name in names:
            z.write(FIXTURE, name)
    with pytest.raises(ValueError, match=f"{len(names)} XML files"):
        extract_package(package)
