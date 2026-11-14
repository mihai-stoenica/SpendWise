from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

import pytest

from spendwise.repositories.category_repo import CategoryRepository
from spendwise.repositories.transaction_repo import TransactionRepository
from spendwise.services.category_service import CategoryService
from spendwise.services.transaction_service import (
    TransactionService,
    format_minor_amount,
    parse_amount_to_minor,
)


def test_parse_and_format_minor_amounts() -> None:
    assert parse_amount_to_minor("12.34") == 1234
    assert parse_amount_to_minor("12,50") == 1250
    assert parse_amount_to_minor(10) == 1000
    assert parse_amount_to_minor(Decimal("99.99")) == 9999
    assert format_minor_amount(1234) == "12.34"
    assert format_minor_amount(0) == "0.00"
    assert format_minor_amount(-505) == "-5.05"


def test_parse_invalid_amounts_raise() -> None:
    with pytest.raises(ValueError, match="positive number"):
        parse_amount_to_minor(True)

    with pytest.raises(ValueError, match="cannot be empty"):
        parse_amount_to_minor("   ")

    with pytest.raises(ValueError, match="Invalid amount"):
        parse_amount_to_minor("abc")

    with pytest.raises(ValueError, match="Invalid amount"):
        parse_amount_to_minor("NaN")

    with pytest.raises(ValueError, match="greater than zero"):
        parse_amount_to_minor("0")

    with pytest.raises(ValueError, match="greater than zero"):
        parse_amount_to_minor("-15.00")


def test_empty_transactions_and_summary(temp_db_path: Path) -> None:
    tx_repo = TransactionRepository(temp_db_path)
    service = TransactionService(tx_repo)

    assert tx_repo.db_path == temp_db_path
    assert service.list_transactions() == []
    assert service.get_summary() == {"income": 0, "expense": 0, "balance": 0}


def test_add_get_update_delete_transaction_and_summary(temp_db_path: Path) -> None:
    cat_repo = CategoryRepository(temp_db_path)
    cat_service = CategoryService(cat_repo)
    categories = {c.name: c.id for c in cat_service.list_categories()}

    tx_service = TransactionService(TransactionRepository(temp_db_path), category_repo=cat_repo)

    salary = tx_service.add_transaction(
        date="2026-11-01",
        amount="5000.00",
        tx_type="income",
        category_id=categories["Salary"],
        note="Monthly salary",
    )
    assert salary.id is not None
    assert salary.amount == 500000
    assert salary.type == "income"

    groceries = tx_service.add_transaction(
        date="2026-11-05",
        amount=12550,
        tx_type="expense",
        category_id=categories["Groceries"],
        note="Kaufland",
        amount_is_minor=True,
    )
    assert groceries.id is not None
    assert groceries.amount == 12550

    summary = tx_service.get_summary()
    assert summary == {"income": 500000, "expense": 12550, "balance": 487450}

    updated = tx_service.update_transaction(
        transaction_id=groceries.id,
        date="2026-11-06",
        amount="150.00",
        tx_type="expense",
        category_id=None,
        note="Kaufland updated",
    )
    assert updated.amount == 15000
    assert updated.date == "2026-11-06"
    assert updated.category_id is None
    assert updated.note == "Kaufland updated"

    updated_minor = tx_service.update_transaction(
        transaction_id=groceries.id,
        date="2026-11-06",
        amount=20000,
        tx_type="expense",
        category_id=categories["Groceries"],
        note="Minor update",
        amount_is_minor=True,
    )
    assert updated_minor.amount == 20000

    tx_service.delete_transaction(groceries.id)
    assert len(tx_service.list_transactions()) == 1

    with pytest.raises(ValueError, match="does not exist"):
        tx_service.get_transaction(groceries.id)

    with pytest.raises(ValueError, match="does not exist"):
        tx_service.delete_transaction(groceries.id)


def test_transaction_validation_errors(temp_db_path: Path) -> None:
    cat_repo = CategoryRepository(temp_db_path)
    CategoryService(cat_repo)
    tx_repo = TransactionRepository(temp_db_path)
    tx_service = TransactionService(tx_repo, category_repo=cat_repo)

    with pytest.raises(ValueError, match="YYYY-MM-DD"):
        tx_service.add_transaction("14-11-2026", "10.00", "expense", None)

    with pytest.raises(ValueError, match="'income' or 'expense'"):
        tx_service.add_transaction("2026-11-14", "10.00", "transfer", None)

    with pytest.raises(ValueError, match="Category with id 9999 does not exist"):
        tx_service.add_transaction("2026-11-14", "10.00", "expense", 9999)

    with pytest.raises(ValueError, match="greater than zero"):
        tx_service.add_transaction("2026-11-14", 0, "expense", None, amount_is_minor=True)

    tx = tx_service.add_transaction("2026-11-14", "25.00", "expense", None)
    assert tx.id is not None

    with pytest.raises(ValueError, match="greater than zero"):
        tx_service.update_transaction(
            tx.id, "2026-11-14", -10, "expense", None, amount_is_minor=True
        )

    with patch.object(tx_repo, "update", return_value=None):
        with pytest.raises(ValueError, match="does not exist"):
            tx_service.update_transaction(tx.id, "2026-11-14", "30.00", "expense", None)
