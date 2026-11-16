from pipeline.build import STEPS


def test_assembly_needs_every_area_table_and_city_file():
    made = {d.name for s in STEPS for d in s.makes}
    area = {n for n in made if n.endswith(("_by_district", "_by_quarter", "_city"))}
    step = next(s for s in STEPS if s.name == "assembly")
    assert area <= {d.name for d in step.needs}, sorted(area - {d.name for d in step.needs})


def test_assembly_writes_the_map_catalog_and_the_map_reads_it():
    from pipeline.engine.datasets import MAP_CATALOG
    steps = {s.name: s for s in STEPS}
    assert MAP_CATALOG in steps["assembly"].makes and MAP_CATALOG in steps["map"].needs
    assert "catalog_numbers" not in {d.name for s in STEPS for d in (*s.needs, *s.makes)}


def test_area_tables_and_city_files_keep_the_order_of_the_joins():
    """The order is the column order of the joined tables and the row order of city_values.csv."""
    from pipeline.map.assembly.step import AREA_TABLES, CITY_FILES
    assert [d.name for d in AREA_TABLES["district"]] == [
        "ownership_shares_by_district", "monitoring_by_district", "survey_by_district", "housing_by_district",
        "construction_year_by_district", "land_by_district", "protection_by_district", "flat_roofs_by_district",
        "building_gaps_by_district"]
    assert [d.name for d in AREA_TABLES["quarter"]] == [
        "ownership_shares_by_quarter", "monitoring_by_quarter",
        "social_housing_by_quarter", "housing_by_quarter", "construction_year_by_quarter", "land_by_quarter",
        "protection_by_quarter", "election_by_quarter", "flat_roofs_by_quarter", "building_gaps_by_quarter"]
    assert [d.name for d in CITY_FILES] == [
        "ownership_shares_city", "monitoring_city", "survey_city", "social_housing_city", "housing_city",
        "construction_year_city", "land_city", "protection_city", "election_city", "flat_roofs_city",
        "building_gaps_city"]


def test_assembly_reads_the_half_widths_and_the_worked_example_of_the_survey():
    from pipeline.engine.datasets import OWNERSHIP_RANGES, SURVEY_CALC_EXAMPLES, SURVEY_HALF_WIDTHS
    from pipeline.map.assembly.step import EXAMPLE_FILES
    step = next(s for s in STEPS if s.name == "assembly")
    assert SURVEY_CALC_EXAMPLES in EXAMPLE_FILES
    assert {OWNERSHIP_RANGES, SURVEY_HALF_WIDTHS, *EXAMPLE_FILES} <= set(step.needs)
