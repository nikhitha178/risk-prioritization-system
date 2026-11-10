
from sqlalchemy import (
    Column, String, Integer, Text, DateTime,
    ForeignKey, func
)
from backend.app.database import Base


class Alert(Base):
    __tablename__ = "alerts"

    alert_id = Column(String(30), primary_key=True)

    transaction_id = Column(
        String(30),
        ForeignKey("transactions.transaction_id"),
        nullable=False,
        index=True
    )

    rule_id = Column(
        String(30),
        ForeignKey("risk_rules.rule_id"),
        nullable=False
    )

    risk_score = Column(Integer, nullable=False)

    risk_level = Column(String(20), nullable=False)

    alert_status = Column(
        String(30),
        nullable=False,
        default="OPEN"
    )

    evidence = Column(Text, nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )
