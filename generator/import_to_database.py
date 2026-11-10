
import csv
from pathlib import Path
from datetime import datetime, date
from decimal import Decimal

from sqlalchemy import DateTime, Date, Numeric, Boolean
from backend.app.models.kyc_profile import KYCProfile
from backend.app.database import SessionLocal

from backend.app.models.customer import Customer
from backend.app.models.merchant import Merchant
from backend.app.models.account import Account
from backend.app.models.account_ownership import AccountOwnership
from backend.app.models.device import Device
from backend.app.models.risk_rule import RiskRule
from backend.app.models.transaction import Transaction
from backend.app.models.transfer import Transfer
from backend.app.models.account_event import AccountEvent
from backend.app.models.alert import Alert
from backend.app.models.alert_evidence import AlertEvidence


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"

# Parent records must be imported before dependent records.
IMPORT_ORDER = [
    ("customers.csv", Customer),
    ("kyc_profiles.csv", KYCProfile),
    ("merchants.csv", Merchant),
    ("accounts.csv", Account),
    ("account_ownerships.csv", AccountOwnership),
    ("devices.csv", Device),
    ("risk_rules.csv", RiskRule),
    ("transactions.csv", Transaction),
    ("transfers.csv", Transfer),
    ("account_events.csv", AccountEvent),
    ("alerts.csv", Alert),
    ("alert_evidence.csv", AlertEvidence),
]


def convert_value(value, column):
    """Convert CSV strings into the correct Python data types."""

    if value is None or value.strip() == "":
        return None

    column_type = column.type

    if isinstance(column_type, Boolean):
        normalized = value.strip().lower()

        if normalized in ("true", "1", "yes"):
            return True

        if normalized in ("false", "0", "no"):
            return False

        raise ValueError(f"Invalid Boolean value: {value}")

    if isinstance(column_type, DateTime):
        return datetime.fromisoformat(value.strip().replace("Z", "+00:00"))

    if isinstance(column_type, Date):
        return date.fromisoformat(value.strip())

    if isinstance(column_type, Numeric):
        return Decimal(value.strip())

    return value


def import_csv(db, filename, model):
    """Import one CSV file while skipping existing primary keys."""

    file_path = DATA_DIR / filename

    if not file_path.exists():
        print(f"SKIPPED: {filename} does not exist.")
        return 0

    table = model.__table__
    primary_key = list(table.primary_key.columns)[0]

    existing_ids = {
        row[0]
        for row in db.query(primary_key).all()
    }

    imported = 0
    skipped = 0

    with file_path.open("r", newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)

        for csv_row in reader:
            record = {}

            for column in table.columns:
                column_name = column.name

                if column_name not in csv_row:
                    continue

                raw_value = csv_row[column_name]

                if raw_value is None or raw_value.strip() == "":
                    if column.nullable:
                        record[column_name] = None
                    elif column.default is None and column.server_default is None:
                        raise ValueError(
                            f"{filename}: Required field "
                            f"'{column_name}' is empty."
                        )
                    continue

                record[column_name] = convert_value(
                    raw_value,
                    column
                )

            record_id = record.get(primary_key.name)

            if not record_id:
                raise ValueError(
                    f"{filename}: Missing primary key "
                    f"'{primary_key.name}'."
                )

            if record_id in existing_ids:
                skipped += 1
                continue

            db.add(model(**record))
            existing_ids.add(record_id)
            imported += 1

            # Flush periodically to keep memory usage manageable.
            if imported % 1000 == 0:
                db.flush()

    db.flush()

    print(
        f"{filename}: imported={imported}, "
        f"already_existing={skipped}"
    )

    return imported


def main():
    db = SessionLocal()

    total_imported = 0

    try:
        for filename, model in IMPORT_ORDER:
            total_imported += import_csv(
                db,
                filename,
                model
            )

        db.commit()

        print("\nDatabase import completed successfully!")
        print("Total new records imported:", total_imported)

    except Exception as error:
        db.rollback()

        print("\nDatabase import failed.")
        print("Reason:", error)

        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()
