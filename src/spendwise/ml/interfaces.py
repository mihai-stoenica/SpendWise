"""Predictor protocols for category suggestion and spending forecast."""

from typing import Any, Protocol

from spendwise.models import ForecastResult


class CategoryPredictor(Protocol):
    """Interface for transaction category suggestion models."""

    def suggest(self, text: str) -> tuple[str, float] | None:
        """Suggest a (category_name, confidence) tuple for a description."""
        ...

    def learn(self, text: str, category: str) -> None:
        """Record a user-confirmed description -> category mapping."""
        ...


class SpendingForecaster(Protocol):
    """Interface for next-month spending forecast models."""

    def forecast(self, history: Any) -> ForecastResult:
        """Forecast next month's spending from historical transaction data."""
        ...
