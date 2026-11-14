import re
from dataclasses import dataclass
from pathlib import Path

from fpdf import FPDF

from spendwise.services.transaction_service import TransactionService, format_minor_amount

MONTH_PATTERN = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


@dataclass(frozen=True)
class MonthlyReportSummary:
    month: str
    previous_month: str
    total_income: int
    total_expenses: int
    balance: int
    prev_income: int
    prev_expenses: int
    expense_diff: int
    expense_change_pct: float | None
    top_categories: list[tuple[str, int]]


def _previous_month_str(month: str) -> str:
    year_str, mon_str = month.split("-")
    year = int(year_str)
    mon = int(mon_str)
    if mon == 1:
        return f"{year - 1:04d}-12"
    return f"{year:04d}-{mon - 1:02d}"


def _sanitize_latin1(text: str) -> str:
    return text.encode("latin-1", errors="replace").decode("latin-1")


class ReportService:
    def __init__(self, transaction_service: TransactionService) -> None:
        self._tx_service = transaction_service

    def _validate_month(self, month: str) -> str:
        cleaned = month.strip()
        if not MONTH_PATTERN.match(cleaned):
            raise ValueError("Month must be in YYYY-MM format.")
        return cleaned

    def build_monthly_summary(self, month: str, top_n: int = 3) -> MonthlyReportSummary:
        valid_month = self._validate_month(month)
        prev_month = _previous_month_str(valid_month)

        all_tx = self._tx_service.list_transactions()

        cur_income = sum(
            t.amount for t in all_tx if t.type == "income" and t.date.startswith(valid_month)
        )
        cur_expenses = sum(
            t.amount for t in all_tx if t.type == "expense" and t.date.startswith(valid_month)
        )
        prev_income = sum(
            t.amount for t in all_tx if t.type == "income" and t.date.startswith(prev_month)
        )
        prev_expenses = sum(
            t.amount for t in all_tx if t.type == "expense" and t.date.startswith(prev_month)
        )

        expense_diff = cur_expenses - prev_expenses
        if prev_expenses > 0:
            expense_change_pct: float | None = round((expense_diff / prev_expenses) * 100.0, 1)
        else:
            expense_change_pct = None

        cat_spending = self._tx_service.get_spending_by_category(month=valid_month)
        top_categories = list(cat_spending.items())[: max(0, top_n)]

        return MonthlyReportSummary(
            month=valid_month,
            previous_month=prev_month,
            total_income=cur_income,
            total_expenses=cur_expenses,
            balance=cur_income - cur_expenses,
            prev_income=prev_income,
            prev_expenses=prev_expenses,
            expense_diff=expense_diff,
            expense_change_pct=expense_change_pct,
            top_categories=top_categories,
        )

    def generate_monthly_pdf(
        self,
        month: str,
        output_path: Path,
        profile_name: str = "Default",
    ) -> Path:
        summary = self.build_monthly_summary(month)
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)

        pdf.set_font("Helvetica", "B", 18)
        pdf.cell(
            0,
            12,
            _sanitize_latin1(f"SpendWise Monthly Report - {summary.month}"),
            new_x="LMARGIN",
            new_y="NEXT",
        )

        pdf.set_font("Helvetica", "", 11)
        pdf.cell(
            0,
            8,
            _sanitize_latin1(f"Profile: {profile_name}"),
            new_x="LMARGIN",
            new_y="NEXT",
        )
        pdf.ln(4)

        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 10, "1. Monthly Totals", new_x="LMARGIN", new_y="NEXT")

        pdf.set_font("Helvetica", "", 11)
        pdf.cell(
            0,
            8,
            f"Total Income: {format_minor_amount(summary.total_income)} RON",
            new_x="LMARGIN",
            new_y="NEXT",
        )
        pdf.cell(
            0,
            8,
            f"Total Expenses: {format_minor_amount(summary.total_expenses)} RON",
            new_x="LMARGIN",
            new_y="NEXT",
        )
        pdf.cell(
            0,
            8,
            f"Net Balance: {format_minor_amount(summary.balance)} RON",
            new_x="LMARGIN",
            new_y="NEXT",
        )
        pdf.ln(4)

        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(
            0,
            10,
            f"2. Comparison with Previous Month ({summary.previous_month})",
            new_x="LMARGIN",
            new_y="NEXT",
        )

        pdf.set_font("Helvetica", "", 11)
        pdf.cell(
            0,
            8,
            f"Previous Month Income: {format_minor_amount(summary.prev_income)} RON",
            new_x="LMARGIN",
            new_y="NEXT",
        )
        pdf.cell(
            0,
            8,
            f"Previous Month Expenses: {format_minor_amount(summary.prev_expenses)} RON",
            new_x="LMARGIN",
            new_y="NEXT",
        )

        sign = "+" if summary.expense_diff > 0 else ""
        diff_str = f"{sign}{format_minor_amount(summary.expense_diff)} RON"
        if summary.expense_change_pct is not None:
            pct_sign = "+" if summary.expense_change_pct > 0 else ""
            comparison_line = (
                f"Expense Change: {diff_str} ({pct_sign}{summary.expense_change_pct:.1f}%)"
            )
        else:
            comparison_line = (
                f"Expense Change: {diff_str} (no expenses in {summary.previous_month})"
            )

        pdf.cell(0, 8, comparison_line, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)

        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 10, "3. Top Spending Categories", new_x="LMARGIN", new_y="NEXT")

        pdf.set_font("Helvetica", "", 11)
        if summary.top_categories:
            for rank, (cat_name, amount_minor) in enumerate(summary.top_categories, start=1):
                line = (
                    f"{rank}. {_sanitize_latin1(cat_name)}: {format_minor_amount(amount_minor)} RON"
                )
                pdf.cell(0, 8, line, new_x="LMARGIN", new_y="NEXT")
        else:
            pdf.cell(
                0,
                8,
                "No expenses recorded for this month.",
                new_x="LMARGIN",
                new_y="NEXT",
            )

        pdf.output(str(output_path))
        return output_path
