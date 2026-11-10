
import os
from pathlib import Path
from dataclasses import dataclass


# Project directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Dataset output directory
DATA_DIR = Path(os.getenv("DATA_DIR", PROJECT_ROOT / "data"))

# Reproducibility: same seed produces repeatable random data
RANDOM_SEED = 20261022

# Dataset mode: starter or full
DATASET_MODE = os.getenv("DATASET_MODE", "starter").lower()


@dataclass(frozen=True)
class DatasetConfig:
    customers: int
    accounts: int
    transactions: int
    alerts: int


DATASET_SIZES = {
    "starter": DatasetConfig(
        customers=500,
        accounts=700,
        transactions=10_000,
        alerts=100,
    ),
    "full": DatasetConfig(
        customers=5_000,
        accounts=7_000,
        transactions=100_000,
        alerts=1_000,
    ),
}

if DATASET_MODE not in DATASET_SIZES:
    raise ValueError(
        "Invalid DATASET_MODE. Choose 'starter' or 'full'."
    )

CONFIG = DATASET_SIZES[DATASET_MODE]


# Synthetic transaction configuration
CURRENCY = "INR"

MIN_TRANSACTION_AMOUNT = 100
MAX_TRANSACTION_AMOUNT = 100_000

# Historical data period
START_DATE = "2025-01-01"
END_DATE = "2026-10-22"


# Create data directory if it does not exist
DATA_DIR.mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    print("Transaction Risk Prioritization System")
    print("--------------------------------------")
    print(f"Dataset mode: {DATASET_MODE}")
    print(f"Random seed: {RANDOM_SEED}")
    print(f"Customers: {CONFIG.customers}")
    print(f"Accounts: {CONFIG.accounts}")
    print(f"Transactions: {CONFIG.transactions}")
    print(f"Target alerts: {CONFIG.alerts}")
    print(f"Data directory: {DATA_DIR}")
