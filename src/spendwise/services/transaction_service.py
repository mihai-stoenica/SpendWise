from collections import defaultdict
from datetime import date as dt_date
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

from spendwise.models import Transaction, TransactionType
from spendwise.repositories.category_repo import CategoryRepository
from spendwise.repositories.transaction_repo import TransactionRepository

VALID_TYPES: set[str] = {"income", "expense"}


def parse_amount_to_minor(value: str | int | float | Decimal) -> int:
    if isinstance(value, bool):
        raise ValueError("Amount must be a positive number.")
    text = str(value).strip().replace(",", ".")
    if not text:
        raise ValueError("Amount cannot be empty.")
    try:
        dec = Decimal(text)
    except InvalidOperation as exc:
        raise ValueError("Invalid amount format.") from exc
    if not dec.is_finite():
        raise ValueError("Invalid amount format.")
    minor = int((dec * Decimal("100")).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    if minor <= 0:
        raise ValueError("Amount must be greater than zero.")
    return minor


def format_minor_amount(minor_units: int) -> str:
    sign = "-" if minor_units < 0 else ""
    abs_val = abs(minor_units)
    major = abs_val // 100
    cents = abs_val % 100
    return f"{sign}{major}.{cents:02d}"


class TransactionService:
    def __init__(
        self,
        repo: TransactionRepository,
        category_repo: CategoryRepository | None = None,
    ) -> None:
        self._repo = repo
        self._category_repo = category_repo

    def _validate_date(self, date_str: str) -> str:
        cleaned = date_str.strip()
        try:
            dt_date.fromisoformat(cleaned)
        except ValueError as exc:
            raise ValueError("Date must be in YYYY-MM-DD format.") from exc
        return cleaned

    def _validate_type(self, tx_type: str) -> TransactionType:
        cleaned = tx_type.strip().lower()
        if cleaned not in VALID_TYPES:
            raise ValueError("Transaction type must be 'income' or 'expense'.")
        return "income" if cleaned == "income" else "expense"

    def _validate_category(self, category_id: int | None) -> int | None:
        if category_id is None:
            return None
        if self._category_repo is not None and self._category_repo.get_by_id(category_id) is None:
            raise ValueError(f"Category with id {category_id} does not exist.")
        return category_id

    def list_transactions(self) -> list[Transaction]:
        return self._repo.list_all()

    def get_transaction(self, transaction_id: int) -> Transaction:
        tx = self._repo.get_by_id(transaction_id)
        if tx is None:
            raise ValueError(f"Transaction with id {transaction_id} does not exist.")
        return tx

    def add_transaction(
        self,
        date: str,
        amount: str | int | float | Decimal,
        tx_type: str,
        category_id: int | None,
        note: str = "",
        attachment_path: str | None = None,
        amount_is_minor: bool = False,
    ) -> Transaction:
        valid_date = self._validate_date(date)
        valid_type = self._validate_type(tx_type)
        valid_category = self._validate_category(category_id)
        if amount_is_minor:
            if not isinstance(amount, int) or isinstance(amount, bool) or amount <= 0:
                raise ValueError("Amount must be greater than zero.")
            minor_amount = amount
        else:
            minor_amount = parse_amount_to_minor(amount)

        return self._repo.add(
            date=valid_date,
            amount=minor_amount,
            tx_type=valid_type,
            category_id=valid_category,
            note=note.strip(),
            attachment_path=attachment_path,
        )

    def update_transaction(
        self,
        transaction_id: int,
        date: str,
        amount: str | int | float | Decimal,
        tx_type: str,
        category_id: int | None,
        note: str = "",
        attachment_path: str | None = None,
        amount_is_minor: bool = False,
    ) -> Transaction:
        self.get_transaction(transaction_id)
        valid_date = self._validate_date(date)
        valid_type = self._validate_type(tx_type)
        valid_category = self._validate_category(category_id)
        if amount_is_minor:
            if not isinstance(amount, int) or isinstance(amount, bool) or amount <= 0:
                raise ValueError("Amount must be greater than zero.")
            minor_amount = amount
        else:
            minor_amount = parse_amount_to_minor(amount)

        updated = self._repo.update(
            transaction_id=transaction_id,
            date=valid_date,
            amount=minor_amount,
            tx_type=valid_type,
            category_id=valid_category,
            note=note.strip(),
            attachment_path=attachment_path,
        )
        if updated is None:
            raise ValueError(f"Transaction with id {transaction_id} does not exist.")
        return updated

    def delete_transaction(self, transaction_id: int) -> None:
        if not self._repo.delete(transaction_id):
            raise ValueError(f"Transaction with id {transaction_id} does not exist.")

    def get_summary(self) -> dict[str, int]:
        transactions = self._repo.list_all()
        income = sum(t.amount for t in transactions if t.type == "income")
        expense = sum(t.amount for t in transactions if t.type == "expense")
        return {
            "income": income,
            "expense": expense,
            "balance": income - expense,
        }

    def get_available_months(self) -> list[str]:
        months = {t.date[:7] for t in self._repo.list_all() if len(t.date) >= 7}
        return sorted(months, reverse=True)

    def get_spending_by_category(self, month: str | None = None) -> dict[str, int]:
        cat_names: dict[int, str] = {}
        if self._category_repo is not None:
            cat_names = {c.id: c.name for c in self._category_repo.list_all() if c.id is not None}

        totals: dict[str, int] = defaultdict(int)
        for tx in self._repo.list_all():
            if tx.type != "expense":
                continue
            if month is not None and not tx.date.startswith(month):
                continue
            name = (
                cat_names.get(tx.category_id, "Uncategorized")
                if tx.category_id is not None
                else "Uncategorized"
            )
            totals[name] += tx.amount

        return dict(sorted(totals.items(), key=lambda item: item[1], reverse=True))

    def get_monthly_income_vs_expense(self) -> list[dict[str, str | int]]:
        monthly: dict[str, dict[str, int]] = defaultdict(lambda: {"income": 0, "expense": 0})
        for tx in self._repo.list_all():
            month_key = tx.date[:7]
            if tx.type == "income":
                monthly[month_key]["income"] += tx.amount
            else:
                monthly[month_key]["expense"] += tx.amount

        return [
            {
                "month": m,
                "income": monthly[m]["income"],
                "expense": monthly[m]["expense"],
            }
            for m in sorted(monthly.keys())
        ]

    def get_balance_over_time(self) -> list[tuple[str, int]]:
        daily_net: dict[str, int] = defaultdict(int)
        for tx in self._repo.list_all():
            delta = tx.amount if tx.type == "income" else -tx.amount
            daily_net[tx.date] += delta

        running_balance = 0
        series: list[tuple[str, int]] = []
        for day in sorted(daily_net.keys()):
            running_balance += daily_net[day]
            series.append((day, running_balance))
        return series
