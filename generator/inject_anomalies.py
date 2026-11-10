
import csv
import random
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

from generator.config import DATA_DIR, RANDOM_SEED


def read_csv(filename):
    path = DATA_DIR / filename

    if not path.exists():
        return []

    with open(path, "r", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def write_csv(filename, records, fieldnames=None):
    path = DATA_DIR / filename

    if not records:
        return

    if fieldnames is None:
        fieldnames = list(records[0].keys())

    with open(
        path,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)


def inject_anomalies():

    rng = random.Random(RANDOM_SEED + 6)

    accounts = read_csv("accounts.csv")
    customers = read_csv("customers.csv")
    ownerships = read_csv("account_ownerships.csv")
    transactions = read_csv("transactions.csv")
    devices = read_csv("devices.csv")
    transfers = read_csv("transfers.csv")
    merchants = read_csv("merchants.csv")
    account_events = read_csv("account_events.csv")

    if not accounts or not transactions:
        raise ValueError("Generate accounts and transactions first.")

    # Prevent accidental duplicate injection on reruns.
    if any(
        txn.get("description", "").startswith("ANOMALY:")
        for txn in transactions
    ):
        raise ValueError(
            "Anomalies already exist. Do not run this generator twice "
            "without restoring the original generated datasets."
        )

    ownership_map = {
        item["account_id"]: item["customer_id"]
        for item in ownerships
    }

    customer_map = {
        item["customer_id"]: item
        for item in customers
    }

    account_map = {
        item["account_id"]: item
        for item in accounts
    }

    balances = {
        account["account_id"]: Decimal(account["opening_balance"])
        for account in accounts
    }

    # Reconstruct balances from the complete existing ledger.
    transactions.sort(
        key=lambda item: (
            item["transaction_timestamp"],
            item["transaction_id"]
        )
    )

    for txn in transactions:
        account_id = txn["account_id"]
        amount = Decimal(txn["amount"])

        before = balances[account_id]
        after = before

        if txn["transaction_status"] == "SUCCESS":
            if txn["transaction_type"] == "DEBIT":
                if amount > before:
                    raise ValueError(
                        f"Invalid existing debit: {txn['transaction_id']}"
                    )
                after -= amount
            else:
                after += amount

        txn["balance_before"] = f"{before:.2f}"
        txn["balance_after"] = f"{after:.2f}"

        balances[account_id] = after

    # Use timestamps after the existing baseline transaction history.
    latest_timestamp = max(
        datetime.fromisoformat(txn["transaction_timestamp"])
        for txn in transactions
    )

    next_timestamp = latest_timestamp + timedelta(minutes=1)

    highest_txn_id = max(
        int(txn["transaction_id"].split("-")[-1])
        for txn in transactions
    )

    new_transactions = []
    ground_truth = []

    def add_transaction(
        account_id,
        amount,
        transaction_type,
        timestamp,
        description,
        device_id="",
        merchant_id="",
    ):
        nonlocal highest_txn_id

        amount = Decimal(str(amount))
        before = balances[account_id]

        if transaction_type == "DEBIT":
            if amount > before:
                raise ValueError(
                    f"Insufficient balance in {account_id}"
                )
            after = before - amount
        else:
            after = before + amount

        highest_txn_id += 1
        transaction_id = f"TXN-2026-{highest_txn_id:08d}"

        new_transactions.append({
            "transaction_id": transaction_id,
            "account_id": account_id,
            "merchant_id": merchant_id,
            "device_id": device_id,
            "transaction_type": transaction_type,
            "amount": f"{amount:.2f}",
            "currency": "INR",
            "transaction_status": "SUCCESS",
            "transaction_timestamp": timestamp.isoformat(),
            "balance_before": f"{before:.2f}",
            "balance_after": f"{after:.2f}",
            "description": description,
        })

        balances[account_id] = after

        return transaction_id

    def record_ground_truth(
        issue_type,
        transaction_id,
        account_id,
        severity,
        description,
        transfer_id=""
    ):
        ground_truth.append({
            "issue_id": f"ISS-{len(ground_truth) + 1:06d}",
            "issue_type": issue_type,
            "transaction_id": transaction_id,
            "account_id": account_id,
            "transfer_id": transfer_id,
            "severity": severity,
            "description": description,
        })

    active_accounts = [
        account for account in accounts
        if account["account_status"] == "ACTIVE"
    ]

    if len(active_accounts) < 6:
        raise ValueError("Not enough active accounts for anomaly scenarios.")

    # -------------------------------------------------
    # 1. HIGH-VALUE TRANSACTIONS
    # -------------------------------------------------

    for index, account in enumerate(active_accounts[:3]):

        timestamp = next_timestamp + timedelta(minutes=index)

        txn_id = add_transaction(
            account["account_id"],
            250000,
            "CREDIT",
            timestamp,
            "ANOMALY: HIGH VALUE",
            merchant_id=merchants[0]["merchant_id"],
        )

        record_ground_truth(
            "HIGH_VALUE",
            txn_id,
            account["account_id"],
            "HIGH",
            "Synthetic unusually large credit transaction."
        )

    # -------------------------------------------------
    # 2. TRANSACTION VELOCITY SPIKE
    # -------------------------------------------------

    velocity_account = active_accounts[3]

    for index in range(5):

        timestamp = next_timestamp + timedelta(
            minutes=10 + index
        )

        txn_id = add_transaction(
            velocity_account["account_id"],
            2000,
            "CREDIT",
            timestamp,
            "ANOMALY: VELOCITY SPIKE",
            merchant_id=merchants[1]["merchant_id"],
        )

        record_ground_truth(
            "VELOCITY_SPIKE",
            txn_id,
            velocity_account["account_id"],
            "MEDIUM",
            "One of five transactions made within five minutes."
        )

    # -------------------------------------------------
    # 3. NEW DEVICE ACTIVITY
    # -------------------------------------------------

    new_device_account = active_accounts[4]
    customer_id = ownership_map[new_device_account["account_id"]]

    new_device_id = f"DEV-ANOMALY-{len(devices) + 1:05d}"
    device_timestamp = next_timestamp + timedelta(minutes=20)

    devices.append({
        "device_id": new_device_id,
        "customer_id": customer_id,
        "device_type": "MOBILE",
        "operating_system": "Android",
        "browser": "Chrome",
        "ip_address": "192.0.2.250",
        "registered_at": device_timestamp.isoformat(),
        "is_trusted": False,
        "is_active": True,
    })

    txn_id = add_transaction(
        new_device_account["account_id"],
        7500,
        "CREDIT",
        device_timestamp + timedelta(seconds=30),
        "ANOMALY: NEW DEVICE",
        device_id=new_device_id,
        merchant_id=merchants[2]["merchant_id"],
    )

    record_ground_truth(
        "NEW_DEVICE",
        txn_id,
        new_device_account["account_id"],
        "MEDIUM",
        "Transaction performed using a newly registered untrusted device."
    )

    # -------------------------------------------------
    # 4. CIRCULAR TRANSFERS
    # -------------------------------------------------

    cycle_accounts = active_accounts[5:8]

    if len(cycle_accounts) < 3:
        raise ValueError("Three separate accounts are required.")

    cycle_amount = Decimal("500")

    for account in cycle_accounts:
        if balances[account["account_id"]] < cycle_amount:
            raise ValueError(
                f"Insufficient balance for circular transfer: "
                f"{account['account_id']}"
            )

    cycle_pairs = [
        (cycle_accounts[0], cycle_accounts[1]),
        (cycle_accounts[1], cycle_accounts[2]),
        (cycle_accounts[2], cycle_accounts[0]),
    ]

    for index, (source, destination) in enumerate(cycle_pairs):

        timestamp = next_timestamp + timedelta(minutes=30 + index)

        transfer_id = f"TRF-ANOMALY-{index + 1:04d}"

        source_txn = add_transaction(
            source["account_id"],
            cycle_amount,
            "DEBIT",
            timestamp,
            f"ANOMALY: CIRCULAR TRANSFER {transfer_id} SOURCE",
        )

        destination_txn = add_transaction(
            destination["account_id"],
            cycle_amount,
            "CREDIT",
            timestamp,
            f"ANOMALY: CIRCULAR TRANSFER {transfer_id} DESTINATION",
        )

        transfers.append({
            "transfer_id": transfer_id,
            "source_transaction_id": source_txn,
            "destination_transaction_id": destination_txn,
            "source_account_id": source["account_id"],
            "destination_account_id": destination["account_id"],
            "amount": f"{cycle_amount:.2f}",
            "transfer_timestamp": timestamp.isoformat(),
        })

        record_ground_truth(
            "CIRCULAR_TRANSFER",
            source_txn,
            source["account_id"],
            "HIGH",
            "Source debit in a three-account circular transfer.",
            transfer_id,
        )

        record_ground_truth(
            "CIRCULAR_TRANSFER",
            destination_txn,
            destination["account_id"],
            "HIGH",
            "Destination credit in a three-account circular transfer.",
            transfer_id,
        )

    # -------------------------------------------------
    # 5. DORMANT ACCOUNT REACTIVATION
    # -------------------------------------------------

    dormant_accounts = [
        account for account in accounts
        if account["account_status"] == "DORMANT"
    ]

    if dormant_accounts:

        dormant_account = dormant_accounts[0]
        dormant_account_id = dormant_account["account_id"]

        reactivation_time = next_timestamp + timedelta(minutes=40)

        account_events.append({
            "event_id": "EVT-REACT-000001",
            "account_id": dormant_account_id,
            "event_type": "REACTIVATION",
            "previous_status": "DORMANT",
            "new_status": "ACTIVE",
            "description": "Synthetic dormant account reactivation.",
            "event_timestamp": reactivation_time.isoformat(),
        })

        dormant_account["account_status"] = "ACTIVE"

        txn_id = add_transaction(
            dormant_account_id,
            5000,
            "CREDIT",
            reactivation_time + timedelta(seconds=30),
            "ANOMALY: DORMANT REACTIVATION",
            merchant_id=merchants[0]["merchant_id"],
        )

        record_ground_truth(
            "DORMANT_REACTIVATION",
            txn_id,
            dormant_account_id,
            "HIGH",
            "Transaction shortly after a dormant account was reactivated."
        )

    # -------------------------------------------------
    # SAVE ALL DATASETS
    # -------------------------------------------------

    transactions.extend(new_transactions)

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

    write_csv("transactions.csv", transactions, transaction_fields)
    write_csv("accounts.csv", accounts)
    write_csv("devices.csv", devices)
    write_csv("transfers.csv", transfers)
    write_csv("account_events.csv", account_events)
    write_csv("ground_truth.csv", ground_truth)

    print("\nAnomaly injection completed!")
    print("--------------------------------")

    print(f"New transactions: {len(new_transactions)}")
    print(f"Ground-truth records: {len(ground_truth)}")
    print(f"Total transactions: {len(transactions)}")
    print(f"Total transfers: {len(transfers)}")

    print("\nGround-truth summary:")

    issue_counts = {}

    for item in ground_truth:
        issue_counts[item["issue_type"]] = (
            issue_counts.get(item["issue_type"], 0) + 1
        )

    for issue_type, count in issue_counts.items():
        print(f"{issue_type}: {count}")


if __name__ == "__main__":
    inject_anomalies()
