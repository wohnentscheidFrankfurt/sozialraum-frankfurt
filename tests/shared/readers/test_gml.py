import pytest

from pipeline.shared.readers.gml import count_with_area, parse_features, read_features

GML32 = """<wfs:FeatureCollection><wfs:member><x:Bezirk><x:STBZ_ID>10</x:STBZ_ID><x:STBZ_NAME>Alt&amp;stadt</x:STBZ_NAME>
<x:SHAPE><gml:MultiSurface><gml:surfaceMember><gml:Polygon gml:id="p1"><gml:exterior><gml:LinearRing>
<gml:posList>0 0 10 0 10 10 0 10 0 0</gml:posList></gml:LinearRing></gml:exterior><gml:interior><gml:LinearRing>
<gml:posList>2 2 4 2 4 4 2 4 2 2</gml:posList></gml:LinearRing></gml:interior></gml:Polygon></gml:surfaceMember>
</gml:MultiSurface></x:SHAPE></x:Bezirk></wfs:member></wfs:FeatureCollection>"""

GML31 = """<wfs:FeatureCollection><gml:featureMember><qgs:e><qgs:geometry><MultiSurface xmlns="http://www.opengis.net/gml">
<surfaceMember><Polygon><exterior><LinearRing><posList srsDimension="2">0 0 5 0 5 5 0 5 0 0</posList></LinearRing>
</exterior></Polygon></surfaceMember></MultiSurface></qgs:geometry><qgs:titel>Westliches   Ostend</qgs:titel>
<qgs:paragraf_172_1_2>1</qgs:paragraf_172_1_2></qgs:e></gml:featureMember></wfs:FeatureCollection>"""


def test_gml32_with_hole_and_entity():
    (f,) = parse_features(GML32)
    assert f.props["STBZ_ID"] == "10" and f.props["STBZ_NAME"] == "Alt&stadt"
    assert f.geom.area == pytest.approx(96)


def test_gml31_without_prefix():
    (f,) = parse_features(GML31)
    assert f.props["titel"] == "Westliches Ostend" and f.props["paragraf_172_1_2"] == "1"
    assert f.geom.area == pytest.approx(25)


def test_count_with_area_counts_only_features_with_geometry(tmp_path):
    empty = tmp_path / "pending_plans.gml"
    empty.write_text('<ows:ExceptionReport><ows:Exception exceptionCode="x"/></ows:ExceptionReport>', encoding="utf-8")
    assert count_with_area(read_features(empty)) == 0
    gml = tmp_path / "social_preservation.gml"
    gml.write_text('<wfs:FeatureCollection><gml:featureMember><x:e><x:titel>A</x:titel><gml:Polygon><gml:exterior>'
                   '<gml:LinearRing><gml:posList>0 0 0 10 10 10 10 0 0 0</gml:posList></gml:LinearRing></gml:exterior>'
                   '</gml:Polygon></x:e></gml:featureMember><gml:featureMember><x:e><x:titel>B</x:titel></x:e>'
                   '</gml:featureMember></wfs:FeatureCollection>', encoding="utf-8")
    features = read_features(gml)
    assert len(features) == 2 and count_with_area(features) == 1
