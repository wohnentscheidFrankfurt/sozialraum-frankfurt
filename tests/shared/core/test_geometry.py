from shapely.geometry import box

from pipeline.shared.core.geometry import (Site, german_date, site_properties, site_properties_with_date, to_25832,
                                           to_wgs84)


def test_to_wgs84_rounds_to_5_digits():
    g = to_wgs84(box(477200, 5550900, 477300, 5551000), 0)
    lon, lat = g["coordinates"][0][0]
    assert 8.67 < lon < 8.69 and 50.10 < lat < 50.12 and round(lon, 5) == lon


def test_to_25832_hits_the_roemer():
    x, y = to_25832([4226750], [3000650])
    assert abs(x[0] - 477262) < 150 and abs(y[0] - 5550954) < 150


def test_german_date_drops_leading_zeros_and_keeps_unreadable_dates_empty():
    assert german_date("1993-02-25") == "25.2.1993" and german_date("2020-11-03T10:00:00") == "3.11.2020"
    assert german_date("") == "" and german_date("kein Datum") == ""


def test_site_properties_name_title_and_project_no_and_optionally_the_date():
    site = Site("Am Bügel", "B 123", None, "1993-02-25")
    assert site_properties(site) == {"title": "Am Bügel", "project_no": "B 123"}
    assert site_properties_with_date(site) == {"title": "Am Bügel", "project_no": "B 123", "date": "25.2.1993"}
