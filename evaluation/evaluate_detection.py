
import csv
from pathlib import Path

from generator.config import DATA_DIR


EVALUATION_DIR = Path(__file__).resolve().parent


def read_csv(path):
    with open(path, encoding="utf-8") as file:
        return list(csv.DictReader(file))


def evaluate_detection():
    ground_truth = read_csv(DATA_DIR / "ground_truth.csv")
    alerts = read_csv(DATA_DIR / "alerts.csv")
    rules = read_csv(DATA_DIR / "risk_rules.csv")

    # Map rule IDs to their risk categories
    rule_categories = {
        rule["rule_id"]: rule["rule_category"]
        for rule in rules
    }

    # Normalize the category names used in ground truth
    category_mapping = {
        "HIGH_VALUE": "HIGH_VALUE",
        "VELOCITY_SPIKE": "VELOCITY",
        "NEW_DEVICE": "NEW_DEVICE",
        "CIRCULAR_TRANSFER": "CIRCULAR_TRANSFER",
        "DORMANT_REACTIVATION": "DORMANT_REACTIVATION",
    }

    actual = set()
    detected = set()

    for row in ground_truth:
        transaction_id = row["transaction_id"]
        issue_type = row["issue_type"].upper()

        actual.add((
            transaction_id,
            category_mapping.get(issue_type, issue_type)
        ))

    for alert in alerts:
        transaction_id = alert["transaction_id"]
        category = rule_categories.get(alert["rule_id"])

        if category:
            detected.add((transaction_id, category))

    # Compare the expected anomalies and engine detections
    all_pairs = actual | detected

    results = []

    for transaction_id, category in sorted(all_pairs):
        is_actual = (transaction_id, category) in actual
        is_detected = (transaction_id, category) in detected

        if is_actual and is_detected:
            result = "TRUE_POSITIVE"
        elif is_detected and not is_actual:
            result = "FALSE_POSITIVE"
        else:
            result = "FALSE_NEGATIVE"

        results.append({
            "transaction_id": transaction_id,
            "issue_type": category,
            "ground_truth": is_actual,
            "detected": is_detected,
            "result": result,
        })

    output_path = EVALUATION_DIR / "detection_results.csv"

    with open(
        output_path,
        "w",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "transaction_id",
                "issue_type",
                "ground_truth",
                "detected",
                "result",
            ],
        )
        writer.writeheader()
        writer.writerows(results)

    print("\nDETECTION EVALUATION")
    print("=" * 50)
    print(f"Ground-truth anomaly pairs: {len(actual)}")
    print(f"Detected transaction-rule pairs: {len(detected)}")
    print(f"Comparison records: {len(results)}")
    print(
        f"True positives: {sum(r['result'] == 'TRUE_POSITIVE' for r in results)}")
    print(
        f"False positives: {sum(r['result'] == 'FALSE_POSITIVE' for r in results)}")
    print(
        f"False negatives: {sum(r['result'] == 'FALSE_NEGATIVE' for r in results)}")
    print(f"\nSaved: {output_path}")


if __name__ == "__main__":
    evaluate_detection()
