"""Smoke tests for the services layer skeleton."""

from spendwise.services.alert_service import AlertService
from spendwise.services.budget_service import BudgetService
from spendwise.services.category_service import DEFAULT_CATEGORIES, CategoryService
from spendwise.services.export_service import ExportService
from spendwise.services.forecast_service import ForecastService
from spendwise.services.profile_service import ProfileService
from spendwise.services.report_service import ReportService
from spendwise.services.transaction_service import TransactionService


def test_service_classes_instantiate() -> None:
    """Verify service skeleton classes can be instantiated."""
    assert ProfileService() is not None
    assert CategoryService() is not None
    assert TransactionService() is not None
    assert BudgetService() is not None
    assert AlertService() is not None
    assert ForecastService() is not None
    assert ExportService() is not None
    assert ReportService() is not None
    assert "Groceries" in DEFAULT_CATEGORIES
