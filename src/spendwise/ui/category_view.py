import customtkinter as ctk

from spendwise.services.category_service import CategoryService


class CategoryView(ctk.CTkFrame):
    def __init__(
        self,
        master: ctk.CTk | ctk.CTkFrame,
        category_service: CategoryService,
    ) -> None:
        super().__init__(master)
        self._service = category_service

        self._build_ui()
        self.refresh_categories()

    def _build_ui(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        add_frame = ctk.CTkFrame(self)
        add_frame.grid(row=0, column=0, padx=16, pady=(16, 8), sticky="ew")
        add_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            add_frame,
            text="Add Custom Category:",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).grid(row=0, column=0, padx=12, pady=12, sticky="w")

        self._name_entry = ctk.CTkEntry(
            add_frame,
            placeholder_text="e.g. Subscriptions, Gym, Travel",
        )
        self._name_entry.grid(row=0, column=1, padx=8, pady=12, sticky="ew")

        ctk.CTkButton(
            add_frame,
            text="Add Category",
            width=130,
            command=self._handle_add,
        ).grid(row=0, column=2, padx=12, pady=12)

        self._status_label = ctk.CTkLabel(self, text="", text_color="tomato")
        self._status_label.grid(row=1, column=0, padx=16, pady=(0, 4), sticky="w")

        self._list_frame = ctk.CTkScrollableFrame(
            self,
            label_text="Categories (Default & Custom)",
        )
        self._list_frame.grid(row=2, column=0, padx=16, pady=(4, 16), sticky="nsew")
        self._list_frame.grid_columnconfigure(0, weight=1)

    def refresh_categories(self) -> None:
        for child in self._list_frame.winfo_children():
            child.destroy()

        categories = self._service.list_categories()
        for idx, category in enumerate(categories):
            row_frame = ctk.CTkFrame(self._list_frame)
            row_frame.grid(row=idx, column=0, padx=8, pady=4, sticky="ew")
            row_frame.grid_columnconfigure(0, weight=1)

            badge = "Default" if category.is_default else "Custom"
            ctk.CTkLabel(
                row_frame,
                text=f"{category.name}  ({badge})",
                font=ctk.CTkFont(size=14),
            ).grid(row=0, column=0, padx=12, pady=8, sticky="w")

            if not category.is_default and category.id is not None:
                ctk.CTkButton(
                    row_frame,
                    text="Delete",
                    width=80,
                    fg_color="firebrick",
                    hover_color="darkred",
                    command=lambda cid=category.id: self._handle_delete(cid),
                ).grid(row=0, column=1, padx=12, pady=6)

    def _handle_add(self) -> None:
        name = self._name_entry.get()
        try:
            self._service.add_category(name)
            self._name_entry.delete(0, "end")
            self._status_label.configure(text="")
            self.refresh_categories()
        except ValueError as exc:
            self._status_label.configure(text=str(exc))

    def _handle_delete(self, category_id: int) -> None:
        try:
            self._service.delete_category(category_id)
            self._status_label.configure(text="")
            self.refresh_categories()
        except ValueError as exc:
            self._status_label.configure(text=str(exc))
