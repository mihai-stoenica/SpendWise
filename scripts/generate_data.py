import argparse
from pathlib import Path

from spendwise.paths import get_profile_db_path
from spendwise.repositories.category_repo import CategoryRepository
from spendwise.repositories.transaction_repo import TransactionRepository
from spendwise.services.category_service import CategoryService
from spendwise.services.profile_service import ProfileService
from spendwise.services.seed_service import seed_demo_transactions
from spendwise.services.transaction_service import TransactionService


def seed_profile(
    profile_name: str,
    password: str | None = None,
    months: int = 12,
    seed: int = 42,
    profiles_dir: Path | None = None,
) -> int:
    profile_service = ProfileService(profiles_dir=profiles_dir)
    existing_names = {p.name for p in profile_service.list_profiles()}

    if profile_name in existing_names:
        profile = profile_service.login(profile_name, password=password)
    else:
        profile = profile_service.create_profile(profile_name, password=password)

    base_dir = profile_service.profiles_dir.parent
    db_path = get_profile_db_path(profile.name, base_dir=base_dir)
    cat_repo = CategoryRepository(db_path)
    cat_service = CategoryService(cat_repo)
    tx_service = TransactionService(TransactionRepository(db_path), category_repo=cat_repo)

    return seed_demo_transactions(
        transaction_service=tx_service,
        category_service=cat_service,
        months=months,
        seed=seed,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", default="Demo", help="Profile name to seed")
    parser.add_argument("--password", default=None, help="Optional profile password")
    parser.add_argument("--months", type=int, default=12, help="Number of months to generate")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()

    count = seed_profile(
        profile_name=args.profile,
        password=args.password,
        months=args.months,
        seed=args.seed,
    )
    print(f"Seeded {count} transactions into profile '{args.profile}'.")


if __name__ == "__main__":
    main()
