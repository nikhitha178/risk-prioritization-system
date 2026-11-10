
import csv
from decimal import Decimal

from generator.config import DATA_DIR


def read_csv(filename):
    with open(DATA_DIR / filename, encoding="utf-8") as file:
        return list(csv.DictReader(file))


def validate_transfers():
    transfers = read_csv("transfers.csv")
    transactions = read_csv("transactions.csv")

    transaction_lookup = {
        row["transaction_id"]: row
        for row in transactions
    }

    errors = []

    print("\nTRANSFER VALIDATION")
    print("=" * 55)

    for transfer in transfers:
        transfer_id = transfer["transfer_id"]

        source = transaction_lookup.get(
            transfer["source_transaction_id"]
        )
        destination = transaction_lookup.get(
            transfer["destination_transaction_id"]
        )

        if source is None or destination is None:
            errors.append(
                f"{transfer_id}: Missing transaction leg"
            )
            continue

        if source["transaction_type"] != "DEBIT":
            errors.append(
                f"{transfer_id}: Source transaction is not a DEBIT"
            )

        if destination["transaction_type"] != "CREDIT":
            errors.append(
                f"{transfer_id}: Destination transaction is not a CREDIT"
            )

        if source["account_id"] != transfer["source_account_id"]:
            errors.append(
                f"{transfer_id}: Source account mismatch"
            )

        if destination["account_id"] != transfer["destination_account_id"]:
            errors.append(
                f"{transfer_id}: Destination account mismatch"
            )

        if Decimal(source["amount"]) != Decimal(destination["amount"]):
            errors.append(
                f"{transfer_id}: Source and destination amounts differ"
            )

        if Decimal(source["amount"]) != Decimal(transfer["amount"]):
            errors.append(
                f"{transfer_id}: Transfer amount does not match transaction amount"
            )

        if source["transaction_status"] != "SUCCESS":
            errors.append(
                f"{transfer_id}: Source transaction is not successful"
            )

        if destination["transaction_status"] != "SUCCESS":
            errors.append(
                f"{transfer_id}: Destination transaction is not successful"
            )

        if source["transaction_timestamp"] != destination["transaction_timestamp"]:
            errors.append(
                f"{transfer_id}: Transaction timestamps do not match"
            )

    print(f"Transfers checked: {len(transfers)}")

    if errors:
        print(f"\nFAIL: {len(errors)} transfer errors found")

        for error in errors[:20]:
            print("FAIL:", error)

        print("\nRESULT: TRANSFER VALIDATION FAILED")
        return False

    print("PASS: Source debit transactions")
    print("PASS: Destination credit transactions")
    print("PASS: Account references")
    print("PASS: Transfer amount reconciliation")
    print("PASS: Transaction statuses")
    print("PASS: Transaction timestamps")
    print("\nRESULT: ALL TRANSFER CHECKS PASSED")

    return True


if __name__ == "__main__":
    validate_transfers()
