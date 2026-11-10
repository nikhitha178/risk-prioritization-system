
from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime,
    Text, Numeric, func
)
from backend.app.database import Base


class RiskRule(Base):
    __tablename__ = "risk_rules"

    rule_id = Column(String(30), primary_key=True)

    rule_name = Column(String(150), nullable=False)

    description = Column(Text, nullable=True)

    rule_category = Column(String(50), nullable=False)

    risk_score = Column(Integer, nullable=False)

    threshold_value = Column(Numeric(18, 2), nullable=True)

    version = Column(Integer, nullable=False, default=1)

    is_active = Column(Boolean, nullable=False, default=True)

    effective_from = Column(DateTime(timezone=True), nullable=False)

    effective_until = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
