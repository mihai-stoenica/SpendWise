import json
from pathlib import Path

import pytest

from spendwise.services.profile_service import (
    ProfileService,
    hash_password,
    verify_password,
)


def test_password_hashing_and_verification() -> None:
    hashed = hash_password("secret123")
    assert hashed != "secret123"
    assert hashed.startswith("$2")
    assert verify_password("secret123", hashed) is True
    assert verify_password("wrong", hashed) is False
    assert verify_password("secret123", "") is False


def test_list_profiles_empty_state(tmp_path: Path) -> None:
    service = ProfileService(profiles_dir=tmp_path / "profiles")
    assert service.list_profiles() == []
    assert service.current_profile is None


def test_create_profile_without_password_creates_structure(tmp_path: Path) -> None:
    profiles_dir = tmp_path / "profiles"
    service = ProfileService(profiles_dir=profiles_dir)

    profile = service.create_profile("Personal")

    assert profile.name == "Personal"
    assert profile.password_hash is None
    assert profile.has_password is False
    assert profile.theme == "system"
    assert service.current_profile == profile

    profile_dir = profiles_dir / "Personal"
    assert (profile_dir / "data.db").is_file()
    assert (profile_dir / "attachments").is_dir()
    assert (profile_dir / "models").is_dir()
    assert (profile_dir / "profile.json").is_file()


def test_create_profile_with_password_stores_bcrypt_hash(tmp_path: Path) -> None:
    profiles_dir = tmp_path / "profiles"
    service = ProfileService(profiles_dir=profiles_dir)

    profile = service.create_profile("Work", password="my_password", theme="dark")

    assert profile.has_password is True
    assert profile.password_hash is not None
    assert profile.password_hash != "my_password"
    assert profile.theme == "dark"

    raw_json = json.loads((profiles_dir / "Work" / "profile.json").read_text(encoding="utf-8"))
    assert raw_json["password_hash"] != "my_password"
    assert verify_password("my_password", raw_json["password_hash"]) is True


def test_create_duplicate_or_invalid_profile_raises(tmp_path: Path) -> None:
    service = ProfileService(profiles_dir=tmp_path / "profiles")
    service.create_profile("Alice")

    with pytest.raises(ValueError, match="already exists"):
        service.create_profile("Alice")

    with pytest.raises(ValueError, match="cannot be empty"):
        service.create_profile("   ")

    with pytest.raises(ValueError, match="may only contain"):
        service.create_profile("../bad_name")

    with pytest.raises(ValueError, match="Invalid theme"):
        service.create_profile("Bob", theme="neon")


def test_login_and_switch_profiles(tmp_path: Path) -> None:
    service = ProfileService(profiles_dir=tmp_path / "profiles")
    service.create_profile("Protected", password="correct-password")
    service.create_profile("NoPass")
    service.logout()
    assert service.current_profile is None
    assert [p.name for p in service.list_profiles()] == ["NoPass", "Protected"]

    logged_in = service.login("NoPass")
    assert logged_in.name == "NoPass"
    assert service.current_profile == logged_in

    with pytest.raises(ValueError, match="Incorrect password"):
        service.switch_profile("Protected")

    with pytest.raises(ValueError, match="Incorrect password"):
        service.switch_profile("Protected", password="wrong-password")

    switched = service.switch_profile("Protected", password="correct-password")
    assert switched.name == "Protected"
    assert service.current_profile == switched

    with pytest.raises(ValueError, match="does not exist"):
        service.login("Ghost")


def test_update_theme_and_current_profile_dir(tmp_path: Path) -> None:
    profiles_dir = tmp_path / "profiles"
    service = ProfileService(profiles_dir=profiles_dir)

    with pytest.raises(ValueError, match="No active profile"):
        service.update_theme("dark")

    with pytest.raises(ValueError, match="No active profile"):
        service.get_current_profile_dir()

    service.create_profile("Personal")
    updated = service.update_theme("dark")
    assert updated.theme == "dark"
    assert service.get_current_profile_dir() == profiles_dir / "Personal"

    with pytest.raises(ValueError, match="Invalid theme"):
        service.update_theme("invalid")

    reloaded = service.get_profile("Personal")
    assert reloaded.theme == "dark"
