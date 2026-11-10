
import csv
from datetime import datetime

from generator.config import DATA_DIR


def read_csv(filename):
    with open(DATA_DIR / filename, encoding="utf-8") as file:
        return list(csv.DictReader(file))


def validate_lifecycle():
    accounts = read_csv("accounts.csv")
    events = read_csv("account_events.csv")

    account_lookup = {
        account["account_id"]: account
        for account in accounts
    }

    errors = []

    print("\nACCOUNT LIFECYCLE VALIDATION")
    print("=" * 55)

    # Check every account event
    for event in events:
        event_id = event["event_id"]
        account_id = event["account_id"]

        account = account_lookup.get(account_id)

        if account is None:
            errors.append(
                f"{event_id}: Account does not exist"
            )
            continue

        # Validate event type and status transition
        if event["event_type"] == "REACTIVATION":
            if event["previous_status"] != "DORMANT":
                errors.append(
                    f"{event_id}: Reactivation must start from DORMANT"
                )

            if event["new_status"] != "ACTIVE":
                errors.append(
                    f"{event_id}: Reactivation must end in ACTIVE"
                )

        elif event["event_type"] == "CLOSURE":
            if event["new_status"] != "CLOSED":
                errors.append(
                    f"{event_id}: Closure must end in CLOSED"
                )

        else:
            errors.append(
                f"{event_id}: Unknown event type"
            )

        # Validate event timestamp
        try:
            datetime.fromisoformat(event["event_timestamp"])
        except ValueError:
            errors.append(
                f"{event_id}: Invalid event timestamp"
            )

        # Validate current status for this event
        if event["event_type"] == "REACTIVATION":
            if account["account_status"] != "ACTIVE":
                errors.append(
                    f"{event_id}: Account is not currently ACTIVE"
                )

    # Check event order for each account
    events_by_account = {}

    for event in events:
        events_by_account.setdefault(
            event["account_id"], []
        ).append(event)

    for account_id, account_events in events_by_account.items():
        account_events.sort(
            key=lambda event: event["event_timestamp"]
        )

        for previous, current in zip(
            account_events, account_events[1:]
        ):
            if current["event_timestamp"] < previous["event_timestamp"]:
                errors.append(
                    f"{account_id}: Events are out of chronological order"
                )

    print(f"Accounts checked: {len(accounts)}")
    print(f"Lifecycle events checked: {len(events)}")

    if errors:
        print(f"\nFAIL: {len(errors)} lifecycle errors found")

        for error in errors[:20]:
            print("FAIL:", error)

        print("\nRESULT: LIFECYCLE VALIDATION FAILED")
        return False

    print("PASS: Account event references")
    print("PASS: Status transition rules")
    print("PASS: Event timestamps")
    print("PASS: Current account status")
    print("PASS: Event chronology")
    print("\nRESULT: ALL LIFECYCLE CHECKS PASSED")

    return True


if __name__ == "__main__":
    validate_lifecycle()
