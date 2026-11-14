"""Domain data models for SpendWise."""

from dataclasses import dataclass
from typing import Literal

TransactionType = Literal["income", "expense"]


@dataclass(frozen=True)
class Profile:
    """User profile metadata."""

    name: str
    password_hash: str | None = None
    theme: str = "system"


@dataclass(frozen=True)
class Category:
    """Transaction category."""

    id: int | None
    name: str
    is_default: bool = False


@dataclass(frozen=True)
class Transaction:
    """Income or expense entry (amount in integer minor units)."""

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
    """Monthly spending budget for a category (amount in integer minor units)."""

    id: int | None
    category_id: int
    monthly_amount: int


@dataclass(frozen=True)
class BudgetAlert:
    """Budget threshold alert (80% or 100%)."""

    category_id: int
    category_name: str
    level: Literal[80, 100]
    spent: int
    monthly_amount: int


@dataclass(frozen=True)
class ForecastResult:
    """Next-month spending forecast result."""

    total_forecast: int
    per_category: dict[str, int]
    low_confidence: bool
