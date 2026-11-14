"""Smoke tests for the ML layer skeleton."""

from spendwise.ml.categorizer import BaselineCategoryPredictor
from spendwise.ml.forecaster import BaselineSpendingForecaster


def test_baseline_predictors() -> None:
    """Verify baseline predictors conform to expected behavior."""
    categorizer = BaselineCategoryPredictor()
    assert categorizer.suggest("Kaufland") is None

    forecaster = BaselineSpendingForecaster()
    result = forecaster.forecast(None)
    assert result.low_confidence is True
    assert result.total_forecast == 0
