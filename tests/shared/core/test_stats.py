import pytest

from pipeline.shared.core.stats import weighted_mean, weighted_median


def test_weighted_mean_ignores_missing_values():
    assert weighted_mean([10, None, 20], [1, 5, 3]) == pytest.approx(17.5)


def test_weighted_mean_without_weight_is_none():
    assert weighted_mean([1, 2], [0, 0]) is None


def test_weighted_median_takes_the_lower_median():
    assert weighted_median([1, 2, 3, 10], [1, 1, 1, 1]) == 2.0
    assert weighted_median([1, 2, 3, 10], [1, 1, 1, 5]) == 10.0
