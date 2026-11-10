
import csv
from datetime import datetime, timezone

from generator.config import DATA_DIR


def generate_risk_rules():

    effective_from = datetime(
        2025, 1, 1, tzinfo=timezone.utc
    ).isoformat()

    rules = [
        {
            "rule_id": "RULE-001",
            "rule_name": "High Value Transaction",
            "description": "Flags transactions exceeding the configured high-value threshold.",
            "rule_category": "HIGH_VALUE",
            "risk_score": 30,
            "threshold_value": 200000,
            "version": 1,
            "is_active": True,
            "effective_from": effective_from,
            "effective_until": "",
        },
        {
            "rule_id": "RULE-002",
            "rule_name": "Transaction Velocity Spike",
            "description": "Flags accounts with five or more transactions within ten minutes.",
            "rule_category": "VELOCITY",
            "risk_score": 25,
            "threshold_value": 5,
            "version": 1,
            "is_active": True,
            "effective_from": effective_from,
            "effective_until": "",
        },
        {
            "rule_id": "RULE-003",
            "rule_name": "Untrusted Device",
            "description": "Flags transactions performed using an untrusted device.",
            "rule_category": "NEW_DEVICE",
            "risk_score": 20,
            "threshold_value": 0,
            "version": 1,
            "is_active": True,
            "effective_from": effective_from,
            "effective_until": "",
        },
        {
            "rule_id": "RULE-004",
            "rule_name": "Circular Fund Transfer",
            "description": "Flags transfers forming a circular movement of funds between accounts.",
            "rule_category": "CIRCULAR_TRANSFER",
            "risk_score": 35,
            "threshold_value": 3,
            "version": 1,
            "is_active": True,
            "effective_from": effective_from,
            "effective_until": "",
        },
        {
            "rule_id": "RULE-005",
            "rule_name": "Dormant Account Reactivation",
            "description": "Flags transactions occurring shortly after a dormant account is reactivated.",
            "rule_category": "DORMANT_REACTIVATION",
            "risk_score": 30,
            "threshold_value": 60,
            "version": 1,
            "is_active": True,
            "effective_from": effective_from,
            "effective_until": "",
        },
    ]

    output_file = DATA_DIR / "risk_rules.csv"

    with open(
        output_file,
        "w",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=rules[0].keys()
        )

        writer.writeheader()
        writer.writerows(rules)

    print("\nRISK RULE GENERATION")
    print("=" * 45)
    print(f"Rules generated: {len(rules)}")
    print(f"Output: {output_file}")

    for rule in rules:
        print(
            f"{rule['rule_id']} | "
            f"{rule['rule_name']} | "
            f"Score: {rule['risk_score']}"
        )


if __name__ == "__main__":
    generate_risk_rules()
