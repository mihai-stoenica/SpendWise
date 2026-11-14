import customtkinter as ctk

from spendwise.models import Profile
from spendwise.paths import get_profile_db_path
from spendwise.repositories.category_repo import CategoryRepository
from spendwise.services.category_service import CategoryService
from spendwise.services.profile_service import ProfileService
from spendwise.ui.category_view import CategoryView
from spendwise.ui.profile_view import ProfileView


class SpendWiseApp(ctk.CTk):
    def __init__(self, profile_service: ProfileService | None = None) -> None:
        super().__init__()
        self._profile_service = profile_service or ProfileService()

        self.title("SpendWise")
        self.geometry("820x580")
        self.minsize(680, 500)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._active_frame: ctk.CTkFrame | None = None
        self.show_profile_view()

    def _clear_active_frame(self) -> None:
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

        theme_menu = ctk.CTkOptionMenu(
            header,
            values=["system", "light", "dark"],
            width=110,
            command=self._handle_theme_change,
        )
        theme_menu.set(profile.theme)
        theme_menu.grid(row=0, column=1, padx=8, pady=12)

        ctk.CTkButton(
            header,
            text="Switch Profile",
            width=130,
            command=self._handle_switch_profile,
        ).grid(row=0, column=2, padx=(8, 16), pady=12)

        tabs = ctk.CTkTabview(shell)
        tabs.grid(row=1, column=0, padx=16, pady=(4, 16), sticky="nsew")
        tabs.add("Categories")

        categories_tab = tabs.tab("Categories")
        categories_tab.grid_rowconfigure(0, weight=1)
        categories_tab.grid_columnconfigure(0, weight=1)

        db_path = get_profile_db_path(
            profile.name,
            base_dir=self._profile_service.profiles_dir.parent,
        )
        category_service = CategoryService(CategoryRepository(db_path))
        category_view = CategoryView(categories_tab, category_service=category_service)
        category_view.grid(row=0, column=0, sticky="nsew")

        self._active_frame = shell

    def _handle_theme_change(self, new_theme: str) -> None:
        updated = self._profile_service.update_theme(new_theme)
        ctk.set_appearance_mode(updated.theme)

    def _handle_switch_profile(self) -> None:
        self._profile_service.logout()
        self.show_profile_view()

    def run(self) -> None:
        self.mainloop()
