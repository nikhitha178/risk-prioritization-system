
from sqlalchemy import (
    Column, String, Text, DateTime,
    ForeignKey, func
)
from backend.app.database import Base


class TransactionEvent(Base):
    __tablename__ = "transaction_events"

    event_id = Column(String(30), primary_key=True)

    transaction_id = Column(
        String(30),
        ForeignKey("transactions.transaction_id"),
        nullable=False,
        index=True
    )

    event_type = Column(String(50), nullable=False)

    previous_status = Column(String(20), nullable=True)

    new_status = Column(String(20), nullable=True)

    description = Column(Text, nullable=True)

    event_timestamp = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )
