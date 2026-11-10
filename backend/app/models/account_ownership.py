
from sqlalchemy import (
    Column, String, DateTime, ForeignKey,
    Numeric, CheckConstraint, func
)
from backend.app.database import Base


class AccountOwnership(Base):
    __tablename__ = "account_ownerships"

    ownership_id = Column(String(30), primary_key=True)

    account_id = Column(
        String(30),
        ForeignKey("accounts.account_id"),
        nullable=False,
        index=True
    )

    customer_id = Column(
        String(20),
        ForeignKey("customers.customer_id"),
        nullable=False,
        index=True
    )

    ownership_percentage = Column(
        Numeric(5, 2),
        nullable=False,
        default=100
    )

    ownership_type = Column(
        String(30),
        nullable=False,
        default="PRIMARY"
    )

    effective_from = Column(
        DateTime(timezone=True),
        nullable=False
    )

    effective_until = Column(
        DateTime(timezone=True),
        nullable=True
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint(
            "ownership_percentage > 0 AND ownership_percentage <= 100",
            name="check_ownership_percentage"
        ),
        CheckConstraint(
            "effective_until IS NULL OR effective_until > effective_from",
            name="check_ownership_dates"
        ),
    )
