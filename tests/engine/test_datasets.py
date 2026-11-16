from pipeline.engine import datasets
from pipeline.engine.datasets import CHECK_RESULTS, ending


def names(found):
    return [d.name for d in found]


def test_ending_selects_by_name_in_declaration_order():
    assert names(ending("_by_district")) == [
        "ownership_shares_by_district", "monitoring_by_district", "survey_by_district", "housing_by_district",
        "construction_year_by_district", "land_by_district", "protection_by_district", "flat_roofs_by_district",
        "building_gaps_by_district"]
    assert names(ending("_by_quarter")) == [
        "ownership_shares_by_quarter", "monitoring_by_quarter",
        "social_housing_by_quarter", "housing_by_quarter", "construction_year_by_quarter", "land_by_quarter",
        "protection_by_quarter", "election_by_quarter", "flat_roofs_by_quarter", "building_gaps_by_quarter"]
    assert names(ending("_city")) == [
        "ownership_shares_city", "monitoring_city", "survey_city", "social_housing_city", "housing_city",
        "construction_year_city", "land_city", "protection_city", "election_city", "flat_roofs_city",
        "building_gaps_city"]
    assert ending("_no_such_ending") == ()


def test_check_results_are_all_datasets_named_checks():
    assert set(names(CHECK_RESULTS)) == {
        "zensus_checks", "ownership_cells_checks", "public_housing_checks", "coops_checks",
        "ownership_shares_checks", "ownership_history_checks", "new_construction_checks", "monitoring_checks",
        "survey_checks", "rent_burden_checks", "land_checks", "flat_roofs_checks", "building_gaps_checks",
        "protection_checks", "election_checks",
        "social_housing_checks", "housing_checks", "construction_year_checks", "assembly_checks"}
    assert all(d.kind == "json" for d in CHECK_RESULTS)
    assert CHECK_RESULTS == ending("_checks") and datasets.CHECK_RESULTS is CHECK_RESULTS
