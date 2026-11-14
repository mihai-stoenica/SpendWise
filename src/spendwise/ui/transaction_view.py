from collections.abc import Callable
from datetime import date as dt_date

import customtkinter as ctk

from spendwise.models import Category, Transaction
from spendwise.services.category_service import CategoryService
from spendwise.services.transaction_service import TransactionService, format_minor_amount
from spendwise.ui.date_picker import DatePickerPopup


class TransactionView(ctk.CTkFrame):
    def __init__(
        self,
        master: ctk.CTk | ctk.CTkFrame,
        transaction_service: TransactionService,
        category_service: CategoryService,
        on_changed: Callable[[], None] | None = None,
    ) -> None:
        super().__init__(master)
        self._tx_service = transaction_service
        self._cat_service = category_service
        self._on_changed = on_changed
        self._categories_by_name: dict[str, Category] = {}
        self._categories_by_id: dict[int, Category] = {}
        self._editing_id: int | None = None

        self._build_ui()
        self.refresh_all()

    def _build_ui(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        summary_frame = ctk.CTkFrame(self)
        summary_frame.grid(row=0, column=0, padx=16, pady=(12, 6), sticky="ew")
        summary_frame.grid_columnconfigure((0, 1, 2), weight=1)

        self._income_label = ctk.CTkLabel(
            summary_frame,
            text="Income: 0.00 RON",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#2ecc71",
        )
        self._income_label.grid(row=0, column=0, padx=12, pady=10)

        self._expense_label = ctk.CTkLabel(
            summary_frame,
            text="Expenses: 0.00 RON",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#e74c3c",
        )
        self._expense_label.grid(row=0, column=1, padx=12, pady=10)

        self._balance_label = ctk.CTkLabel(
            summary_frame,
            text="Balance: 0.00 RON",
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        self._balance_label.grid(row=0, column=2, padx=12, pady=10)

        form_frame = ctk.CTkFrame(self)
        form_frame.grid(row=1, column=0, padx=16, pady=6, sticky="ew")
        form_frame.grid_columnconfigure(1, weight=1)
        form_frame.grid_columnconfigure(3, weight=1)

        ctk.CTkLabel(form_frame, text="Type:").grid(
            row=0, column=0, padx=(12, 6), pady=8, sticky="w"
        )
        self._type_menu = ctk.CTkOptionMenu(
            form_frame,
            values=["expense", "income"],
            width=120,
        )
        self._type_menu.set("expense")
        self._type_menu.grid(row=0, column=1, padx=6, pady=8, sticky="w")

        ctk.CTkLabel(form_frame, text="Amount (RON):").grid(
            row=0, column=2, padx=(12, 6), pady=8, sticky="w"
        )
        self._amount_entry = ctk.CTkEntry(form_frame, placeholder_text="e.g. 45.50")
        self._amount_entry.grid(row=0, column=3, padx=(6, 12), pady=8, sticky="ew")

        ctk.CTkLabel(form_frame, text="Date:").grid(
            row=1, column=0, padx=(12, 6), pady=8, sticky="w"
        )
        date_box = ctk.CTkFrame(form_frame, fg_color="transparent")
        date_box.grid(row=1, column=1, padx=6, pady=8, sticky="ew")
        date_box.grid_columnconfigure(0, weight=1)

        self._date_entry = ctk.CTkEntry(date_box)
        self._date_entry.insert(0, dt_date.today().isoformat())
        self._date_entry.grid(row=0, column=0, padx=(0, 6), sticky="ew")

        ctk.CTkButton(
            date_box,
            text="Pick",
            width=60,
            command=self._open_date_picker,
        ).grid(row=0, column=1)

        ctk.CTkLabel(form_frame, text="Category:").grid(
            row=1, column=2, padx=(12, 6), pady=8, sticky="w"
        )
        self._category_menu = ctk.CTkOptionMenu(form_frame, values=["Other"])
        self._category_menu.grid(row=1, column=3, padx=(6, 12), pady=8, sticky="ew")

        ctk.CTkLabel(form_frame, text="Note:").grid(
            row=2, column=0, padx=(12, 6), pady=8, sticky="w"
        )
        self._note_entry = ctk.CTkEntry(form_frame, placeholder_text="Optional description")
        self._note_entry.grid(row=2, column=1, columnspan=2, padx=6, pady=8, sticky="ew")

        btn_box = ctk.CTkFrame(form_frame, fg_color="transparent")
        btn_box.grid(row=2, column=3, padx=(6, 12), pady=8, sticky="e")

        self._submit_btn = ctk.CTkButton(
            btn_box,
            text="Add Transaction",
            width=130,
            command=self._handle_submit,
        )
        self._submit_btn.grid(row=0, column=0, padx=4)

        self._cancel_btn = ctk.CTkButton(
            btn_box,
            text="Cancel",
            width=75,
            fg_color="gray40",
            command=self._reset_form,
        )

        self._status_label = ctk.CTkLabel(self, text="", text_color="tomato")
        self._status_label.grid(row=2, column=0, padx=16, pady=(0, 4), sticky="w")

        self._list_frame = ctk.CTkScrollableFrame(self, label_text="Transactions")
        self._list_frame.grid(row=3, column=0, padx=16, pady=(4, 12), sticky="nsew")
        self._list_frame.grid_columnconfigure(0, weight=1)

    def _open_date_picker(self) -> None:
        raw = self._date_entry.get().strip()
        try:
            current = dt_date.fromisoformat(raw)
        except ValueError:
            current = dt_date.today()

        DatePickerPopup(self, initial_date=current, on_select=self._set_date_str)

    def _set_date_str(self, iso_date: str) -> None:
        self._date_entry.delete(0, "end")
        self._date_entry.insert(0, iso_date)

    def refresh_all(self) -> None:
        self._refresh_category_options()
        self._refresh_summary()
        self._refresh_list()

    def _refresh_category_options(self) -> None:
        categories = self._cat_service.list_categories()
        self._categories_by_name = {c.name: c for c in categories}
        self._categories_by_id = {c.id: c for c in categories if c.id is not None}
        names = list(self._categories_by_name.keys())
        if names:
            current = self._category_menu.get()
            self._category_menu.configure(values=names)
            self._category_menu.set(current if current in self._categories_by_name else names[0])

    def _refresh_summary(self) -> None:
        summary = self._tx_service.get_summary()
        self._income_label.configure(text=f"Income: {format_minor_amount(summary['income'])} RON")
        self._expense_label.configure(
            text=f"Expenses: {format_minor_amount(summary['expense'])} RON"
        )
        self._balance_label.configure(
            text=f"Balance: {format_minor_amount(summary['balance'])} RON"
        )

    def _refresh_list(self) -> None:
        for child in self._list_frame.winfo_children():
            child.destroy()

        transactions = self._tx_service.list_transactions()
        if not transactions:
            ctk.CTkLabel(
                self._list_frame,
                text="No transactions recorded yet.",
            ).grid(row=0, column=0, padx=12, pady=12, sticky="w")
            return

        for idx, tx in enumerate(transactions):
            row = ctk.CTkFrame(self._list_frame)
            row.grid(row=idx, column=0, padx=6, pady=4, sticky="ew")
            row.grid_columnconfigure(0, weight=1)

            cat_name = (
                self._categories_by_id[tx.category_id].name
                if tx.category_id in self._categories_by_id
                else "Uncategorized"
            )
            sign = "+" if tx.type == "income" else "-"
            amount_str = f"{sign}{format_minor_amount(tx.amount)} RON"
            note_part = f" — {tx.note}" if tx.note else ""
            summary_text = f"{tx.date}  |  [{cat_name}]  {amount_str}{note_part}"

            ctk.CTkLabel(
                row,
                text=summary_text,
                font=ctk.CTkFont(size=13),
            ).grid(row=0, column=0, padx=12, pady=8, sticky="w")

            if tx.id is not None:
                ctk.CTkButton(
                    row,
                    text="Edit",
                    width=65,
                    command=lambda item=tx: self._start_edit(item),
                ).grid(row=0, column=1, padx=4, pady=6)

                ctk.CTkButton(
                    row,
                    text="Delete",
                    width=65,
                    fg_color="firebrick",
                    hover_color="darkred",
                    command=lambda tid=tx.id: self._handle_delete(tid),
                ).grid(row=0, column=2, padx=(4, 10), pady=6)

    def _start_edit(self, tx: Transaction) -> None:
        self._editing_id = tx.id
        self._type_menu.set(tx.type)
        self._amount_entry.delete(0, "end")
        self._amount_entry.insert(0, format_minor_amount(tx.amount))
        self._date_entry.delete(0, "end")
        self._date_entry.insert(0, tx.date)

        if tx.category_id in self._categories_by_id:
            self._category_menu.set(self._categories_by_id[tx.category_id].name)

        self._note_entry.delete(0, "end")
        if tx.note:
            self._note_entry.insert(0, tx.note)

        self._submit_btn.configure(text="Save Changes")
        self._cancel_btn.grid(row=0, column=1, padx=4)
        self._status_label.configure(text="")

    def _reset_form(self) -> None:
        self._editing_id = None
        self._type_menu.set("expense")
        self._amount_entry.delete(0, "end")
        self._date_entry.delete(0, "end")
        self._date_entry.insert(0, dt_date.today().isoformat())
        self._note_entry.delete(0, "end")
        self._submit_btn.configure(text="Add Transaction")
        self._cancel_btn.grid_forget()
        self._status_label.configure(text="")

    def _handle_submit(self) -> None:
        tx_type = self._type_menu.get()
        amount_str = self._amount_entry.get()
        date_str = self._date_entry.get()
        cat_name = self._category_menu.get()
        category = self._categories_by_name.get(cat_name)
        category_id = category.id if category else None
        note = self._note_entry.get()

        try:
            if self._editing_id is None:
                self._tx_service.add_transaction(
                    date=date_str,
                    amount=amount_str,
                    tx_type=tx_type,
                    category_id=category_id,
                    note=note,
                )
            else:
                self._tx_service.update_transaction(
                    transaction_id=self._editing_id,
                    date=date_str,
                    amount=amount_str,
                    tx_type=tx_type,
                    category_id=category_id,
                    note=note,
                )
            self._reset_form()
            self.refresh_all()
            if self._on_changed is not None:
                self._on_changed()
        except ValueError as exc:
            self._status_label.configure(text=str(exc))

    def _handle_delete(self, transaction_id: int) -> None:
        try:
            self._tx_service.delete_transaction(transaction_id)
            if self._editing_id == transaction_id:
                self._reset_form()
            self._status_label.configure(text="")
            self.refresh_all()
            if self._on_changed is not None:
                self._on_changed()
        except ValueError as exc:
            self._status_label.configure(text=str(exc))
