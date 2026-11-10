
import csv
from generator.config import DATA_DIR


def read_csv(filename):
    with open(DATA_DIR / filename, encoding="utf-8") as file:
        return list(csv.DictReader(file))


def clean_descriptions():
    transactions = read_csv("transactions.csv")
    ground_truth = read_csv("ground_truth.csv")

    # Ground truth identifies which transactions contain planted anomalies.
    anomaly_transaction_ids = {
        row["transaction_id"]
        for row in ground_truth
        if row.get("transaction_id", "").strip()
    }

    cleaned_count = 0

    for transaction in transactions:
        if transaction["transaction_id"] in anomaly_transaction_ids:
            transaction["description"] = "Account transaction"
            cleaned_count += 1

    if cleaned_count != len(anomaly_transaction_ids):
        raise ValueError(
            "Not all ground-truth transaction IDs were found."
        )

    fieldnames = list(transactions[0].keys())

    with open(
        DATA_DIR / "transactions.csv",
        "w",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(transactions)

    print("Transaction description cleanup completed.")
    print(f"Descriptions neutralized: {cleaned_count}")
    print("Ground-truth labels remain in ground_truth.csv.")


if __name__ == "__main__":
    clean_descriptions()
