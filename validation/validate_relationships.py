
import csv

from generator.config import DATA_DIR


def read_csv(filename):
    with open(DATA_DIR / filename, encoding="utf-8") as file:
        return list(csv.DictReader(file))


def validate_relationships():

    customers = read_csv("customers.csv")
    accounts = read_csv("accounts.csv")
    ownerships = read_csv("account_ownerships.csv")
    merchants = read_csv("merchants.csv")
    devices = read_csv("devices.csv")
    transactions = read_csv("transactions.csv")
    transfers = read_csv("transfers.csv")
    ground_truth = read_csv("ground_truth.csv")
    account_events = read_csv("account_events.csv")

    customer_ids = {x["customer_id"] for x in customers}
    account_ids = {x["account_id"] for x in accounts}
    merchant_ids = {x["merchant_id"] for x in merchants}
    device_ids = {x["device_id"] for x in devices}
    transaction_ids = {x["transaction_id"] for x in transactions}
    transfer_ids = {x["transfer_id"] for x in transfers}

    errors = []

    # Account ownership relationships
    for row in ownerships:
        if row["account_id"] not in account_ids:
            errors.append(
                f"Ownership {row['ownership_id']}: invalid account"
            )

        if row["customer_id"] not in customer_ids:
            errors.append(
                f"Ownership {row['ownership_id']}: invalid customer"
            )

    # Device ownership relationships
    for row in devices:
        if row["customer_id"] not in customer_ids:
            errors.append(
                f"Device {row['device_id']}: invalid customer"
            )

    # Transaction relationships
    for row in transactions:
        if row["account_id"] not in account_ids:
            errors.append(
                f"Transaction {row['transaction_id']}: invalid account"
            )

        if row["merchant_id"] and row["merchant_id"] not in merchant_ids:
            errors.append(
                f"Transaction {row['transaction_id']}: invalid merchant"
            )

        if row["device_id"] and row["device_id"] not in device_ids:
            errors.append(
                f"Transaction {row['transaction_id']}: invalid device"
            )

    # Transfer relationships
    for row in transfers:
        if row["source_transaction_id"] not in transaction_ids:
            errors.append(
                f"Transfer {row['transfer_id']}: invalid source transaction"
            )

        if row["destination_transaction_id"] not in transaction_ids:
            errors.append(
                f"Transfer {row['transfer_id']}: invalid destination transaction"
            )

        if row["source_account_id"] not in account_ids:
            errors.append(
                f"Transfer {row['transfer_id']}: invalid source account"
            )

        if row["destination_account_id"] not in account_ids:
            errors.append(
                f"Transfer {row['transfer_id']}: invalid destination account"
            )

    # Ground-truth relationships
    for row in ground_truth:
        if row["transaction_id"] not in transaction_ids:
            errors.append(
                f"Issue {row['issue_id']}: invalid transaction"
            )

        if row["account_id"] not in account_ids:
            errors.append(
                f"Issue {row['issue_id']}: invalid account"
            )

        if row["transfer_id"] and row["transfer_id"] not in transfer_ids:
            errors.append(
                f"Issue {row['issue_id']}: invalid transfer"
            )

    # Account event relationships
    for row in account_events:
        if row["account_id"] not in account_ids:
            errors.append(
                f"Event {row['event_id']}: invalid account"
            )

    print("\nFOREIGN KEY VALIDATION")
    print("=" * 45)

    if errors:
        for error in errors[:30]:
            print("FAIL:", error)

        print(f"\nTotal relationship errors: {len(errors)}")
        return False

    print("PASS: Account ownership relationships")
    print("PASS: Device ownership relationships")
    print("PASS: Transaction relationships")
    print("PASS: Transfer relationships")
    print("PASS: Ground-truth relationships")
    print("PASS: Account event relationships")
    print("\nRESULT: ALL RELATIONSHIPS ARE VALID")

    return True


if __name__ == "__main__":
    validate_relationships()
