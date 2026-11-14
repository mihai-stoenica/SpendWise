from dataclasses import dataclass
from typing import Literal

TransactionType = Literal["income", "expense"]


@dataclass(frozen=True)
class Profile:
    name: str
    password_hash: str | None = None
    theme: str = "system"

    @property
    def has_password(self) -> bool:
        return bool(self.password_hash)


@dataclass(frozen=True)
class Category:
    id: int | None
    name: str
    is_default: bool = False


@dataclass(frozen=True)
class Transaction:
    id: int | None
    date: str
    amount: int
    type: TransactionType
    category_id: int | None
    note: str = ""
    attachment_path: str | None = None
    created_at: str | None = None


@dataclass(frozen=True)
class Budget:
    id: int | None
    category_id: int
    monthly_amount: int


@dataclass(frozen=True)
class BudgetAlert:
    category_id: int
    category_name: str
    level: Literal[80, 100]
    spent: int
    monthly_amount: int


@dataclass(frozen=True)
class ForecastResult:
    total_forecast: int
    per_category: dict[str, int]
    low_confidence: bool
