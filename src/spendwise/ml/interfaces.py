from typing import Any, Protocol

from spendwise.models import ForecastResult


class CategoryPredictor(Protocol):
    def suggest(self, text: str) -> tuple[str, float] | None: ...

    def learn(self, text: str, category: str) -> None: ...


class SpendingForecaster(Protocol):
    def forecast(self, history: Any) -> ForecastResult: ...
