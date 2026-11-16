import json

import pandas as pd

from pipeline.use_cases.public_housing.sources import read_research_sites


def test_read_research_sites_keeps_frankfurt_estates_and_new_buildings_with_a_number():
    def feature(i, gebiet="Frankfurt am Main", ebene="neubau", wohnungen=10, stand="fertig 2019"):
        return {"type": "Feature", "id": i, "geometry": {"type": "Point", "coordinates": [8.6, 50.1]},
                "properties": {"id": i, "gebiet": gebiet, "ebene": ebene, "wohnungen": wohnungen,
                               "lage_genauigkeit": "Q", "stand": stand}}
    text = json.dumps({"type": "FeatureCollection", "features": [
        feature("a", stand="Bau 2017–2019"), feature("b", gebiet="Offenbach"), feature("c", ebene="parken"),
        feature("d", wohnungen=None), feature("e", ebene="bestand", stand="1920er"),
        feature("f", stand="unbekannt")]})
    df = read_research_sites(text)
    assert df["id"].tolist() == ["a", "e", "f"]
    assert df.loc[0].to_dict() == {"id": "a", "level": "neubau", "dwellings": 10, "precision": "Q", "year": 2019,
                                   "lon": 8.6, "lat": 50.1}
    assert df["year"].tolist()[1] == 1920 and pd.isna(df["year"].tolist()[2])
