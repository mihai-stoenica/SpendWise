"""Application data directory helpers using platformdirs."""

from pathlib import Path

from platformdirs import user_data_dir

APP_NAME = "SpendWise"


def get_app_data_dir() -> Path:
    """Return the root application data directory."""
    return Path(user_data_dir(APP_NAME, appauthor=False))


def get_profiles_dir() -> Path:
    """Return the directory containing all user profiles."""
    return get_app_data_dir() / "profiles"


def get_profile_dir(profile_name: str) -> Path:
    """Return the directory for a specific profile."""
    return get_profiles_dir() / profile_name
