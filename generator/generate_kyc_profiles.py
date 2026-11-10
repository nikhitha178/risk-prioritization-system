
import csv
import random
from datetime import date, datetime, timedelta, timezone

from generator.config import DATA_DIR, RANDOM_SEED


DOCUMENT_TYPES = [
    "PAN",
    "PASSPORT",
    "VOTER_ID",
    "DRIVING_LICENSE",
]

VERIFICATION_STATUSES = [
    "VERIFIED",
    "PENDING",
    "REJECTED",
]


def generate_kyc_profiles():
    rng = random.Random(RANDOM_SEED + 10)

    customers_file = DATA_DIR / "customers.csv"

    if not customers_file.exists():
        raise FileNotFoundError("Generate customers first.")

    with customers_file.open(
        "r", newline="", encoding="utf-8-sig"
    ) as file:
        customers = list(csv.DictReader(file))

    profiles = []

    for index, customer in enumerate(customers, start=1):
        created_at = datetime.fromisoformat(
            customer["created_at"]
        )

        status = rng.choices(
            VERIFICATION_STATUSES,
            weights=[80, 12, 8],
            k=1
        )[0]

        document_type = rng.choice(DOCUMENT_TYPES)

        verified_at = ""
        expiry_date = ""
        remarks = ""

        if status == "VERIFIED":
            verified_at = (
                created_at + timedelta(days=rng.randint(1, 15))
            ).isoformat()

            expiry_date = (
                date(2026, 10, 22)
                + timedelta(days=rng.randint(365, 3650))
            ).isoformat()

            remarks = "Synthetic KYC verification completed."

        elif status == "PENDING":
            remarks = "Awaiting document verification."

        else:
            remarks = "Synthetic document verification failed."

        profiles.append({
            "kyc_id": f"KYC-2026-{index:06d}",
            "customer_id": customer["customer_id"],
            "verification_status": status,
            "document_type": document_type,
            "verified_at": verified_at,
            "expiry_date": expiry_date,
            "remarks": remarks,
        })

    output_file = DATA_DIR / "kyc_profiles.csv"

    with output_file.open(
        "w", newline="", encoding="utf-8"
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "kyc_id",
                "customer_id",
                "verification_status",
                "document_type",
                "verified_at",
                "expiry_date",
                "remarks",
            ]
        )

        writer.writeheader()
        writer.writerows(profiles)

    print("KYC generation completed.")
    print("Customers:", len(customers))
    print("KYC profiles:", len(profiles))

    for status in VERIFICATION_STATUSES:
        count = sum(
            profile["verification_status"] == status
            for profile in profiles
        )
        print(f"{status}: {count}")


if __name__ == "__main__":
    generate_kyc_profiles()
