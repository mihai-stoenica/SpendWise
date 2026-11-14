import customtkinter as ctk

from spendwise.models import Profile
from spendwise.paths import get_profile_db_path
from spendwise.repositories.category_repo import CategoryRepository
from spendwise.repositories.transaction_repo import TransactionRepository
from spendwise.services.category_service import CategoryService
from spendwise.services.profile_service import ProfileService
from spendwise.services.report_service import ReportService
from spendwise.services.seed_service import seed_demo_transactions
from spendwise.services.transaction_service import TransactionService
from spendwise.ui.category_view import CategoryView
from spendwise.ui.dashboard_view import DashboardView
from spendwise.ui.profile_view import ProfileView
from spendwise.ui.transaction_view import TransactionView


class SpendWiseApp(ctk.CTk):
    def __init__(self, profile_service: ProfileService | None = None) -> None:
        super().__init__()
        self._profile_service = profile_service or ProfileService()
        self._dashboard_view: DashboardView | None = None

        self.title("SpendWise")
        self.geometry("940x680")
        self.minsize(780, 560)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._active_frame: ctk.CTkFrame | None = None
        self.show_profile_view()

    def _clear_active_frame(self) -> None:
        self._dashboard_view = None
        if self._active_frame is not None:
            self._active_frame.destroy()
            self._active_frame = None

    def show_profile_view(self) -> None:
        self._clear_active_frame()
        view = ProfileView(
            self,
            profile_service=self._profile_service,
            on_authenticated=self._on_profile_authenticated,
        )
        view.grid(row=0, column=0, sticky="nsew")
        self._active_frame = view

    def _on_profile_authenticated(self, profile: Profile) -> None:
        ctk.set_appearance_mode(profile.theme)
        self.show_dashboard_shell(profile)

    def show_dashboard_shell(self, profile: Profile) -> None:
        self._clear_active_frame()
        shell = ctk.CTkFrame(self)
        shell.grid(row=0, column=0, sticky="nsew")
        shell.grid_columnconfigure(0, weight=1)
        shell.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(shell, height=52)
        header.grid(row=0, column=0, padx=16, pady=(16, 8), sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header,
            text=f"Active Profile: {profile.name}",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).grid(row=0, column=0, padx=16, pady=12, sticky="w")

        db_path = get_profile_db_path(
            profile.name,
            base_dir=self._profile_service.profiles_dir.parent,
        )
        category_repo = CategoryRepository(db_path)
        category_service = CategoryService(category_repo)
        transaction_service = TransactionService(
            TransactionRepository(db_path),
            category_repo=category_repo,
        )
        report_service = ReportService(transaction_service)

        tabs = ctk.CTkTabview(shell)
        tabs.grid(row=1, column=0, padx=16, pady=(4, 16), sticky="nsew")
        tabs.add("Transactions")
        tabs.add("Dashboard")
        tabs.add("Categories")

        transactions_tab = tabs.tab("Transactions")
        transactions_tab.grid_rowconfigure(0, weight=1)
        transactions_tab.grid_columnconfigure(0, weight=1)

        dashboard_tab = tabs.tab("Dashboard")
        dashboard_tab.grid_rowconfigure(0, weight=1)
        dashboard_tab.grid_columnconfigure(0, weight=1)

        categories_tab = tabs.tab("Categories")
        categories_tab.grid_rowconfigure(0, weight=1)
        categories_tab.grid_columnconfigure(0, weight=1)

        dashboard_view = DashboardView(
            dashboard_tab,
            transaction_service=transaction_service,
            report_service=report_service,
            profile_name=profile.name,
        )
        dashboard_view.grid(row=0, column=0, sticky="nsew")
        self._dashboard_view = dashboard_view

        tx_view = TransactionView(
            transactions_tab,
            transaction_service=transaction_service,
            category_service=category_service,
            on_changed=dashboard_view.refresh_charts,
        )
        tx_view.grid(row=0, column=0, sticky="nsew")

        def _on_categories_changed() -> None:
            tx_view.refresh_all()
            dashboard_view.refresh_charts()

        category_view = CategoryView(
            categories_tab,
            category_service=category_service,
            on_changed=_on_categories_changed,
        )
        category_view.grid(row=0, column=0, sticky="nsew")

        def _handle_seed_demo_data() -> None:
            seed_demo_transactions(
                transaction_service=transaction_service,
                category_service=category_service,
                months=6,
            )
            tx_view.refresh_all()
            dashboard_view.refresh_charts()

        ctk.CTkButton(
            header,
            text="Seed Demo Data",
            width=130,
            fg_color="#27ae60",
            hover_color="#1e8449",
            command=_handle_seed_demo_data,
        ).grid(row=0, column=1, padx=6, pady=12)

        theme_menu = ctk.CTkOptionMenu(
            header,
            values=["system", "light", "dark"],
            width=110,
            command=self._handle_theme_change,
        )
        theme_menu.set(profile.theme)
        theme_menu.grid(row=0, column=2, padx=6, pady=12)

        ctk.CTkButton(
            header,
            text="Switch Profile",
            width=130,
            command=self._handle_switch_profile,
        ).grid(row=0, column=3, padx=(6, 16), pady=12)

        self._active_frame = shell

    def _handle_theme_change(self, new_theme: str) -> None:
        updated = self._profile_service.update_theme(new_theme)
        ctk.set_appearance_mode(updated.theme)
        if self._dashboard_view is not None:
            self._dashboard_view.refresh_charts()

    def _handle_switch_profile(self) -> None:
        self._profile_service.logout()
        self.show_profile_view()

    def run(self) -> None:
        self.mainloop()
