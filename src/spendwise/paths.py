from pathlib import Path

from platformdirs import user_data_dir

APP_NAME = "SpendWise"


def get_app_data_dir() -> Path:
    return Path(user_data_dir(APP_NAME, appauthor=False))


def get_profiles_dir(base_dir: Path | None = None) -> Path:
    root = base_dir if base_dir is not None else get_app_data_dir()
    return root / "profiles"


def get_profile_dir(profile_name: str, base_dir: Path | None = None) -> Path:
    return get_profiles_dir(base_dir) / profile_name


def get_profile_db_path(profile_name: str, base_dir: Path | None = None) -> Path:
    return get_profile_dir(profile_name, base_dir) / "data.db"


def get_profile_attachments_dir(profile_name: str, base_dir: Path | None = None) -> Path:
    return get_profile_dir(profile_name, base_dir) / "attachments"


def get_profile_models_dir(profile_name: str, base_dir: Path | None = None) -> Path:
    return get_profile_dir(profile_name, base_dir) / "models"


def get_profile_json_path(profile_name: str, base_dir: Path | None = None) -> Path:
    return get_profile_dir(profile_name, base_dir) / "profile.json"
