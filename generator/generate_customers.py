
import csv
import random
from datetime import date, datetime, timedelta, timezone

from generator.config import CONFIG, DATA_DIR, RANDOM_SEED, START_DATE, END_DATE


# Synthetic name lists
FIRST_NAMES = [
    "Aarav", "Aditya", "Ananya", "Arjun", "Diya",
    "Ishaan", "Kavya", "Meera", "Neha", "Rahul",
    "Riya", "Sanjay", "Sneha", "Varun", "Priya",
    "Kiran", "Vikram", "Pooja", "Rohan", "Sana",
]

LAST_NAMES = [
    "Sharma", "Reddy", "Kumar", "Patel", "Rao",
    "Gupta", "Verma", "Mehta", "Singh", "Nair",
    "Iyer", "Das", "Joshi", "Kapoor", "Naidu",
]


def random_date_of_birth(rng):
    """Generate a synthetic date of birth for an adult customer."""

    today = date(2026, 10, 22)

    minimum_date = today - timedelta(days=85 * 365)
    maximum_date = today - timedelta(days=18 * 365)

    days_range = (maximum_date - minimum_date).days

    return minimum_date + timedelta(
        days=rng.randint(0, days_range)
    )


def random_created_at(rng):
    """Generate a deterministic customer creation timestamp."""

    start = datetime.fromisoformat(START_DATE).replace(
        tzinfo=timezone.utc
    )

    end = datetime.fromisoformat(END_DATE).replace(
        tzinfo=timezone.utc
    )

    total_seconds = int((end - start).total_seconds())

    return start + timedelta(
        seconds=rng.randint(0, total_seconds)
    )


def generate_customers():
    rng = random.Random(RANDOM_SEED)

    customers = []

    for number in range(1, CONFIG.customers + 1):

        customer_id = f"CUS-{number:06d}"

        first_name = rng.choice(FIRST_NAMES)
        last_name = rng.choice(LAST_NAMES)

        email = (
            f"{first_name.lower()}."
            f"{last_name.lower()}."
            f"{number:06d}@example.test"
        )

        # Synthetic placeholder phone number.
        # Never use this as a real contact number.
        phone = f"+910000{number:06d}"

        dob = random_date_of_birth(rng)
        created_at = random_created_at(rng)

        customers.append({
            "customer_id": customer_id,
            "first_name": first_name,
            "last_name": last_name,
            "date_of_birth": dob.isoformat(),
            "email": email,
            "phone": phone,
            "created_at": created_at.isoformat(),
        })

    return customers


def save_customers(customers):
    output_file = DATA_DIR / "customers.csv"

    fieldnames = [
        "customer_id",
        "first_name",
        "last_name",
        "date_of_birth",
        "email",
        "phone",
        "created_at",
    ]

    with open(
        output_file,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames
        )

        writer.writeheader()
        writer.writerows(customers)

    print(f"Customers generated: {len(customers)}")
    print(f"File saved: {output_file}")


if __name__ == "__main__":
    customer_data = generate_customers()

    save_customers(customer_data)

    print("\nSample customer records:")

    for customer in customer_data[:5]:
        print(customer)
