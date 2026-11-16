from pipeline.shared.readers.gml import read_features
from pipeline.use_cases.protection.sources import (DECIDED, IN_FORCE, is_social_preservation, is_townscape,
                                                   read_social_preservation, read_townscape)


def test_is_social_preservation():
    assert is_social_preservation({"paragraf_172_1_2": "1"})
    assert is_social_preservation({"zusatz": "zur Erhaltung der Zusammensetzung der Wohnbevölkerung (gemäß §172 (1) Nr. 2 BauGB)"})
    assert not is_social_preservation({"paragraf_172_1_1": "1", "zusatz": "(gemäß §172 (1) Nr. 1 BauGB)"})


def test_is_townscape_only_no_1_without_social_preservation():
    assert is_townscape({"paragraf_172_1_1": "1", "paragraf_172_1_2": "0", "zusatz": "(gemäß §172 (1) Nr. 1 BauGB)"})
    assert not is_townscape({"paragraf_172_1_1": "1", "paragraf_172_1_2": "1"})
    assert not is_townscape({"paragraf_172_1_1": "0", "paragraf_172_1_2": "1"})
    assert not is_townscape({"paragraf_172_1_1": "1", "zusatz": "Nr. 2 BauGB"})


def test_read_townscape_keeps_the_given_date(tmp_path):
    gml = tmp_path / "e.gml"
    gml.write_text('<wfs:FeatureCollection><gml:featureMember><x:e><x:titel>Höchst</x:titel><x:projekt_nr>E1</x:projekt_nr>'
                   '<x:paragraf_172_1_1>1</x:paragraf_172_1_1><x:inkrafttreten>1993-02-25</x:inkrafttreten>'
                   '<gml:Polygon><gml:exterior><gml:LinearRing><gml:posList>0 0 0 10 10 10 10 0 0 0</gml:posList>'
                   '</gml:LinearRing></gml:exterior></gml:Polygon></x:e></gml:featureMember></wfs:FeatureCollection>',
                   encoding="utf-8")
    features = read_features(gml)
    (site,) = read_townscape(features, IN_FORCE)
    assert (site.title, site.project_no, site.date) == ("Höchst", "E1", "1993-02-25")
    assert read_townscape(features, DECIDED)[0].date == "" and read_social_preservation(features) == []
