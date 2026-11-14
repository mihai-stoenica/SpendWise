"""Spending forecaster baseline and scikit-learn implementations skeleton."""

from typing import Any

from spendwise.models import ForecastResult


class BaselineSpendingForecaster:
    """Baseline average-based spending forecaster."""

    def forecast(self, history: Any) -> ForecastResult:
        """Return a placeholder low-confidence empty forecast."""
        return ForecastResult(total_forecast=0, per_category={}, low_confidence=True)
