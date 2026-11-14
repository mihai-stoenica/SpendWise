import sqlite3

from spendwise.models import Category
from spendwise.repositories.category_repo import CategoryRepository

DEFAULT_CATEGORIES: tuple[str, ...] = (
    "Groceries",
    "Rent",
    "Utilities",
    "Transport",
    "Dining",
    "Entertainment",
    "Health",
    "Shopping",
    "Salary",
    "Other",
)


class CategoryService:
    def __init__(self, repo: CategoryRepository) -> None:
        self._repo = repo
        self.ensure_defaults()

    def ensure_defaults(self) -> None:
        self._repo.seed_defaults(DEFAULT_CATEGORIES)

    def list_categories(self) -> list[Category]:
        return self._repo.list_all()

    def get_category(self, category_id: int) -> Category:
        category = self._repo.get_by_id(category_id)
        if category is None:
            raise ValueError(f"Category with id {category_id} does not exist.")
        return category

    def add_category(self, name: str) -> Category:
        cleaned = name.strip()
        if not cleaned:
            raise ValueError("Category name cannot be empty.")
        if len(cleaned) > 50:
            raise ValueError("Category name cannot exceed 50 characters.")

        existing = self._repo.get_by_name(cleaned)
        if existing is not None:
            raise ValueError(f"Category '{existing.name}' already exists.")

        return self._repo.add(cleaned, is_default=False)

    def delete_category(self, category_id: int) -> None:
        category = self.get_category(category_id)
        if category.is_default:
            raise ValueError(f"Cannot delete default category '{category.name}'.")
        try:
            self._repo.delete(category_id)
        except sqlite3.IntegrityError as exc:
            raise ValueError(
                f"Cannot delete category '{category.name}' because it is in use."
            ) from exc
