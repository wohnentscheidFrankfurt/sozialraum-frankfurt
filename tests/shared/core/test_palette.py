from pipeline.shared.core import colours, palette


def test_trend_colours_stay_as_decided():
    # docs/design.md, Owner groups: the colours of the view Trend in bar order
    assert (palette.HOUSING_COMPANY, palette.OTHER_COMPANY, palette.CONDO, palette.PERSON) == (
        "#262626", "#575757", "#8c8c8c", "#bfbfbf")
    assert (palette.PUBLIC, palette.COOP, palette.NONPROFIT) == ("#d40000", "#8c0000", "#f07067")


def test_map_colours_reuse_the_trend_colours():
    # docs/design.md, Owner groups: the map has its own groups, two need their own colour
    assert palette.COMPANIES == palette.HOUSING_COMPANY
    assert palette.PERSONS_AND_CONDOS == "#a6a6a6" and palette.STATE == "#ffc9c2"
    colours = [palette.PUBLIC, palette.STATE, palette.COOP, palette.COMPANIES, palette.PERSONS_AND_CONDOS,
               palette.NONPROFIT]
    assert len(set(colours)) == 6


def test_candidate_hit_border_is_orange_and_unlike_every_other_colour():
    # docs/design.md, Candidates: a black border would look like Milieuschutz
    assert palette.HIT_BORDER == "#e8590c"
    others = [palette.PUBLIC, palette.STATE, palette.COOP, palette.COMPANIES, palette.PERSONS_AND_CONDOS,
              palette.NONPROFIT, "#000000", "#6a3d9a"]
    assert palette.HIT_BORDER not in others


def test_rents_take_the_reds_and_the_references_grey():
    # docs/design.md, View Neubau: the rents take the red family of the dwellings, prices and wages are a grey band
    # with thin edges
    assert (palette.RENT_NEW, palette.RENT_OLD) == (palette.COOP, palette.NONPROFIT) == ("#8c0000", "#f07067")
    assert (palette.REFERENCE_PRICES, palette.REFERENCE_WAGES, palette.REFERENCE_BAND) == (
        "#8c8c8c", "#6b6b6b", "#e6e6e6")
    assert not hasattr(palette, "REFERENCE_PRICES_INK") and not hasattr(palette, "REFERENCE_WAGES_INK")
    assert [c for c in (palette.RENT_NEW, palette.REFERENCE_PRICES, palette.REFERENCE_WAGES)
            if colours.contrast(c, "#ffffff") < 3] == []
    # intended: the light red is named by its end label or the key
    assert colours.contrast(palette.RENT_OLD, "#ffffff") < 3
