"""The real inputs of the use case, read once for the tests of model and checks."""
import math

import pandas as pd
import pytest

from pipeline import config
from pipeline.shared.readers.pdf import page_texts
from pipeline.use_cases.new_construction.catalog import RENT_TO, SURVEY_DATES
from pipeline.use_cases.rent_burden.catalog import FLAT_M2
from pipeline.use_cases.rent_burden.model import low_income_facts, wage_facts, wage_table
from pipeline.use_cases.rent_burden.sources import (MIETSPIEGEL_COSTS, MINDESTLOHN, WAGE_RULES, read_median_wage,
                                                    read_mietspiegel_costs, read_nebenkosten)
from pipeline.use_cases.survey.sources import read_microdata

YEARS = tuple(SURVEY_DATES)
# interim/new_construction_rents.csv of the build (the survey years and one year between): net cold rent per m² of new
# and older contracts, price index with 2017 = 100
RENTS = pd.DataFrame({"year": [2017, 2018, 2021, 2023, 2025],
                      "new": [10.21, math.nan, 11.56, 13.05, 13.95], "old": [8.69, math.nan, 9.14, 9.43, 10.11],
                      "prices_index": [100.0, 102.05761316872427, 106.06995884773663, 119.95884773662551, 125.0]})


@pytest.fixture(name="inputs", scope="session")
def inputs_fixture():
    """The inputs of the step: the rents, the Nebenkosten of the BA and of the Mietspiegel, the median wage."""
    cache = {}

    def pages_of(name):
        if name not in cache:
            cache[name] = page_texts(getattr(config, name))
        return cache[name]
    ba = {y: sum(read_nebenkosten(config.BA_KDU_XLSX[y], y).values()) for y in YEARS}
    wages = {y: read_median_wage(y, {2017: config.BA_WAGES_2017_XLSM}, config.BA_WAGES_SERIES_XLSX) for y in YEARS}
    return {"rents": RENTS, "ba": ba, "mietspiegel": read_mietspiegel_costs(pages_of, MIETSPIEGEL_COSTS),
            "wages": wages}


def _table(inputs, nebenkosten):
    return wage_table(inputs["rents"], nebenkosten, inputs["wages"], WAGE_RULES, MINDESTLOHN, YEARS, FLAT_M2)


@pytest.fixture(name="table", scope="session")
def table_fixture(inputs):
    return _table(inputs, inputs["ba"])


@pytest.fixture(name="mietspiegel_table", scope="session")
def mietspiegel_table_fixture(inputs):
    """The same table with the Nebenkosten of the Mietspiegel (the sensitivity)."""
    return _table(inputs, inputs["mietspiegel"])


@pytest.fixture(name="facts", scope="session")
def facts_fixture(table, mietspiegel_table):
    return wage_facts(table, mietspiegel_table, RENT_TO)


@pytest.fixture(name="respondents", scope="session")
def respondents_fixture():
    """The dataset SURVEY_RESPONDENTS: the respondents of both surveys."""
    return pd.concat([read_microdata(path, year) for year, path in config.SURVEY_MICRODATA.items()], ignore_index=True)


@pytest.fixture(name="low_facts", scope="session")
def low_facts_fixture(respondents):
    return low_income_facts(respondents)
