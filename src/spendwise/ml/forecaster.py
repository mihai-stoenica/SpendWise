from typing import Any

from spendwise.models import ForecastResult


class BaselineSpendingForecaster:
    def forecast(self, history: Any) -> ForecastResult:
        return ForecastResult(total_forecast=0, per_category={}, low_confidence=True)
