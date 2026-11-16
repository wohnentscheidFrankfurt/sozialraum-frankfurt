"""The ramps computed in Python equal the ramps the browser computed before Task 16 (web/js/01_base.js, APP.rampFor).

The values were taken from the built map by running that function in Chrome on every ramp the catalog and the party
lists use, plus the light party yellow (FDP, #ffd600) and the light ownership colour of Bund oder Land (#ffc9c2).
"""
import pytest

from pipeline.shared.core import colours

EXPECTED = {
    "blue": ["#eff3ff", "#bdd7e7", "#6baed6", "#3182bd", "#08519c"],
    "color:#1d1d1b": ["#e4e4e4", "#b7b7b6", "#858584", "#4f4f4d", "#1d1d1b"],
    "color:#262626": ["#e5e5e5", "#bababa", "#8a8a8a", "#565656", "#262626"],
    "color:#3ea3dc": ["#e6f0f5", "#bdd6e4", "#8fbad2", "#5e9cbe", "#3080ac"],
    "color:#4f2779": ["#eae5ef", "#c7bad4", "#a08ab7", "#765796", "#4f2779"],
    "color:#52ae32": ["#e8f1e5", "#c2daba", "#99c18b", "#6ba557", "#428b28"],
    "color:#8c0000": ["#f1e0e0", "#daadad", "#c17575", "#a53838", "#8c0000"],
    "color:#9e9e9e": ["#efefef", "#d4d4d4", "#b6b6b6", "#959595", "#777777"],
    "color:#a6a6a6": ["#efefef", "#d4d4d4", "#b6b6b6", "#959595", "#777777"],
    "color:#b64661": ["#f6e9ec", "#e8c4cc", "#d89baa", "#c66f84", "#b64661"],
    "color:#d40000": ["#fae0e0", "#f1adad", "#e87575", "#dd3838", "#d40000"],
    "color:#e30613": ["#fce1e3", "#f6afb3", "#f07980", "#e93d47", "#e30613"],
    "color:#f07067": ["#f6ebea", "#e8c9c6", "#d8a3a0", "#c77b75", "#b7554e"],
    "color:#ffc9c2": ["#f1eeed", "#dad1d0", "#c1b1af", "#a68f8c", "#8d6f6b"],
    "color:#ffd600": ["#f1efe0", "#dad3ad", "#c1b575", "#a69438", "#8d7600"],
    "orange": ["#feedde", "#fdbe85", "#fd8d3c", "#e6550d", "#a63603"],
    "purple": ["#f2f0f7", "#cbc9e2", "#9e9ac8", "#756bb1", "#54278f"],
    "red": ["#fee5d9", "#fcae91", "#fb6a4a", "#de2d26", "#a50f15"],
    "teal": ["#e6fafa", "#b3eeee", "#66dddd", "#16cccc", "#0e8080"],
}
TEAL = ["#e6fafa", "#b3eeee", "#66dddd", "#16cccc", "#0e8080"]


@pytest.mark.parametrize("name", sorted(EXPECTED))
def test_ramp_equals_the_browser(name):
    assert colours.ramp(name) == EXPECTED[name]


def test_named_ramps_are_the_five_of_the_browser():
    assert sorted(colours.NAMED) == ["blue", "orange", "purple", "red", "teal"]
    assert all(colours.NAMED[name] == EXPECTED[name] for name in colours.NAMED)


@pytest.mark.parametrize("name", ["color:red;x", "gibtsnicht", "", "color:#12345", "color:#1234567", "teal\n"])
def test_an_unknown_or_invalid_ramp_falls_back_to_teal(name):
    assert colours.ramp(name) == TEAL


def test_a_light_colour_ends_darker_than_itself():
    assert colours.oklab_l((255, 214, 0)) > 0.59
    assert colours.ramp("color:#ffd600")[4] != "#ffd600"


def test_a_dark_colour_ends_in_itself():
    assert colours.ramp("color:#e30613")[4] == "#e30613"


def test_oklab_lightness_of_black_and_white():
    assert colours.oklab_l((0, 0, 0)) == 0
    assert colours.oklab_l((255, 255, 255)) == pytest.approx(1, abs=1e-6)


def test_the_ramp_is_case_insensitive_like_the_browser():
    assert colours.ramp("color:#D40000") == EXPECTED["color:#d40000"]


# Text colour, line colour and the contrasts of the view "Trend". The values were taken from the built map by running
# APP.textOn, APP.lineOn and APP.contrast of web/js/06_history.js (before Task 19) in Chrome: the group and sector
# colours of the view, the light party yellow and ownership colour, and the extremes white and black.
# Each value: (text_on, line_on, contrast of the colour and its text colour, contrast of the colour and white).
CONTRAST_EXPECTED = {
    "#bfbfbf": ("#1a1a1a", "#919191", 9.464565691232814, 1.8388934157712187),
    "#8c8c8c": ("#1a1a1a", "#8c8c8c", 5.175726396153281, 3.362683071052112),
    "#d40000": ("#ffffff", "#d40000", 5.527174358815752, 5.527174358815752),
    "#262626": ("#ffffff", "#262626", 15.133529408889883, 15.133529408889883),
    "#575757": ("#ffffff", "#575757", 7.226056749490168, 7.226056749490168),
    "#8c0000": ("#ffffff", "#8c0000", 9.928656476684269, 9.928656476684269),
    "#f07067": ("#1a1a1a", "#e46a61", 5.982593140089544, 2.9091611488862994),
    "#ffd600": ("#1a1a1a", "#af9200", 12.324441022991277, 1.4121798708983533),
    "#ffc9c2": ("#1a1a1a", "#af8985", 11.922516385125265, 1.459786421804052),
    "#ffffff": ("#1a1a1a", "#8d8d8d", 17.40432753274219, 1),
    "#000000": ("#ffffff", "#000000", 21, 21),
    "#808080": ("#1a1a1a", "#808080", 4.406784020953281, 3.9494396480491156),
    "#1a1a1a": ("#ffffff", "#1a1a1a", 17.40432753274219, 17.40432753274219),
    "#ffed00": ("#1a1a1a", "#9d9100", 14.392280493669793, 1.209282124566513),
    "#9a9a9a": ("#1a1a1a", "#929292", 6.18505393144791, 2.813933027204481),
}


@pytest.mark.parametrize("colour", sorted(CONTRAST_EXPECTED))
def test_text_and_line_colours_equal_the_browser(colour):
    text, line, with_text, with_white = CONTRAST_EXPECTED[colour]
    assert colours.text_on(colour) == text
    assert colours.line_on(colour) == line
    assert colours.contrast(colour, text) == pytest.approx(with_text, rel=1e-12)
    assert colours.contrast(colour, "#ffffff") == pytest.approx(with_white, rel=1e-12)


def test_a_line_colour_reaches_three_to_one_against_white():
    assert all(colours.contrast(colours.line_on(c), "#ffffff") >= 3 for c in CONTRAST_EXPECTED)


def test_contrast_is_symmetric_and_runs_from_one_to_twenty_one():
    assert colours.contrast("#000000", "#ffffff") == colours.contrast("#ffffff", "#000000") == pytest.approx(21)
    assert colours.contrast("#123456", "#123456") == 1
