"""Every interim dataset. This is the published language between the steps."""
from __future__ import annotations

from dataclasses import dataclass, replace

from pipeline.shared.core.texts import LANGUAGES, SOURCE_LANGUAGE


@dataclass(frozen=True)
class Dataset:
    name: str  # file name without suffix
    kind: str = "csv"  # csv, json or md
    keys: tuple[str, ...] = ()  # columns read as text

    @property
    def file(self) -> str:
        return f"{self.name}.{self.kind}"


def in_language(dataset: Dataset, lang: str) -> Dataset:
    """The dataset of a language: the source language (German) is the dataset itself, another language adds `.<lang>`
    to the name."""
    return dataset if lang == SOURCE_LANGUAGE else replace(dataset, name=f"{dataset.name}.{lang}")


def languages(dataset: Dataset) -> tuple[Dataset, ...]:
    """One dataset per language of the map."""
    return tuple(in_language(dataset, lang) for lang in LANGUAGES)


def ending(suffix: str) -> tuple[Dataset, ...]:
    """The datasets declared so far in this module whose name ends with the suffix, in the order of declaration."""
    return tuple(v for v in globals().values() if isinstance(v, Dataset) and v.name.endswith(suffix))


CELLS_2022 = Dataset("cells_2022", keys=("cell_id", "district", "quarter"))
CELLS_2011_DWELLINGS = Dataset("cells_2011_dwellings", keys=("cell_id",))
CELLS_2011_BUILDINGS = Dataset("cells_2011_buildings", keys=("cell_id",))
ZENSUS_CHECKS = Dataset("zensus_checks", kind="json")
OWNERSHIP_CELLS = Dataset("ownership_cells", keys=("cell_id",))
OWNERSHIP_GRID_CELLS = Dataset("ownership_grid_cells", kind="json")
OWNERSHIP_CELLS_CHECKS = Dataset("ownership_cells_checks", kind="json")
OWNERSHIP_SHARES_BY_DISTRICT = Dataset("ownership_shares_by_district", keys=("id",))
OWNERSHIP_SHARES_BY_QUARTER = Dataset("ownership_shares_by_quarter", keys=("id",))
OWNERSHIP_SHARES_CITY = Dataset("ownership_shares_city", kind="json")
OWNERSHIP_RANGES = Dataset("ownership_ranges", kind="json")  # smallest and largest half range per group, points
OWNERSHIP_CALC_EXAMPLES = Dataset("ownership_calc_examples", kind="json")  # worked examples, one file per language
OWNERSHIP_SHARES_CHECKS = Dataset("ownership_shares_checks", kind="json")
OWNERSHIP_HISTORY = Dataset("ownership_history", keys=("group",))
OWNERSHIP_BY_SIZE = Dataset("ownership_by_size", keys=("group", "size"))
COMPANY_BUILDINGS_BY_DECADE = Dataset("company_buildings_by_decade", keys=("decade", "key"))
OWNERSHIP_HISTORY_VIEW = Dataset("ownership_history_view", kind="json")  # the view Trend, one file per language
OWNERSHIP_HISTORY_CHECKS = Dataset("ownership_history_checks", kind="json")
NEW_CONSTRUCTION = Dataset("new_construction", keys=("year",))
NEW_CONSTRUCTION_STOCK = Dataset("new_construction_stock", keys=("year",))
NEW_CONSTRUCTION_RENTS = Dataset("new_construction_rents", keys=("year",))
NEW_CONSTRUCTION_VIEW = Dataset("new_construction_view", kind="json")
NEW_CONSTRUCTION_CHECKS = Dataset("new_construction_checks", kind="json")
PUBLIC_HOUSING_QUARTERS = Dataset("public_housing_quarters", keys=("quarter",))
PUBLIC_HOUSING_CHECKS = Dataset("public_housing_checks", kind="json")
COOPS_QUARTERS = Dataset("coops_quarters", keys=("quarter",))
COOPS_CHECKS = Dataset("coops_checks", kind="json")
MONITORING_BY_DISTRICT = Dataset("monitoring_by_district", keys=("id",))  # one file per language (column _SHARED is a text)
MONITORING_BY_QUARTER = Dataset("monitoring_by_quarter", keys=("id",))
MONITORING_CITY = Dataset("monitoring_city", kind="json")
MONITORING_CHECKS = Dataset("monitoring_checks", kind="json")
SURVEY_BY_DISTRICT = Dataset("survey_by_district", keys=("id",))
SURVEY_CITY = Dataset("survey_city", kind="json")
SURVEY_HALF_WIDTHS = Dataset("survey_half_widths", kind="json")  # typical and largest half width of the income groups, points
SURVEY_CALC_EXAMPLES = Dataset("survey_calc_examples", kind="json")  # worked example of the rent burden, one file per language
SURVEY_RESPONDENTS = Dataset("survey_respondents", keys=("survey_area",))  # working data: respondents of both years
SURVEY_CHECKS = Dataset("survey_checks", kind="json")
RENT_BURDEN_WAGE = Dataset("rent_burden_wage", keys=("person", "contract"))  # S1: year × person × contract
RENT_BURDEN_GROUPS = Dataset("rent_burden_groups", keys=("group",))  # S2: income group × burden class
RENT_BURDEN_VIEW = Dataset("rent_burden_view", kind="json")
RENT_BURDEN_CHECKS = Dataset("rent_burden_checks", kind="json")
SOCIAL_HOUSING_BY_QUARTER = Dataset("social_housing_by_quarter", keys=("id",))
SOCIAL_HOUSING_CITY = Dataset("social_housing_city", kind="json")
SOCIAL_HOUSING_CALC_EXAMPLES = Dataset("social_housing_calc_examples", kind="json")  # worked example of the share, one file per language
SOCIAL_HOUSING_CHECKS = Dataset("social_housing_checks", kind="json")
HOUSING_BY_DISTRICT = Dataset("housing_by_district", keys=("id",))
HOUSING_BY_QUARTER = Dataset("housing_by_quarter", keys=("id",))
HOUSING_CITY = Dataset("housing_city", kind="json")
HOUSING_CHECKS = Dataset("housing_checks", kind="json")
HOUSING_CALC_EXAMPLES = Dataset("housing_calc_examples", kind="json")  # worked example per indicator, one file per language
CONSTRUCTION_YEAR_BY_DISTRICT = Dataset("construction_year_by_district", keys=("id",))
CONSTRUCTION_YEAR_BY_QUARTER = Dataset("construction_year_by_quarter", keys=("id",))
CONSTRUCTION_YEAR_CITY = Dataset("construction_year_city", kind="json")
CONSTRUCTION_YEAR_CALC_EXAMPLES = Dataset("construction_year_calc_examples", kind="json")  # worked example per class, one file per language
CONSTRUCTION_YEAR_CHECKS = Dataset("construction_year_checks", kind="json")
LAND_VALUE_CELLS = Dataset("land_value_cells", keys=("cell_id",))
LAND_BY_DISTRICT = Dataset("land_by_district", keys=("id",))
LAND_BY_QUARTER = Dataset("land_by_quarter", keys=("id",))
LAND_CITY = Dataset("land_city", kind="json")
LAND_OVERLAYS = Dataset("land_overlays", kind="json")
LAND_CHECKS = Dataset("land_checks", kind="json")
PROTECTION_CELLS = Dataset("protection_cells", keys=("cell_id",))
PROTECTION_BY_DISTRICT = Dataset("protection_by_district", keys=("id",))
PROTECTION_BY_QUARTER = Dataset("protection_by_quarter", keys=("id",))
PROTECTION_CITY = Dataset("protection_city", kind="json")
PROTECTION_OVERLAYS = Dataset("protection_overlays", kind="json")
PROTECTION_CHECKS = Dataset("protection_checks", kind="json")
ELECTION_BY_QUARTER = Dataset("election_by_quarter", keys=("id",))
ELECTION_LISTS = Dataset("election_lists", kind="json")
ELECTION_CITY = Dataset("election_city", kind="json")
ELECTION_CHECKS = Dataset("election_checks", kind="json")
INDICATORS_DISTRICTS = Dataset("indicators_districts", keys=("id", "quarter", "survey_area"))
INDICATORS_QUARTERS = Dataset("indicators_quarters", keys=("id",))
CITY_VALUES = Dataset("city_values")
MAP_CATALOG = Dataset("map_catalog", kind="json")  # indicators, overlays and sources with finished texts
ASSEMBLY_CHECKS = Dataset("assembly_checks", kind="json")
FLAT_ROOFS_BY_DISTRICT = Dataset("flat_roofs_by_district", keys=("id",))
FLAT_ROOFS_BY_QUARTER = Dataset("flat_roofs_by_quarter", keys=("id",))
FLAT_ROOFS_CITY = Dataset("flat_roofs_city", kind="json")
FLAT_ROOFS_OVERLAYS = Dataset("flat_roofs_overlays", kind="json")
FLAT_ROOFS_CALC_EXAMPLES = Dataset("flat_roofs_calc_examples", kind="json")  # the funnel as a written sum
FLAT_ROOFS_CHECKS = Dataset("flat_roofs_checks", kind="json")
BUILDING_GAPS_BY_DISTRICT = Dataset("building_gaps_by_district", keys=("id",))
BUILDING_GAPS_BY_QUARTER = Dataset("building_gaps_by_quarter", keys=("id",))
BUILDING_GAPS_CITY = Dataset("building_gaps_city", kind="json")
BUILDING_GAPS_OVERLAYS = Dataset("building_gaps_overlays", kind="json")
BUILDING_GAPS_CALC_EXAMPLES = Dataset("building_gaps_calc_examples", kind="json")  # the funnel as a written sum
BUILDING_GAPS_CHECKS = Dataset("building_gaps_checks", kind="json")
# every check result of the steps (`_checks`); the step `checks` reads them in this order
CHECK_RESULTS = ending("_checks")
CANDIDATES_REFERENCE = Dataset("candidates_reference", keys=("area",))
CHECK_REPORT = Dataset("check_report", kind="md")
