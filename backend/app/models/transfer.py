
from sqlalchemy import Column, String, ForeignKey, DateTime, Numeric, func
from backend.app.database import Base


class Transfer(Base):
    __tablename__ = "transfers"

    transfer_id = Column(String(30), primary_key=True)

    source_transaction_id = Column(
        String(30),
        ForeignKey("transactions.transaction_id"),
        nullable=False,
        unique=True
    )

    destination_transaction_id = Column(
        String(30),
        ForeignKey("transactions.transaction_id"),
        nullable=False,
        unique=True
    )

    source_account_id = Column(
        String(30),
        ForeignKey("accounts.account_id"),
        nullable=False
    )

    destination_account_id = Column(
        String(30),
        ForeignKey("accounts.account_id"),
        nullable=False
    )

    amount = Column(Numeric(18, 2), nullable=False)

    transfer_timestamp = Column(
        DateTime(timezone=True),
        nullable=False
    )

    created_at = Column(DateTime(timezone=True), server_default=func.now())
