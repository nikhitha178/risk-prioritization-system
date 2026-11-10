
import csv
import random
from datetime import datetime, timedelta, timezone

from generator.config import DATA_DIR, RANDOM_SEED


DEVICE_TYPES = ["MOBILE", "LAPTOP", "TABLET"]

OPERATING_SYSTEMS = {
    "MOBILE": ["Android", "iOS"],
    "LAPTOP": ["Windows 11", "Linux", "macOS"],
    "TABLET": ["Android", "iPadOS"],
}

BROWSERS = ["Chrome", "Firefox", "Edge", "Safari"]


def generate_devices():
    rng = random.Random(RANDOM_SEED + 3)

    with open(DATA_DIR / "customers.csv", encoding="utf-8") as file:
        customers = list(csv.DictReader(file))

    devices = []

    for customer in customers:
        customer_id = customer["customer_id"]

        # Each customer gets between 1 and 3 registered devices.
        device_count = rng.randint(1, 3)

        customer_created = datetime.fromisoformat(
            customer["created_at"]
        )

        for sequence in range(1, device_count + 1):
            device_type = rng.choice(DEVICE_TYPES)

            registered_at = customer_created + timedelta(
                seconds=rng.randint(0, 86400 * 30)
            )

            device_number = len(devices) + 1

            devices.append({
                "device_id": f"DEV-{device_number:07d}",
                "customer_id": customer_id,
                "device_type": device_type,
                "operating_system": rng.choice(
                    OPERATING_SYSTEMS[device_type]
                ),
                "browser": rng.choice(BROWSERS),
                # Documentation-only IP address range.
                "ip_address": f"192.0.2.{rng.randint(1, 254)}",
                "registered_at": registered_at.isoformat(),
                "is_trusted": rng.random() < 0.75,
                "is_active": rng.random() < 0.95,
            })

    return devices


def save_devices(devices):
    output_file = DATA_DIR / "devices.csv"

    with open(output_file, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=devices[0].keys())
        writer.writeheader()
        writer.writerows(devices)

    print(f"Devices generated: {len(devices)}")
    print(f"Saved to: {output_file}")


if __name__ == "__main__":
    data = generate_devices()
    save_devices(data)

    print("\nSample devices:")

    for device in data[:5]:
        print(device)
