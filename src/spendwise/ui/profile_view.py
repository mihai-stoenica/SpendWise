from collections.abc import Callable

import customtkinter as ctk

from spendwise.models import Profile
from spendwise.services.profile_service import ProfileService


class ProfileView(ctk.CTkFrame):
    def __init__(
        self,
        master: ctk.CTk | ctk.CTkFrame,
        profile_service: ProfileService,
        on_authenticated: Callable[[Profile], None],
    ) -> None:
        super().__init__(master)
        self._service = profile_service
        self._on_authenticated = on_authenticated
        self._profiles_by_name: dict[str, Profile] = {}

        self._build_ui()
        self.refresh_profiles()

    def _build_ui(self) -> None:
        self.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            self,
            text="SpendWise — Select or Create Profile",
            font=ctk.CTkFont(size=22, weight="bold"),
        )
        title.grid(row=0, column=0, padx=24, pady=(28, 16))

        login_frame = ctk.CTkFrame(self)
        login_frame.grid(row=1, column=0, padx=32, pady=10, sticky="ew")
        login_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            login_frame,
            text="Log In to Existing Profile",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).grid(row=0, column=0, columnspan=2, padx=16, pady=(14, 8), sticky="w")

        ctk.CTkLabel(login_frame, text="Profile:").grid(
            row=1, column=0, padx=16, pady=6, sticky="w"
        )
        self._profile_dropdown = ctk.CTkOptionMenu(
            login_frame,
            values=["(No profiles yet)"],
            command=self._on_profile_selected,
        )
        self._profile_dropdown.grid(row=1, column=1, padx=16, pady=6, sticky="ew")

        ctk.CTkLabel(login_frame, text="Password:").grid(
            row=2, column=0, padx=16, pady=6, sticky="w"
        )
        self._login_password_entry = ctk.CTkEntry(
            login_frame,
            placeholder_text="Leave blank if no password",
            show="*",
        )
        self._login_password_entry.grid(row=2, column=1, padx=16, pady=6, sticky="ew")

        self._login_button = ctk.CTkButton(
            login_frame,
            text="Log In",
            command=self._handle_login,
        )
        self._login_button.grid(row=3, column=0, columnspan=2, padx=16, pady=(10, 14), sticky="ew")

        create_frame = ctk.CTkFrame(self)
        create_frame.grid(row=2, column=0, padx=32, pady=10, sticky="ew")
        create_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            create_frame,
            text="Create New Profile",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).grid(row=0, column=0, columnspan=2, padx=16, pady=(14, 8), sticky="w")

        ctk.CTkLabel(create_frame, text="Name:").grid(row=1, column=0, padx=16, pady=6, sticky="w")
        self._new_name_entry = ctk.CTkEntry(
            create_frame,
            placeholder_text="e.g. Personal",
        )
        self._new_name_entry.grid(row=1, column=1, padx=16, pady=6, sticky="ew")

        ctk.CTkLabel(create_frame, text="Password (optional):").grid(
            row=2, column=0, padx=16, pady=6, sticky="w"
        )
        self._new_password_entry = ctk.CTkEntry(
            create_frame,
            placeholder_text="Optional password",
            show="*",
        )
        self._new_password_entry.grid(row=2, column=1, padx=16, pady=6, sticky="ew")

        self._create_button = ctk.CTkButton(
            create_frame,
            text="Create Profile",
            command=self._handle_create,
        )
        self._create_button.grid(row=3, column=0, columnspan=2, padx=16, pady=(10, 14), sticky="ew")

        self._status_label = ctk.CTkLabel(self, text="", text_color="tomato")
        self._status_label.grid(row=3, column=0, padx=24, pady=(8, 16))

    def refresh_profiles(self) -> None:
        profiles = self._service.list_profiles()
        self._profiles_by_name = {p.name: p for p in profiles}
        self._status_label.configure(text="")
        self._login_password_entry.delete(0, "end")

        if not profiles:
            self._profile_dropdown.configure(values=["(No profiles yet)"], state="disabled")
            self._profile_dropdown.set("(No profiles yet)")
            self._login_password_entry.configure(state="disabled")
            self._login_button.configure(state="disabled")
        else:
            names = list(self._profiles_by_name.keys())
            self._profile_dropdown.configure(values=names, state="normal")
            self._profile_dropdown.set(names[0])
            self._login_button.configure(state="normal")
            self._on_profile_selected(names[0])

    def _on_profile_selected(self, selected_name: str) -> None:
        profile = self._profiles_by_name.get(selected_name)
        self._login_password_entry.delete(0, "end")
        if profile and profile.has_password:
            self._login_password_entry.configure(
                state="normal",
                placeholder_text="Enter profile password",
            )
        else:
            self._login_password_entry.configure(
                state="disabled",
                placeholder_text="No password required",
            )

    def _handle_login(self) -> None:
        selected_name = self._profile_dropdown.get()
        password = self._login_password_entry.get() or None
        try:
            profile = self._service.login(selected_name, password=password)
            self._status_label.configure(text="")
            self._on_authenticated(profile)
        except ValueError as exc:
            self._status_label.configure(text=str(exc))

    def _handle_create(self) -> None:
        name = self._new_name_entry.get()
        password = self._new_password_entry.get() or None
        try:
            profile = self._service.create_profile(name, password=password)
            self._new_name_entry.delete(0, "end")
            self._new_password_entry.delete(0, "end")
            self._status_label.configure(text="")
            self._on_authenticated(profile)
        except ValueError as exc:
            self._status_label.configure(text=str(exc))
