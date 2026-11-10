
import csv
import random
from collections import defaultdict
from datetime import datetime, timedelta, timezone

from generator.config import DATA_DIR, CONFIG, RANDOM_SEED, END_DATE


ACCOUNT_TYPES = [
    "SAVINGS",
    "CURRENT",
    "SALARY",
]

ACCOUNT_STATUSES = [
    "ACTIVE",
    "DORMANT",
    "CLOSED",
]


def generate_accounts():
    rng = random.Random(RANDOM_SEED + 1)

    customers_file = DATA_DIR / "customers.csv"

    with open(customers_file, "r", encoding="utf-8") as file:
        customers = list(csv.DictReader(file))

    if not customers:
        raise ValueError("No customers found. Generate customers first.")

    # Give every customer at least one account.
    account_owners = customers.copy()

    # Distribute remaining accounts among existing customers.
    remaining = CONFIG.accounts - len(account_owners)

    if remaining < 0:
        raise ValueError(
            "Account count must be greater than or equal to customer count."
        )

    account_owners.extend(
        rng.choices(customers, k=remaining)
    )

    rng.shuffle(account_owners)

    # Track account sequence for each customer.
    customer_account_counts = defaultdict(int)

    accounts = []
    ownerships = []

    end_date = datetime.fromisoformat(END_DATE).replace(
        tzinfo=timezone.utc
    )

    for number, customer in enumerate(account_owners, start=1):

        customer_id = customer["customer_id"]

        customer_account_counts[customer_id] += 1
        sequence = customer_account_counts[customer_id]

        account_id = f"ACC-{customer_id}-{sequence:02d}"

        # Account opening date cannot be before customer creation.
        customer_created = datetime.fromisoformat(
            customer["created_at"]
        )

        available_seconds = max(
            0,
            int((end_date - customer_created).total_seconds())
        )

        opened_at = customer_created + timedelta(
            seconds=rng.randint(0, available_seconds)
        )

        account_type = rng.choice(ACCOUNT_TYPES)

        status = rng.choices(
            ACCOUNT_STATUSES,
            weights=[85, 10, 5],
            k=1
        )[0]

        opening_balance = round(
            rng.uniform(2_000, 150_000),
            2
        )

        overdraft_allowed = rng.random() < 0.05

        overdraft_limit = (
            round(rng.uniform(5_000, 25_000), 2)
            if overdraft_allowed
            else 0
        )

        accounts.append({
            "account_id": account_id,
            "account_type": account_type,
            "account_status": status,
            "opening_balance": opening_balance,
            "current_balance": opening_balance,
            "currency": "INR",
            "overdraft_allowed": overdraft_allowed,
            "overdraft_limit": overdraft_limit,
            "opened_at": opened_at.isoformat(),
        })

        ownerships.append({
            "ownership_id": f"OWN-{number:07d}",
            "account_id": account_id,
            "customer_id": customer_id,
            "ownership_percentage": 100.00,
            "ownership_type": "PRIMARY",
            "effective_from": opened_at.isoformat(),
            "effective_until": "",
        })

    return accounts, ownerships


def save_csv(records, filename):
    output_file = DATA_DIR / filename

    if not records:
        raise ValueError(f"No records to save in {filename}")

    with open(
        output_file,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=list(records[0].keys())
        )

        writer.writeheader()
        writer.writerows(records)

    print(f"{filename}: {len(records)} records saved")


if __name__ == "__main__":
    accounts, ownerships = generate_accounts()

    save_csv(accounts, "accounts.csv")
    save_csv(ownerships, "account_ownerships.csv")

    print("\nSample accounts:")

    for account in accounts[:5]:
        print(account)

    print("\nSample ownership records:")

    for ownership in ownerships[:5]:
        print(ownership)
