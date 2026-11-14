import sqlite3
from pathlib import Path
from unittest.mock import patch

import pytest

from spendwise.repositories.category_repo import CategoryRepository
from spendwise.services.category_service import DEFAULT_CATEGORIES, CategoryService


def test_default_categories_seeded_automatically(temp_db_path: Path) -> None:
    repo = CategoryRepository(temp_db_path)
    service = CategoryService(repo)

    categories = service.list_categories()
    names = [c.name for c in categories]

    assert len(categories) == len(DEFAULT_CATEGORIES)
    assert set(names) == set(DEFAULT_CATEGORIES)
    assert all(c.is_default for c in categories)
    assert repo.db_path == temp_db_path


def test_seed_defaults_is_idempotent(temp_db_path: Path) -> None:
    repo = CategoryRepository(temp_db_path)
    service = CategoryService(repo)
    service.ensure_defaults()

    assert len(service.list_categories()) == len(DEFAULT_CATEGORIES)


def test_add_and_get_custom_category(temp_db_path: Path) -> None:
    service = CategoryService(CategoryRepository(temp_db_path))

    created = service.add_category("  Subscriptions  ")
    assert created.id is not None
    assert created.name == "Subscriptions"
    assert created.is_default is False

    fetched = service.get_category(created.id)
    assert fetched == created


def test_add_invalid_or_duplicate_category_raises(temp_db_path: Path) -> None:
    service = CategoryService(CategoryRepository(temp_db_path))

    with pytest.raises(ValueError, match="cannot be empty"):
        service.add_category("   ")

    with pytest.raises(ValueError, match="cannot exceed 50 characters"):
        service.add_category("A" * 51)

    with pytest.raises(ValueError, match="already exists"):
        service.add_category("groceries")


def test_get_nonexistent_category_raises(temp_db_path: Path) -> None:
    service = CategoryService(CategoryRepository(temp_db_path))

    with pytest.raises(ValueError, match="does not exist"):
        service.get_category(9999)


def test_delete_custom_and_protect_default_categories(temp_db_path: Path) -> None:
    repo = CategoryRepository(temp_db_path)
    service = CategoryService(repo)

    default_cat = service.list_categories()[0]
    assert default_cat.id is not None

    with pytest.raises(ValueError, match="Cannot delete default category"):
        service.delete_category(default_cat.id)

    custom = service.add_category("Gym")
    assert custom.id is not None
    service.delete_category(custom.id)

    with pytest.raises(ValueError, match="does not exist"):
        service.get_category(custom.id)


def test_delete_category_in_use_raises_value_error(temp_db_path: Path) -> None:
    repo = CategoryRepository(temp_db_path)
    service = CategoryService(repo)
    custom = service.add_category("Pet Care")
    assert custom.id is not None

    with patch.object(repo, "delete", side_effect=sqlite3.IntegrityError("FK constraint")):
        with pytest.raises(ValueError, match="is in use"):
            service.delete_category(custom.id)
