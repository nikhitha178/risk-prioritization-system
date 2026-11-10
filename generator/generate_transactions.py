
import csv
import random
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from generator.config import (
    CONFIG,
    DATA_DIR,
    RANDOM_SEED,
    END_DATE,
)


def read_csv(filename):
    with open(DATA_DIR / filename, "r", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def write_csv(filename, records):
    if not records:
        raise ValueError(f"No records to write: {filename}")

    with open(
        DATA_DIR / filename,
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


def random_timestamp(rng, start, end):
    """Generate a timestamp between two dates."""

    seconds = int((end - start).total_seconds())

    if seconds <= 0:
        return start

    return start + timedelta(
        seconds=rng.randint(0, seconds)
    )


def generate_transactions():

    rng = random.Random(RANDOM_SEED + 4)

    accounts = read_csv("accounts.csv")
    customers = read_csv("customers.csv")
    devices = read_csv("devices.csv")
    merchants = read_csv("merchants.csv")
    ownerships = read_csv("account_ownerships.csv")

    if not accounts or not devices or not merchants:
        raise ValueError("Master datasets are incomplete.")

    customer_map = {
        customer["customer_id"]: customer
        for customer in customers
    }

    # Map accounts to their owners using the ownership bridge.
    account_owner_map = {
        ownership["account_id"]: ownership["customer_id"]
        for ownership in ownerships
    }

    # Map customers to their registered devices.
    customer_devices = defaultdict(list)

    for device in devices:
        customer_devices[device["customer_id"]].append(device)

    # Only active accounts receive normal transactions.
    active_accounts = [
        account for account in accounts
        if account["account_status"] == "ACTIVE"
    ]

    if not active_accounts:
        raise ValueError("No active accounts available.")

    end_date = datetime.fromisoformat(END_DATE).replace(
        tzinfo=timezone.utc
    )

    # Assign transactions according to each account's exposure period.
    # Older accounts have more available time to generate transactions.
    account_weights = []

    for account in active_accounts:
        opened_at = datetime.fromisoformat(account["opened_at"])

        if opened_at > end_date:
            raise ValueError(
                f"Account {account['account_id']} opened after dataset end date."
            )

        exposure_seconds = max(
            1,
            int((end_date - opened_at).total_seconds())
        )

        account_weights.append(exposure_seconds)

    if len(account_weights) != len(active_accounts):
        raise ValueError("Account weights do not match active accounts.")

    selected_accounts = rng.choices(
        active_accounts,
        weights=account_weights,
        k=CONFIG.transactions
    )

    account_events = defaultdict(list)

    for account in selected_accounts:

        account_id = account["account_id"]

        opened_at = datetime.fromisoformat(
            account["opened_at"]
        )

        if opened_at > end_date:
            raise ValueError(
                f"Account {account_id} opened after dataset end date."
            )

        timestamp = random_timestamp(
            rng,
            opened_at,
            end_date
        )

        account_events[account_id].append(timestamp)

    transactions = []
 # Track balances using Decimal for accurate currency arithmetic.
    account_balances = {
        account["account_id"]: Decimal(
            account["opening_balance"]
        )
        for account in accounts
    }

    account_lookup = {
        account["account_id"]: account
        for account in accounts
    }

    for account_id, timestamps in account_events.items():

        account = account_lookup[account_id]

        customer_id = account_owner_map[account_id]

        owner = customer_map[customer_id]

        available_devices = customer_devices[customer_id]

        # Process each account's transactions chronologically.
        timestamps.sort()

        for timestamp in timestamps:

            balance_before = account_balances[account_id]

            amount = Decimal(
                rng.randint(100, 100_000)
            )

            transaction_type = rng.choice([
                "DEBIT",
                "CREDIT"
            ])

            transaction_status = rng.choices(
                ["SUCCESS", "FAILED", "PENDING"],
                weights=[94, 4, 2],
                k=1
            )[0]

            # Do not allow an ordinary debit to exceed the balance.
            if (
                transaction_type == "DEBIT"
                and balance_before < Decimal("100")
            ):
                transaction_type = "CREDIT"

            if transaction_type == "DEBIT":
                amount = min(amount, balance_before)

            balance_after = balance_before

            # Only successful transactions change the balance.
            if transaction_status == "SUCCESS":

                if transaction_type == "DEBIT":
                    balance_after -= amount

                else:
                    balance_after += amount

                account_balances[account_id] = balance_after

            # Select a device registered before this transaction.
            eligible_devices = [
                device for device in available_devices
                if datetime.fromisoformat(
                    device["registered_at"]
                ) <= timestamp
            ]

            selected_device = (
                rng.choice(eligible_devices)
                if eligible_devices
                else None
            )

            merchant = rng.choice(merchants)

            transactions.append({
                "account_id": account_id,
                "merchant_id": merchant["merchant_id"],
                "device_id": (
                    selected_device["device_id"]
                    if selected_device else ""
                ),
                "transaction_type": transaction_type,
                "amount": f"{amount:.2f}",
                "currency": "INR",
                "transaction_status": transaction_status,
                "transaction_timestamp": timestamp.isoformat(),
                "balance_before": f"{balance_before:.2f}",
                "balance_after": f"{balance_after:.2f}",
                "description": (
                    f"{transaction_type} at "
                    f"{merchant['merchant_name']}"
                ),
            })

    # Sort all transactions chronologically for deterministic IDs.
    transactions.sort(
        key=lambda item: (
            item["transaction_timestamp"],
            item["account_id"]
        )
    )

    for number, transaction in enumerate(transactions, start=1):
        transaction["transaction_id"] = (
            f"TXN-2026-{number:08d}"
        )

    # Keep transaction CSV columns in the model's expected order.
    fieldnames = [
        "transaction_id",
        "account_id",
        "merchant_id",
        "device_id",
        "transaction_type",
        "amount",
        "currency",
        "transaction_status",
        "transaction_timestamp",
        "balance_before",
        "balance_after",
        "description",
    ]

    transactions = [
        {field: transaction[field] for field in fieldnames}
        for transaction in transactions
    ]

    # Update account balances after successful transactions.
    for account in accounts:
        account["current_balance"] = (
            f"{account_balances[account['account_id']]:.2f}"
        )

    write_csv("transactions.csv", transactions)
    write_csv("accounts.csv", accounts)

    print("\nTransaction generation completed!")
    print("----------------------------------")
    print(f"Total transactions: {len(transactions)}")
    print(f"Active accounts used: {len(account_events)}")
    print(f"Updated account balances: {len(accounts)}")

    print("\nSample transactions:")

    for transaction in transactions[:5]:
        print(transaction)

    print("\nTransaction status summary:")

    for status in ["SUCCESS", "FAILED", "PENDING"]:
        count = sum(
            1 for transaction in transactions
            if transaction["transaction_status"] == status
        )
        print(f"{status}: {count}")


if __name__ == "__main__":
    generate_transactions()
