from pathlib import Path

import pytest

from spendwise.repositories.category_repo import CategoryRepository
from spendwise.repositories.transaction_repo import TransactionRepository
from spendwise.services.category_service import CategoryService
from spendwise.services.report_service import ReportService
from spendwise.services.transaction_service import TransactionService


def test_build_monthly_summary_and_comparison(temp_db_path: Path) -> None:
    cat_repo = CategoryRepository(temp_db_path)
    cat_service = CategoryService(cat_repo)
    cats = {c.name: c.id for c in cat_service.list_categories()}

    tx_service = TransactionService(TransactionRepository(temp_db_path), category_repo=cat_repo)
    report_service = ReportService(tx_service)

    tx_service.add_transaction("2026-10-01", "5000.00", "income", cats["Salary"])
    tx_service.add_transaction("2026-10-10", "1000.00", "expense", cats["Rent"])

    tx_service.add_transaction("2026-11-01", "5200.00", "income", cats["Salary"])
    tx_service.add_transaction("2026-11-05", "1000.00", "expense", cats["Rent"])
    tx_service.add_transaction("2026-11-12", "300.00", "expense", cats["Groceries"])
    tx_service.add_transaction("2026-11-18", "200.00", "expense", cats["Utilities"])
    tx_service.add_transaction("2026-11-20", "50.00", "expense", cats["Dining"])

    summary = report_service.build_monthly_summary("2026-11", top_n=3)

    assert summary.month == "2026-11"
    assert summary.previous_month == "2026-10"
    assert summary.total_income == 520000
    assert summary.total_expenses == 155000
    assert summary.balance == 365000
    assert summary.prev_income == 500000
    assert summary.prev_expenses == 100000
    assert summary.expense_diff == 55000
    assert summary.expense_change_pct == 55.0
    assert summary.top_categories == [
        ("Rent", 100000),
        ("Groceries", 30000),
        ("Utilities", 20000),
    ]


def test_january_previous_month_and_empty_data(temp_db_path: Path) -> None:
    tx_service = TransactionService(TransactionRepository(temp_db_path))
    report_service = ReportService(tx_service)

    summary = report_service.build_monthly_summary("2026-01")
    assert summary.previous_month == "2025-12"
    assert summary.total_income == 0
    assert summary.total_expenses == 0
    assert summary.balance == 0
    assert summary.expense_change_pct is None
    assert summary.top_categories == []


def test_invalid_month_raises_value_error(temp_db_path: Path) -> None:
    tx_service = TransactionService(TransactionRepository(temp_db_path))
    report_service = ReportService(tx_service)

    with pytest.raises(ValueError, match="YYYY-MM"):
        report_service.build_monthly_summary("2026-13")

    with pytest.raises(ValueError, match="YYYY-MM"):
        report_service.build_monthly_summary("invalid")


def test_generate_monthly_pdf_creates_valid_pdf_file(
    temp_db_path: Path,
    tmp_path: Path,
) -> None:
    cat_repo = CategoryRepository(temp_db_path)
    cat_service = CategoryService(cat_repo)
    cats = {c.name: c.id for c in cat_service.list_categories()}
    tx_service = TransactionService(TransactionRepository(temp_db_path), category_repo=cat_repo)
    report_service = ReportService(tx_service)

    pdf_empty = tmp_path / "reports" / "empty_2026-01.pdf"
    result_empty = report_service.generate_monthly_pdf("2026-01", pdf_empty, profile_name="Demo")
    assert result_empty == pdf_empty
    assert pdf_empty.is_file()
    assert pdf_empty.read_bytes().startswith(b"%PDF")

    tx_service.add_transaction("2026-10-05", "100.00", "expense", cats["Groceries"])
    tx_service.add_transaction("2026-11-01", "3000.00", "income", cats["Salary"])
    tx_service.add_transaction("2026-11-05", "150.00", "expense", cats["Groceries"])

    pdf_populated = tmp_path / "reports" / "nov_2026-11.pdf"
    report_service.generate_monthly_pdf("2026-11", pdf_populated, profile_name="Personal")
    assert pdf_populated.is_file()
    assert pdf_populated.read_bytes().startswith(b"%PDF")
