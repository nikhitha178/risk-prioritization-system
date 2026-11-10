
from sqlalchemy import (
    Column, String, Numeric, DateTime, ForeignKey,
    CheckConstraint, Index, func
)
from backend.app.database import Base


class Transaction(Base):
    __tablename__ = "transactions"

    transaction_id = Column(
        String(30),
        primary_key=True,
        index=True
    )

    account_id = Column(
        String(30),
        ForeignKey("accounts.account_id"),
        nullable=False,
        index=True
    )

    merchant_id = Column(
        String(20),
        ForeignKey("merchants.merchant_id"),
        nullable=True,
        index=True
    )

    device_id = Column(
        String(30),
        ForeignKey("devices.device_id"),
        nullable=True,
        index=True
    )

    transaction_type = Column(String(20), nullable=False)

    amount = Column(Numeric(18, 2), nullable=False)

    currency = Column(String(3), nullable=False, default="INR")

    transaction_status = Column(
        String(20),
        nullable=False,
        default="SUCCESS"
    )

    transaction_timestamp = Column(
        DateTime(timezone=True),
        nullable=False,
        index=True
    )

    balance_before = Column(Numeric(18, 2), nullable=False)

    balance_after = Column(Numeric(18, 2), nullable=False)

    description = Column(String(255), nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint(
            "amount > 0",
            name="check_transaction_amount"
        ),
        CheckConstraint(
            "transaction_type IN ('DEBIT', 'CREDIT')",
            name="check_transaction_type"
        ),
        CheckConstraint(
            "transaction_status IN ('SUCCESS', 'FAILED', 'PENDING')",
            name="check_transaction_status"
        ),
        Index(
            "ix_transactions_account_timestamp",
            "account_id",
            "transaction_timestamp"
        ),
    )
