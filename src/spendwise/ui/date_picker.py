import calendar
from collections.abc import Callable
from datetime import date as dt_date

import customtkinter as ctk


class DatePickerPopup(ctk.CTkToplevel):
    def __init__(
        self,
        master: ctk.CTk | ctk.CTkFrame,
        initial_date: dt_date,
        on_select: Callable[[str], None],
    ) -> None:
        super().__init__(master)
        self._on_select = on_select
        self._year = initial_date.year
        self._month = initial_date.month
        self._selected_date = initial_date

        self.title("Select Date")
        self.geometry("310x310")
        self.resizable(False, False)
        self.transient(master.winfo_toplevel())
        self.grab_set()

        self._build_ui()
        self._render_calendar()

    def _build_ui(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        nav = ctk.CTkFrame(self, fg_color="transparent")
        nav.grid(row=0, column=0, padx=10, pady=(10, 4), sticky="ew")
        nav.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(
            nav,
            text="<",
            width=32,
            height=28,
            command=self._prev_month,
        ).grid(row=0, column=0, padx=4)

        self._header_label = ctk.CTkLabel(
            nav,
            text="",
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        self._header_label.grid(row=0, column=1, padx=4)

        ctk.CTkButton(
            nav,
            text=">",
            width=32,
            height=28,
            command=self._next_month,
        ).grid(row=0, column=2, padx=4)

        self._grid_frame = ctk.CTkFrame(self)
        self._grid_frame.grid(row=1, column=0, padx=10, pady=4, sticky="nsew")
        for col in range(7):
            self._grid_frame.grid_columnconfigure(col, weight=1)

        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.grid(row=2, column=0, padx=10, pady=(4, 10), sticky="ew")
        footer.grid_columnconfigure(0, weight=1)

        ctk.CTkButton(
            footer,
            text="Today",
            height=28,
            command=self._pick_today,
        ).grid(row=0, column=0, sticky="ew")

    def _prev_month(self) -> None:
        if self._month == 1:
            self._month = 12
            self._year -= 1
        else:
            self._month -= 1
        self._render_calendar()

    def _next_month(self) -> None:
        if self._month == 12:
            self._month = 1
            self._year += 1
        else:
            self._month += 1
        self._render_calendar()

    def _render_calendar(self) -> None:
        for child in self._grid_frame.winfo_children():
            child.destroy()

        month_name = calendar.month_name[self._month]
        self._header_label.configure(text=f"{month_name} {self._year}")

        weekdays = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
        for col, day_label in enumerate(weekdays):
            ctk.CTkLabel(
                self._grid_frame,
                text=day_label,
                font=ctk.CTkFont(size=12, weight="bold"),
            ).grid(row=0, column=col, padx=2, pady=(6, 4))

        cal = calendar.Calendar(firstweekday=0)
        weeks = cal.monthdayscalendar(self._year, self._month)

        for row_idx, week in enumerate(weeks, start=1):
            for col_idx, day in enumerate(week):
                if day == 0:
                    continue
                is_selected = (
                    self._year == self._selected_date.year
                    and self._month == self._selected_date.month
                    and day == self._selected_date.day
                )
                btn = ctk.CTkButton(
                    self._grid_frame,
                    text=str(day),
                    width=34,
                    height=28,
                    fg_color="#1f6aa5" if is_selected else "transparent",
                    text_color=("gray10", "gray90") if not is_selected else "white",
                    hover_color=("gray75", "gray30"),
                    command=lambda d=day: self._select_day(d),
                )
                btn.grid(row=row_idx, column=col_idx, padx=2, pady=2)

    def _select_day(self, day: int) -> None:
        chosen = dt_date(self._year, self._month, day)
        self._on_select(chosen.isoformat())
        self.destroy()

    def _pick_today(self) -> None:
        self._on_select(dt_date.today().isoformat())
        self.destroy()
