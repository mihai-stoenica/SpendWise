from datetime import date as dt_date
from pathlib import Path
from tkinter import filedialog

import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from spendwise.services.report_service import ReportService
from spendwise.services.transaction_service import TransactionService


class DashboardView(ctk.CTkFrame):
    def __init__(
        self,
        master: ctk.CTk | ctk.CTkFrame,
        transaction_service: TransactionService,
        report_service: ReportService | None = None,
        profile_name: str = "Default",
    ) -> None:
        super().__init__(master, fg_color="transparent")
        self._tx_service = transaction_service
        self._report_service = report_service or ReportService(transaction_service)
        self._profile_name = profile_name
        self._canvas: FigureCanvasTkAgg | None = None

        self._build_ui()
        self.refresh_charts()

    def _build_ui(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        toolbar = ctk.CTkFrame(self)
        toolbar.grid(row=0, column=0, padx=16, pady=(12, 8), sticky="ew")
        toolbar.grid_columnconfigure(4, weight=1)

        ctk.CTkLabel(
            toolbar,
            text="Category Breakdown Month:",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).grid(row=0, column=0, padx=(12, 8), pady=10, sticky="w")

        self._month_menu = ctk.CTkOptionMenu(
            toolbar,
            values=["All Months"],
            width=140,
            command=lambda _: self._draw_figures(),
        )
        self._month_menu.set("All Months")
        self._month_menu.grid(row=0, column=1, padx=6, pady=10, sticky="w")

        ctk.CTkButton(
            toolbar,
            text="Refresh Charts",
            width=120,
            command=self.refresh_charts,
        ).grid(row=0, column=2, padx=8, pady=10, sticky="w")

        ctk.CTkButton(
            toolbar,
            text="Export Monthly PDF",
            width=155,
            command=self._handle_export_pdf,
        ).grid(row=0, column=3, padx=8, pady=10, sticky="w")

        self._status_label = ctk.CTkLabel(
            toolbar,
            text="",
            font=ctk.CTkFont(size=12),
        )
        self._status_label.grid(row=0, column=4, padx=12, pady=10, sticky="w")

        self._chart_container = ctk.CTkFrame(self, fg_color="transparent")
        self._chart_container.grid(row=1, column=0, padx=16, pady=(0, 12), sticky="nsew")
        self._chart_container.grid_rowconfigure(0, weight=1)
        self._chart_container.grid_columnconfigure(0, weight=1)

    def _resolve_report_month(self) -> str:
        selected = self._month_menu.get()
        if selected != "All Months":
            return selected
        available = self._tx_service.get_available_months()
        if available:
            return available[0]
        return dt_date.today().strftime("%Y-%m")

    def _handle_export_pdf(self) -> None:
        report_month = self._resolve_report_month()
        default_filename = f"SpendWise_Report_{self._profile_name}_{report_month}.pdf"
        chosen_path = filedialog.asksaveasfilename(
            parent=self.winfo_toplevel(),
            title=f"Save Monthly PDF Report ({report_month})",
            defaultextension=".pdf",
            initialfile=default_filename,
            filetypes=[("PDF files", "*.pdf")],
        )
        if not chosen_path:
            return

        try:
            saved = self._report_service.generate_monthly_pdf(
                month=report_month,
                output_path=Path(chosen_path),
                profile_name=self._profile_name,
            )
            self._status_label.configure(
                text=f"Saved PDF: {saved.name}",
                text_color="#2ecc71",
            )
        except (ValueError, OSError) as exc:
            self._status_label.configure(text=str(exc), text_color="tomato")

    def refresh_charts(self) -> None:
        months = self._tx_service.get_available_months()
        options = ["All Months", *months]
        current = self._month_menu.get()
        self._month_menu.configure(values=options)
        if current not in options:
            self._month_menu.set("All Months")
        self._draw_figures()

    def _get_theme_colors(self) -> tuple[str, str, str]:
        mode = ctk.get_appearance_mode().lower()
        if mode == "dark":
            return "#2b2b2b", "#1f1f1f", "#f0f0f0"
        return "#ebebeb", "#ffffff", "#1a1a1a"

    def _draw_figures(self) -> None:
        if self._canvas is not None:
            self._canvas.get_tk_widget().destroy()
            self._canvas = None

        fig_bg, axes_bg, text_color = self._get_theme_colors()

        fig = Figure(figsize=(8.6, 5.2), dpi=100, facecolor=fig_bg)
        ax_pie = fig.add_subplot(2, 2, 1)
        ax_bar = fig.add_subplot(2, 2, 2)
        ax_line = fig.add_subplot(2, 1, 2)

        for ax in (ax_pie, ax_bar, ax_line):
            ax.set_facecolor(axes_bg)
            ax.tick_params(colors=text_color, labelsize=8)
            for spine in ax.spines.values():
                spine.set_color(text_color)

        selected_month = self._month_menu.get()
        month_filter = None if selected_month == "All Months" else selected_month
        spending_by_cat = self._tx_service.get_spending_by_category(month=month_filter)

        if spending_by_cat:
            labels = list(spending_by_cat.keys())
            values = [v / 100.0 for v in spending_by_cat.values()]
            wedges, texts, autotexts = ax_pie.pie(
                values,
                labels=labels,
                autopct="%1.0f%%",
                startangle=140,
                wedgeprops={"width": 0.45},
                textprops={"color": text_color, "fontsize": 8},
            )
            for autotext in autotexts:
                autotext.set_color(text_color)
        else:
            ax_pie.text(
                0.5,
                0.5,
                "No expense data",
                ha="center",
                va="center",
                color=text_color,
                fontsize=10,
            )
            ax_pie.set_xticks([])
            ax_pie.set_yticks([])

        ax_pie.set_title(
            f"Spending by Category ({selected_month})",
            color=text_color,
            fontsize=10,
            fontweight="bold",
        )

        monthly_data = self._tx_service.get_monthly_income_vs_expense()
        if monthly_data:
            months = [str(item["month"]) for item in monthly_data]
            incomes = [int(item["income"]) / 100.0 for item in monthly_data]
            expenses = [int(item["expense"]) / 100.0 for item in monthly_data]
            positions = list(range(len(months)))
            width = 0.36

            ax_bar.bar(
                [p - width / 2 for p in positions],
                incomes,
                width=width,
                label="Income",
                color="#2ecc71",
            )
            ax_bar.bar(
                [p + width / 2 for p in positions],
                expenses,
                width=width,
                label="Expenses",
                color="#e74c3c",
            )
            ax_bar.set_xticks(positions)
            ax_bar.set_xticklabels(months, rotation=25, ha="right", color=text_color)
            ax_bar.set_ylabel("RON", color=text_color, fontsize=8)
            legend = ax_bar.legend(
                facecolor=axes_bg,
                edgecolor=text_color,
                fontsize=8,
            )
            for text in legend.get_texts():
                text.set_color(text_color)
        else:
            ax_bar.text(
                0.5,
                0.5,
                "No monthly data",
                ha="center",
                va="center",
                color=text_color,
                fontsize=10,
            )
            ax_bar.set_xticks([])
            ax_bar.set_yticks([])

        ax_bar.set_title(
            "Income vs. Expenses per Month",
            color=text_color,
            fontsize=10,
            fontweight="bold",
        )

        balance_series = self._tx_service.get_balance_over_time()
        if balance_series:
            dates = [point[0] for point in balance_series]
            balances = [point[1] / 100.0 for point in balance_series]
            ax_line.plot(dates, balances, marker="o", linewidth=2, color="#3498db")
            ax_line.axhline(0, color=text_color, linestyle="--", linewidth=0.7, alpha=0.5)
            ax_line.set_ylabel("Balance (RON)", color=text_color, fontsize=8)
            step = max(1, len(dates) // 8)
            tick_indices = list(range(0, len(dates), step))
            ax_line.set_xticks(tick_indices)
            ax_line.set_xticklabels(
                [dates[i] for i in tick_indices],
                rotation=20,
                ha="right",
                color=text_color,
            )
        else:
            ax_line.text(
                0.5,
                0.5,
                "No balance history",
                ha="center",
                va="center",
                color=text_color,
                fontsize=10,
            )
            ax_line.set_xticks([])
            ax_line.set_yticks([])

        ax_line.set_title(
            "Balance Over Time",
            color=text_color,
            fontsize=10,
            fontweight="bold",
        )

        fig.tight_layout(pad=2.0)

        canvas = FigureCanvasTkAgg(fig, master=self._chart_container)
        canvas.draw()
        tk_widget = canvas.get_tk_widget()
        tk_widget.configure(bg=fig_bg, highlightthickness=0, bd=0)
        tk_widget.grid(row=0, column=0, sticky="nsew")
        self._canvas = canvas
