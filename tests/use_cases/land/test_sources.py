from pipeline.use_cases.land.sources import is_residential_zone


def test_is_residential_zone():
    assert is_residential_zone("Frankfurt am Main", "B", "WA") and is_residential_zone("Frankfurt am Main", "B", "M")
    assert not is_residential_zone("Frankfurt am Main", "B", "G")
    assert not is_residential_zone("Kriftel", "B", "W")
    assert not is_residential_zone("Frankfurt am Main", "E", "W")


def test_read_values_keeps_only_numbers_with_a_value(tmp_path):
    from pipeline.use_cases.land.sources import read_values
    path = tmp_path / "v.csv"
    path.write_text("number,value,as_of\n43391012,3300,01.01.2026\n49999999,,\n00000001,0.01,01.01.2026\n")
    assert read_values(path) == {"43391012": (3300.0, "01.01.2026"), "00000001": (0.01, "01.01.2026")}
