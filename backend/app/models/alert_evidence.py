
from sqlalchemy import (
    Column, String, Text, DateTime,
    ForeignKey, func
)
from backend.app.database import Base


class AlertEvidence(Base):
    __tablename__ = "alert_evidence"

    evidence_id = Column(String(30), primary_key=True)

    alert_id = Column(
        String(30),
        ForeignKey("alerts.alert_id"),
        nullable=False,
        index=True
    )

    evidence_type = Column(String(50), nullable=False)

    evidence_description = Column(Text, nullable=False)

    source_transaction_id = Column(
        String(30),
        ForeignKey("transactions.transaction_id"),
        nullable=True
    )

    captured_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )
