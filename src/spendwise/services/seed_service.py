import calendar
import random
from datetime import date

from faker import Faker

from spendwise.services.category_service import CategoryService
from spendwise.services.transaction_service import TransactionService

CATEGORY_TEMPLATES: dict[str, tuple[tuple[str, ...], int, int]] = {
    "Groceries": (
        ("Kaufland", "Lidl", "Carrefour", "Mega Image", "Auchan"),
        4500,
        32000,
    ),
    "Dining": (
        ("Starbucks", "Pizza Hut", "Burger King", "Local Bistro", "Glovo Order"),
        2500,
        16000,
    ),
    "Transport": (
        ("OMV Fuel", "Petrom", "Uber Trip", "Bolt Ride", "Metrorex Pass"),
        1800,
        24000,
    ),
    "Entertainment": (
        ("Netflix", "Spotify", "Cinema City", "Steam Store", "Bookstore"),
        3000,
        18000,
    ),
    "Health": (
        ("Catena Pharmacy", "HelpNet", "Regina Maria Clinic", "Dental Checkup"),
        2500,
        35000,
    ),
    "Shopping": (
        ("eMAG Order", "Zara", "IKEA", "Decathlon", "Altex"),
        6000,
        45000,
    ),
}


def _shift_months(anchor: date, delta_months: int) -> tuple[int, int]:
    total_months = (anchor.year * 12 + (anchor.month - 1)) + delta_months
    year = total_months // 12
    month = (total_months % 12) + 1
    return year, month


def seed_demo_transactions(
    transaction_service: TransactionService,
    category_service: CategoryService,
    months: int = 12,
    seed: int = 42,
    reference_date: date | None = None,
) -> int:
    rng = random.Random(seed)
    fake = Faker()
    Faker.seed(seed)

    anchor = reference_date or date.today()
    categories = {c.name: c.id for c in category_service.list_categories()}
    inserted = 0

    for offset in range(-(months - 1), 1):
        year, month = _shift_months(anchor, offset)
        days_in_month = calendar.monthrange(year, month)[1]

        salary_minor = rng.randint(580000, 650000)
        transaction_service.add_transaction(
            date=date(year, month, 1).isoformat(),
            amount=salary_minor,
            tx_type="income",
            category_id=categories.get("Salary"),
            note=f"Monthly Salary - {fake.company()}",
            amount_is_minor=True,
        )
        inserted += 1

        rent_day = min(5, days_in_month)
        transaction_service.add_transaction(
            date=date(year, month, rent_day).isoformat(),
            amount=180000,
            tx_type="expense",
            category_id=categories.get("Rent"),
            note="Monthly Apartment Rent",
            amount_is_minor=True,
        )
        inserted += 1

        util_day = min(10, days_in_month)
        util_minor = rng.randint(32000, 58000)
        transaction_service.add_transaction(
            date=date(year, month, util_day).isoformat(),
            amount=util_minor,
            tx_type="expense",
            category_id=categories.get("Utilities"),
            note="Enel & Digi Utilities",
            amount_is_minor=True,
        )
        inserted += 1

        num_variable = rng.randint(12, 18)
        cat_choices = list(CATEGORY_TEMPLATES.keys())
        cat_weights = [0.35, 0.22, 0.16, 0.10, 0.07, 0.10]

        for _ in range(num_variable):
            cat_name = rng.choices(cat_choices, weights=cat_weights, k=1)[0]
            merchants, min_amt, max_amt = CATEGORY_TEMPLATES[cat_name]
            merchant = rng.choice(merchants)
            day = rng.randint(1, days_in_month)
            amount_minor = rng.randint(min_amt, max_amt)
            receipt_no = rng.randint(100, 999)

            transaction_service.add_transaction(
                date=date(year, month, day).isoformat(),
                amount=amount_minor,
                tx_type="expense",
                category_id=categories.get(cat_name),
                note=f"{merchant} #{receipt_no}",
                amount_is_minor=True,
            )
            inserted += 1

    return inserted
