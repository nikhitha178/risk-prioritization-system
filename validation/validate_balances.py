
import csv
from collections import defaultdict
from decimal import Decimal, InvalidOperation

from generator.config import DATA_DIR


def read_csv(filename):
    with open(DATA_DIR / filename, encoding="utf-8") as file:
        return list(csv.DictReader(file))


def money(value):
    return Decimal(value)


def validate_balances():
    accounts = read_csv("accounts.csv")
    transactions = read_csv("transactions.csv")

    errors = []
    calculated_balances = {}

    print("\nTRANSACTION BALANCE VALIDATION")
    print("=" * 55)

    # Start with each account's opening balance
    for account in accounts:
        calculated_balances[account["account_id"]] = money(
            account["opening_balance"]
        )

    # Process transactions in chronological order
    transactions.sort(
        key=lambda row: (
            row["transaction_timestamp"],
            row["transaction_id"]
        )
    )

    for txn in transactions:
        account_id = txn["account_id"]

        if account_id not in calculated_balances:
            errors.append(
                f"{txn['transaction_id']}: Account not found"
            )
            continue

        try:
            amount = money(txn["amount"])
            recorded_before = money(txn["balance_before"])
            recorded_after = money(txn["balance_after"])
        except (InvalidOperation, TypeError):
            errors.append(
                f"{txn['transaction_id']}: Invalid monetary value"
            )
            continue

        expected_before = calculated_balances[account_id]

        if recorded_before != expected_before:
            errors.append(
                f"{txn['transaction_id']}: "
                f"Expected balance before {expected_before}, "
                f"found {recorded_before}"
            )

        if txn["transaction_status"] == "SUCCESS":
            if txn["transaction_type"] == "DEBIT":
                expected_after = expected_before - amount
            elif txn["transaction_type"] == "CREDIT":
                expected_after = expected_before + amount
            else:
                errors.append(
                    f"{txn['transaction_id']}: Invalid transaction type"
                )
                continue
        else:
            expected_after = expected_before

        if recorded_after != expected_after:
            errors.append(
                f"{txn['transaction_id']}: "
                f"Expected balance after {expected_after}, "
                f"found {recorded_after}"
            )

        calculated_balances[account_id] = expected_after

    # Compare final ledger balance with account master data
    account_lookup = {
        account["account_id"]: account
        for account in accounts
    }

    for account_id, calculated_balance in calculated_balances.items():
        stored_balance = money(
            account_lookup[account_id]["current_balance"]
        )

        if calculated_balance != stored_balance:
            errors.append(
                f"{account_id}: "
                f"Ledger balance {calculated_balance} "
                f"does not match account balance {stored_balance}"
            )

    print(f"Transactions checked: {len(transactions)}")
    print(f"Accounts checked: {len(accounts)}")

    if errors:
        print(f"\nFAIL: {len(errors)} balance errors found")

        for error in errors[:20]:
            print("FAIL:", error)

        return False

    print("PASS: Transaction balance arithmetic")
    print("PASS: Chronological balance continuity")
    print("PASS: Failed/pending transaction balances")
    print("PASS: Final account balances")
    print("\nRESULT: ALL BALANCE CHECKS PASSED")

    return True


if __name__ == "__main__":
    validate_balances()
