
import csv
from collections import defaultdict
from datetime import datetime, timedelta
from decimal import Decimal

from generator.config import DATA_DIR


def read_csv(filename):
    path = DATA_DIR / filename

    with open(path, "r", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def write_csv(filename, records, fieldnames):
    with open(
        DATA_DIR / filename,
        "w",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)


def parse_timestamp(value):
    return datetime.fromisoformat(value)


def is_successful(transaction):
    return transaction["transaction_status"].upper() == "SUCCESS"


def is_true(value):
    return str(value).strip().lower() in ("true", "1", "yes")


def get_risk_level(score):
    if score >= 50:
        return "CRITICAL"
    elif score >= 30:
        return "HIGH"
    elif score >= 20:
        return "MEDIUM"
    return "LOW"


def find_circular_transfers(transfers, threshold):
    """
    Find transfer edges that belong to a circular path
    involving at least the configured number of accounts.
    """

    graph = defaultdict(list)
    nodes = set()

    for transfer in transfers:
        source = transfer["source_account_id"]
        destination = transfer["destination_account_id"]

        graph[source].append((destination, transfer))
        nodes.add(source)
        nodes.add(destination)

    index = 0
    stack = []
    on_stack = set()
    indices = {}
    lowlink = {}
    components = []

    def strong_connect(node):
        nonlocal index

        indices[node] = index
        lowlink[node] = index
        index += 1

        stack.append(node)
        on_stack.add(node)

        for neighbor, transfer in graph[node]:
            if neighbor not in indices:
                strong_connect(neighbor)
                lowlink[node] = min(
                    lowlink[node], lowlink[neighbor]
                )

            elif neighbor in on_stack:
                lowlink[node] = min(
                    lowlink[node], indices[neighbor]
                )

        if lowlink[node] == indices[node]:
            component = []

            while True:
                member = stack.pop()
                on_stack.remove(member)
                component.append(member)

                if member == node:
                    break

            components.append(component)

    for node in nodes:
        if node not in indices:
            strong_connect(node)

    component_map = {}

    for component_number, component in enumerate(components):
        for account_id in component:
            component_map[account_id] = component_number

    circular_transfer_ids = set()

    for transfer in transfers:
        source = transfer["source_account_id"]
        destination = transfer["destination_account_id"]

        if (
            source != destination
            and component_map.get(source) == component_map.get(destination)
        ):
            component_size = len(
                components[component_map[source]]
            )

            if component_size >= threshold:
                circular_transfer_ids.add(transfer["transfer_id"])

    return circular_transfer_ids


def evaluate_transactions():
    transactions = read_csv("transactions.csv")
    accounts = read_csv("accounts.csv")
    devices = read_csv("devices.csv")
    transfers = read_csv("transfers.csv")
    account_events = read_csv("account_events.csv")
    rules = read_csv("risk_rules.csv")

    active_rules = {
        rule["rule_category"]: rule
        for rule in rules
        if is_true(rule["is_active"])
    }

    triggers = defaultdict(dict)

    def add_trigger(transaction_id, category, description):
        if category not in active_rules:
            return

        triggers[transaction_id][category] = description

    # RULE 1: High-value transactions
    high_value_rule = active_rules.get("HIGH_VALUE")

    if high_value_rule:
        threshold = Decimal(high_value_rule["threshold_value"])

        for transaction in transactions:
            if (
                is_successful(transaction)
                and Decimal(transaction["amount"]) > threshold
            ):
                add_trigger(
                    transaction["transaction_id"],
                    "HIGH_VALUE",
                    f"Transaction amount ₹{transaction['amount']} "
                    f"exceeds the configured threshold ₹{threshold}."
                )

    # RULE 2: Transaction velocity
    velocity_rule = active_rules.get("VELOCITY")

    if velocity_rule:
        minimum_count = int(
            Decimal(velocity_rule["threshold_value"])
        )

        window_minutes = 10

        account_transactions = defaultdict(list)

        for transaction in transactions:
            if is_successful(transaction):
                account_transactions[
                    transaction["account_id"]
                ].append(transaction)

        for account_id, account_txns in account_transactions.items():
            account_txns.sort(
                key=lambda txn: parse_timestamp(
                    txn["transaction_timestamp"]
                )
            )

            left = 0

            for right in range(len(account_txns)):
                current_time = parse_timestamp(
                    account_txns[right]["transaction_timestamp"]
                )

                while left <= right:
                    oldest_time = parse_timestamp(
                        account_txns[left]["transaction_timestamp"]
                    )

                    if current_time - oldest_time > timedelta(
                        minutes=window_minutes
                    ):
                        left += 1
                    else:
                        break

                window = account_txns[left:right + 1]

                if len(window) >= minimum_count:
                    description = (
                        f"Account {account_id} performed "
                        f"{len(window)} successful transactions "
                        f"within {window_minutes} minutes."
                    )

                    for transaction in window:
                        add_trigger(
                            transaction["transaction_id"],
                            "VELOCITY",
                            description
                        )

    # RULE 3: Transactions using untrusted devices

    # RULE 3: Recently registered untrusted devices
    device_rule = active_rules.get("NEW_DEVICE")

    if device_rule:
        device_lookup = {
            device["device_id"]: device
            for device in devices
        }

        registration_window = timedelta(hours=24)

        for transaction in transactions:
            if not is_successful(transaction):
                continue

            device = device_lookup.get(transaction["device_id"])

            if not device or is_true(device["is_trusted"]):
                continue

            registered_at = parse_timestamp(device["registered_at"])
            transaction_time = parse_timestamp(
                transaction["transaction_timestamp"]
            )

            time_since_registration = (
                transaction_time - registered_at
            )

            if (
                timedelta(0) <= time_since_registration
                <= registration_window
            ):
                add_trigger(
                    transaction["transaction_id"],
                    "NEW_DEVICE",
                    f"Transaction used untrusted device "
                    f"{device['device_id']} registered "
                    f"{time_since_registration} before the transaction."
                )

    # RULE 4: Circular transfers
    circular_rule = active_rules.get("CIRCULAR_TRANSFER")

    if circular_rule:
        minimum_accounts = int(
            Decimal(circular_rule["threshold_value"])
        )

        circular_ids = find_circular_transfers(
            transfers,
            minimum_accounts
        )

        for transfer in transfers:
            if transfer["transfer_id"] not in circular_ids:
                continue

            add_trigger(
                transfer["source_transaction_id"],
                "CIRCULAR_TRANSFER",
                f"Source transaction belongs to circular transfer "
                f"{transfer['transfer_id']} involving "
                f"{transfer['source_account_id']} and "
                f"{transfer['destination_account_id']}."
            )

            add_trigger(
                transfer["destination_transaction_id"],
                "CIRCULAR_TRANSFER",
                f"Destination transaction belongs to circular transfer "
                f"{transfer['transfer_id']} involving "
                f"{transfer['source_account_id']} and "
                f"{transfer['destination_account_id']}."
            )

    # RULE 5: Transactions after dormant account reactivation
    dormant_rule = active_rules.get("DORMANT_REACTIVATION")

    if dormant_rule:
        window_minutes = int(
            Decimal(dormant_rule["threshold_value"])
        )

        reactivations = defaultdict(list)

        for event in account_events:
            if (
                event["event_type"] == "REACTIVATION"
                and event["previous_status"] == "DORMANT"
                and event["new_status"] == "ACTIVE"
            ):
                reactivations[event["account_id"]].append(
                    parse_timestamp(event["event_timestamp"])
                )

        for transaction in transactions:
            if not is_successful(transaction):
                continue

            account_id = transaction["account_id"]
            transaction_time = parse_timestamp(
                transaction["transaction_timestamp"]
            )

            for event_time in reactivations.get(account_id, []):
                if (
                    event_time <= transaction_time
                    <= event_time + timedelta(minutes=window_minutes)
                ):
                    add_trigger(
                        transaction["transaction_id"],
                        "DORMANT_REACTIVATION",
                        f"Transaction occurred within "
                        f"{window_minutes} minutes after "
                        f"dormant account reactivation."
                    )

    return transactions, active_rules, triggers


def run_risk_engine():
    transactions, rules, triggers = evaluate_transactions()

    transaction_lookup = {
        transaction["transaction_id"]: transaction
        for transaction in transactions
    }

    alerts = []
    evidence_records = []

    alert_number = 0
    evidence_number = 0

    # Stable ordering for reproducible results
    for transaction in sorted(
        transactions,
        key=lambda txn: (
            txn["transaction_timestamp"],
            txn["transaction_id"]
        )
    ):
        transaction_id = transaction["transaction_id"]

        triggered_rules = triggers.get(transaction_id, {})

        for category in sorted(triggered_rules):
            rule = rules[category]
            description = triggered_rules[category]

            alert_number += 1
            evidence_number += 1

            alert_id = f"ALT-2026-{alert_number:06d}"
            evidence_id = f"EVD-2026-{evidence_number:06d}"

            score = int(rule["risk_score"])
            timestamp = transaction["transaction_timestamp"]

            alerts.append({
                "alert_id": alert_id,
                "transaction_id": transaction_id,
                "rule_id": rule["rule_id"],
                "risk_score": score,
                "risk_level": get_risk_level(score),
                "alert_status": "OPEN",
                "evidence": description,
                "created_at": timestamp,
            })

            evidence_records.append({
                "evidence_id": evidence_id,
                "alert_id": alert_id,
                "evidence_type": category,
                "evidence_description": description,
                "source_transaction_id": transaction_id,
                "captured_at": timestamp,
            })

    alert_fields = [
        "alert_id",
        "transaction_id",
        "rule_id",
        "risk_score",
        "risk_level",
        "alert_status",
        "evidence",
        "created_at",
    ]

    evidence_fields = [
        "evidence_id",
        "alert_id",
        "evidence_type",
        "evidence_description",
        "source_transaction_id",
        "captured_at",
    ]

    write_csv("alerts.csv", alerts, alert_fields)
    write_csv("alert_evidence.csv", evidence_records, evidence_fields)

    print("\nTRANSACTION RISK ENGINE")
    print("=" * 55)
    print(f"Transactions evaluated: {len(transactions)}")
    print(f"Active rules evaluated: {len(rules)}")
    print(f"Alerts generated: {len(alerts)}")
    print(f"Evidence records generated: {len(evidence_records)}")

    print("\nALERTS BY RISK LEVEL")

    for level in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
        count = sum(
            1 for alert in alerts
            if alert["risk_level"] == level
        )
        print(f"{level}: {count}")

    print("\nALERTS BY RULE")

    for category in sorted(rules):
        count = sum(
            1 for alert in alerts
            if alert["rule_id"] == rules[category]["rule_id"]
        )
        print(f"{category}: {count}")

    print("\nOutput files:")
    print("data/alerts.csv")
    print("data/alert_evidence.csv")

    print("\nRisk engine execution completed.")

    return alerts


if __name__ == "__main__":
    run_risk_engine()
