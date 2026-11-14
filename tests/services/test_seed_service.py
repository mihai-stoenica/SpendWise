from datetime import date
from pathlib import Path

from spendwise.repositories.category_repo import CategoryRepository
from spendwise.repositories.transaction_repo import TransactionRepository
from spendwise.services.category_service import CategoryService
from spendwise.services.seed_service import seed_demo_transactions
from spendwise.services.transaction_service import TransactionService


def test_seed_demo_transactions_is_deterministic(temp_db_path: Path, tmp_path: Path) -> None:
    cat_repo1 = CategoryRepository(temp_db_path)
    cat_service1 = CategoryService(cat_repo1)
    tx_service1 = TransactionService(
        TransactionRepository(temp_db_path),
        category_repo=cat_repo1,
    )

    count1 = seed_demo_transactions(
        transaction_service=tx_service1,
        category_service=cat_service1,
        months=3,
        seed=99,
        reference_date=date(2026, 3, 15),
    )
    assert count1 > 30

    summary1 = tx_service1.get_summary()
    assert summary1["income"] > 0
    assert summary1["expense"] > 0
    assert len(tx_service1.get_available_months()) == 3

    second_db = tmp_path / "second.db"
    from spendwise.repositories.db import init_db

    init_db(second_db)
    cat_repo2 = CategoryRepository(second_db)
    cat_service2 = CategoryService(cat_repo2)
    tx_service2 = TransactionService(
        TransactionRepository(second_db),
        category_repo=cat_repo2,
    )

    count2 = seed_demo_transactions(
        transaction_service=tx_service2,
        category_service=cat_service2,
        months=3,
        seed=99,
        reference_date=date(2026, 3, 15),
    )
    assert count2 == count1
    assert tx_service2.get_summary() == summary1
