import json
import re
from pathlib import Path

import bcrypt

from spendwise.models import Profile
from spendwise.paths import get_profiles_dir
from spendwise.repositories.db import init_db

VALID_NAME_PATTERN = re.compile(r"^[A-Za-z0-9 _-]{1,50}$")
VALID_THEMES = {"system", "light", "dark"}


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    if not password_hash:
        return False
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


class ProfileService:
    def __init__(self, profiles_dir: Path | None = None) -> None:
        self._profiles_dir = profiles_dir if profiles_dir is not None else get_profiles_dir()
        self.current_profile: Profile | None = None

    @property
    def profiles_dir(self) -> Path:
        return self._profiles_dir

    def _validate_name(self, name: str) -> str:
        cleaned = name.strip()
        if not cleaned:
            raise ValueError("Profile name cannot be empty.")
        if not VALID_NAME_PATTERN.match(cleaned):
            raise ValueError("Profile name may only contain letters, numbers, spaces, '-' and '_'.")
        return cleaned

    def _profile_dir(self, name: str) -> Path:
        return self._profiles_dir / name

    def _profile_json_path(self, name: str) -> Path:
        return self._profile_dir(name) / "profile.json"

    def _ensure_profile_structure(self, name: str) -> Path:
        profile_dir = self._profile_dir(name)
        profile_dir.mkdir(parents=True, exist_ok=True)
        (profile_dir / "attachments").mkdir(exist_ok=True)
        (profile_dir / "models").mkdir(exist_ok=True)
        init_db(profile_dir / "data.db")
        return profile_dir

    def _save_profile_metadata(self, profile: Profile) -> None:
        data = {
            "name": profile.name,
            "password_hash": profile.password_hash,
            "theme": profile.theme,
        }
        self._profile_json_path(profile.name).write_text(
            json.dumps(data, indent=2), encoding="utf-8"
        )

    def _load_profile_metadata(self, json_path: Path) -> Profile:
        raw = json.loads(json_path.read_text(encoding="utf-8"))
        return Profile(
            name=raw["name"],
            password_hash=raw.get("password_hash"),
            theme=raw.get("theme", "system"),
        )

    def list_profiles(self) -> list[Profile]:
        if not self._profiles_dir.exists():
            return []

        profiles: list[Profile] = []
        for entry in sorted(self._profiles_dir.iterdir(), key=lambda p: p.name.lower()):
            json_path = entry / "profile.json"
            if entry.is_dir() and json_path.is_file():
                try:
                    profiles.append(self._load_profile_metadata(json_path))
                except (json.JSONDecodeError, KeyError, OSError):
                    continue
        return profiles

    def get_profile(self, name: str) -> Profile:
        cleaned = self._validate_name(name)
        json_path = self._profile_json_path(cleaned)
        if not json_path.is_file():
            raise ValueError(f"Profile '{cleaned}' does not exist.")
        return self._load_profile_metadata(json_path)

    def create_profile(
        self,
        name: str,
        password: str | None = None,
        theme: str = "system",
    ) -> Profile:
        cleaned_name = self._validate_name(name)
        if theme not in VALID_THEMES:
            raise ValueError(f"Invalid theme '{theme}'. Choose from {sorted(VALID_THEMES)}.")

        if self._profile_json_path(cleaned_name).exists():
            raise ValueError(f"Profile '{cleaned_name}' already exists.")

        pw_hash = hash_password(password) if password else None
        profile = Profile(name=cleaned_name, password_hash=pw_hash, theme=theme)

        self._ensure_profile_structure(cleaned_name)
        self._save_profile_metadata(profile)
        self.current_profile = profile
        return profile

    def login(self, name: str, password: str | None = None) -> Profile:
        profile = self.get_profile(name)

        if profile.has_password:
            if not password or not verify_password(password, profile.password_hash or ""):
                raise ValueError("Incorrect password.")

        self._ensure_profile_structure(profile.name)
        self.current_profile = profile
        return profile

    def switch_profile(self, name: str, password: str | None = None) -> Profile:
        return self.login(name, password=password)

    def logout(self) -> None:
        self.current_profile = None

    def update_theme(self, theme: str) -> Profile:
        if self.current_profile is None:
            raise ValueError("No active profile.")
        if theme not in VALID_THEMES:
            raise ValueError(f"Invalid theme '{theme}'. Choose from {sorted(VALID_THEMES)}.")

        updated = Profile(
            name=self.current_profile.name,
            password_hash=self.current_profile.password_hash,
            theme=theme,
        )
        self._save_profile_metadata(updated)
        self.current_profile = updated
        return updated

    def get_current_profile_dir(self) -> Path:
        if self.current_profile is None:
            raise ValueError("No active profile.")
        return self._profile_dir(self.current_profile.name)
