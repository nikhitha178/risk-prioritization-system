
import csv
import random
from datetime import datetime
from decimal import Decimal

from generator.config import DATA_DIR, RANDOM_SEED


TRANSFER_COUNT = 100


def read_csv(filename):
    with open(DATA_DIR / filename, encoding="utf-8") as file:
        return list(csv.DictReader(file))


def write_csv(filename, records, fieldnames=None):
    if not records:
        raise ValueError(f"No records to save: {filename}")

    if fieldnames is None:
        fieldnames = list(records[0].keys())

    with open(
        DATA_DIR / filename,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)


def generate_transfers():
    rng = random.Random(RANDOM_SEED + 5)

    accounts = read_csv("accounts.csv")
    transactions = read_csv("transactions.csv")

    # Remove transfer transactions from an earlier run, if any.
    transactions = [
        txn for txn in transactions
        if not txn["description"].startswith("TRANSFER:")
    ]

    account_lookup = {
        account["account_id"]: account
        for account in accounts
    }

    # Recalculate balances from the original transaction history.
    balances = {
        account["account_id"]: Decimal(account["opening_balance"])
        for account in accounts
    }

    transactions.sort(
        key=lambda txn: (
            txn["transaction_timestamp"],
            txn["transaction_id"]
        )
    )

    for txn in transactions:
        account_id = txn["account_id"]

        if account_id not in balances:
            raise ValueError(f"Unknown account: {account_id}")

        before = balances[account_id]
        amount = Decimal(txn["amount"])
        after = before

        if txn["transaction_status"] == "SUCCESS":
            if txn["transaction_type"] == "DEBIT":
                if amount > before:
                    raise ValueError(
                        f"Insufficient balance for {txn['transaction_id']}"
                    )
                after -= amount

            elif txn["transaction_type"] == "CREDIT":
                after += amount

        txn["balance_before"] = f"{before:.2f}"
        txn["balance_after"] = f"{after:.2f}"

        balances[account_id] = after

    # Choose source accounts that have enough money.
    active_accounts = [
        account for account in accounts
        if account["account_status"] == "ACTIVE"
    ]

    source_candidates = [
        account for account in active_accounts
        if balances[account["account_id"]] >= Decimal("100")
    ]

    rng.shuffle(source_candidates)

    source_accounts = source_candidates[:TRANSFER_COUNT]

    if len(source_accounts) < TRANSFER_COUNT:
        raise ValueError("Not enough funded source accounts.")

    source_ids = {
        account["account_id"] for account in source_accounts
    }

    destination_candidates = [
        account for account in active_accounts
        if account["account_id"] not in source_ids
    ]

    rng.shuffle(destination_candidates)

    destination_accounts = destination_candidates[:TRANSFER_COUNT]

    if len(destination_accounts) < TRANSFER_COUNT:
        raise ValueError("Not enough separate destination accounts.")

    # Use the latest existing transaction timestamp.
    latest_timestamp = max(
        datetime.fromisoformat(txn["transaction_timestamp"])
        for txn in transactions
    )

    transfer_timestamp = latest_timestamp.isoformat()

    # Continue transaction numbering without duplicates.
    highest_id = max(
        int(txn["transaction_id"].split("-")[-1])
        for txn in transactions
    )

    new_transactions = []
    transfers = []

    for index in range(TRANSFER_COUNT):

        source = source_accounts[index]
        destination = destination_accounts[index]

        source_id = source["account_id"]
        destination_id = destination["account_id"]

        source_balance = balances[source_id]
        destination_balance = balances[destination_id]

        maximum_amount = min(1000, int(source_balance))
        amount = Decimal(
            rng.randint(100, maximum_amount)
        )

        source_transaction_id = (
            f"TXN-2026-{highest_id + 1:08d}"
        )

        destination_transaction_id = (
            f"TXN-2026-{highest_id + 2:08d}"
        )

        highest_id += 2

        # Source debit leg.
        new_transactions.append({
            "transaction_id": source_transaction_id,
            "account_id": source_id,
            "merchant_id": "",
            "device_id": "",
            "transaction_type": "DEBIT",
            "amount": f"{amount:.2f}",
            "currency": "INR",
            "transaction_status": "SUCCESS",
            "transaction_timestamp": transfer_timestamp,
            "balance_before": f"{source_balance:.2f}",
            "balance_after": f"{source_balance - amount:.2f}",
            "description": f"TRANSFER: {index + 1:06d} SOURCE",
        })

        # Destination credit leg.
        new_transactions.append({
            "transaction_id": destination_transaction_id,
            "account_id": destination_id,
            "merchant_id": "",
            "device_id": "",
            "transaction_type": "CREDIT",
            "amount": f"{amount:.2f}",
            "currency": "INR",
            "transaction_status": "SUCCESS",
            "transaction_timestamp": transfer_timestamp,
            "balance_before": f"{destination_balance:.2f}",
            "balance_after": f"{destination_balance + amount:.2f}",
            "description": f"TRANSFER: {index + 1:06d} DESTINATION",
        })

        balances[source_id] -= amount
        balances[destination_id] += amount

        transfers.append({
            "transfer_id": f"TRF-2026-{index + 1:06d}",
            "source_transaction_id": source_transaction_id,
            "destination_transaction_id": destination_transaction_id,
            "source_account_id": source_id,
            "destination_account_id": destination_id,
            "amount": f"{amount:.2f}",
            "transfer_timestamp": transfer_timestamp,
        })

    transactions.extend(new_transactions)

    # Update account balances.
    for account in accounts:
        account["current_balance"] = (
            f"{balances[account['account_id']]:.2f}"
        )

    transaction_fields = [
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

    write_csv(
        "transactions.csv",
        transactions,
        transaction_fields
    )

    write_csv("accounts.csv", accounts)

    write_csv(
        "transfers.csv",
        transfers,
        [
            "transfer_id",
            "source_transaction_id",
            "destination_transaction_id",
            "source_account_id",
            "destination_account_id",
            "amount",
            "transfer_timestamp",
        ]
    )

    print("\nTransfer generation successful!")
    print(f"Transfers created: {len(transfers)}")
    print(f"New transaction legs: {len(new_transactions)}")
    print(f"Total transactions: {len(transactions)}")

    print("\nSample transfer:")
    print(transfers[0])


if __name__ == "__main__":
    generate_transfers()
