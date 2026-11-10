
import csv
from pathlib import Path
from collections import Counter
from generator.config import DATA_DIR


# Dataset filename and its primary key column
DATASETS = {
    "customers.csv": "customer_id",
    "accounts.csv": "account_id",
    "account_ownerships.csv": "ownership_id",
    "merchants.csv": "merchant_id",
    "devices.csv": "device_id",
    "transactions.csv": "transaction_id",
    "transfers.csv": "transfer_id",
    "ground_truth.csv": "issue_id",
    "account_events.csv": "event_id",
}


def validate_ids():

    total_records = 0
    total_errors = 0

    print("\nPRIMARY KEY VALIDATION")
    print("=" * 45)

    for filename, id_column in DATASETS.items():

        file_path = DATA_DIR / filename

        if not file_path.exists():
            print(f"SKIPPED: {filename} not found")
            continue

        with open(file_path, "r", encoding="utf-8") as file:
            records = list(csv.DictReader(file))

        ids = [
            record.get(id_column, "").strip()
            for record in records
        ]

        total_records += len(records)

        missing_ids = [
            index + 2
            for index, value in enumerate(ids)
            if not value
        ]
        from collections import Counter

        id_counts = Counter(value for value in ids if value)

    duplicate_ids = sorted(
        value
        for value, count in id_counts.items()
        if count > 1
    )
    errors = len(missing_ids) + len(duplicate_ids)
    total_errors += errors

    if errors == 0:
        print(
            f"PASS: {filename} "
            f"({len(records)} unique records)"
        )
    else:
        print(f"FAIL: {filename}")

        if missing_ids:
            print(f"  Missing IDs on CSV rows: {missing_ids[:10]}")

        if duplicate_ids:
            print(f"  Duplicate IDs: {duplicate_ids[:10]}")

    print("\n" + "=" * 45)
    print(f"Total records checked: {total_records}")
    print(f"Total errors: {total_errors}")

    if total_errors == 0:
        print("RESULT: ALL PRIMARY KEYS ARE VALID")
    else:
        print("RESULT: VALIDATION FAILED")

    return total_errors == 0


if __name__ == "__main__":
    validate_ids()
