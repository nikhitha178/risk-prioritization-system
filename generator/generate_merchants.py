
import csv
import random

from generator.config import DATA_DIR, RANDOM_SEED


MERCHANTS = [
    ("FreshMart Supermarket", "GROCERY", "Hyderabad"),
    ("CityFuel Station", "FUEL", "Hyderabad"),
    ("TechZone Electronics", "ELECTRONICS", "Bengaluru"),
    ("QuickBite Restaurant", "FOOD", "Hyderabad"),
    ("StyleHub Fashion", "FASHION", "Mumbai"),
    ("HealthPlus Pharmacy", "HEALTHCARE", "Hyderabad"),
    ("TravelWorld", "TRAVEL", "Delhi"),
    ("OnlineStore India", "E_COMMERCE", "Bengaluru"),
    ("MovieTime Cinemas", "ENTERTAINMENT", "Chennai"),
    ("EduLearn Services", "EDUCATION", "Hyderabad"),
    ("HomeNeeds Store", "HOME", "Pune"),
    ("DigitalPay Services", "DIGITAL_SERVICES", "Hyderabad"),
    ("MetroMart", "GROCERY", "Delhi"),
    ("AutoCare Center", "AUTOMOTIVE", "Mumbai"),
    ("CloudTech Services", "DIGITAL_SERVICES", "Bengaluru"),
]


def generate_merchants():
    rng = random.Random(RANDOM_SEED + 2)

    merchants = []

    for number, merchant in enumerate(MERCHANTS, start=1):
        name, category, location = merchant

        merchants.append({
            "merchant_id": f"MER-{number:04d}",
            "merchant_name": name,
            "merchant_category": category,
            "merchant_location": location,
            "country": "India",
            "is_active": True,
        })

    # Add extra synthetic merchants if needed in future.
    rng.shuffle(merchants)

    return merchants


def save_merchants(merchants):
    output_file = DATA_DIR / "merchants.csv"

    with open(output_file, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=merchants[0].keys())
        writer.writeheader()
        writer.writerows(merchants)

    print(f"Merchants generated: {len(merchants)}")
    print(f"Saved to: {output_file}")


if __name__ == "__main__":
    data = generate_merchants()
    save_merchants(data)

    for merchant in data[:5]:
        print(merchant)
