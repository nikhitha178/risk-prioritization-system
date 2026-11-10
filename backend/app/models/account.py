
from sqlalchemy import (
    Column,
    String,
    Numeric,
    DateTime,
    Boolean,
    CheckConstraint,
    func,
)

from backend.app.database import Base


class Account(Base):
    __tablename__ = "accounts"

    account_id = Column(String(30), primary_key=True, index=True)

    account_type = Column(String(30), nullable=False)

    account_status = Column(
        String(20),
        nullable=False,
        default="ACTIVE"
    )

    current_balance = Column(
        Numeric(18, 2),
        nullable=False,
        default=0
    )

    currency = Column(
        String(3),
        nullable=False,
        default="INR"
    )

    overdraft_allowed = Column(
        Boolean,
        nullable=False,
        default=False
    )

    overdraft_limit = Column(
        Numeric(18, 2),
        nullable=False,
        default=0
    )

    opened_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint(
            "current_balance >= 0 OR overdraft_allowed = TRUE",
            name="check_account_balance"
        ),
        CheckConstraint(
            "overdraft_limit >= 0",
            name="check_overdraft_limit"
        ),
    )
