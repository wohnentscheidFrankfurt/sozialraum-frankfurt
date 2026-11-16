import pytest

from pipeline.use_cases.construction_year.catalog import CALC_EXAMPLE_QUARTERS as CONSTRUCTION_EXAMPLES
from pipeline.use_cases.housing.catalog import CALC_EXAMPLE_QUARTERS as HOUSING_EXAMPLES
from pipeline.use_cases.ownership_shares.catalog import CALC_EXAMPLE_QUARTERS as OWNERSHIP_EXAMPLES
from pipeline.use_cases.social_housing.catalog import CALC_EXAMPLE_QUARTERS as SOCIAL_HOUSING_EXAMPLES


@pytest.fixture(scope="session")
def example_ids():
    """The indicators whose Rechnung is a worked example."""
    return {**OWNERSHIP_EXAMPLES, **HOUSING_EXAMPLES, **CONSTRUCTION_EXAMPLES, **SOCIAL_HOUSING_EXAMPLES}
