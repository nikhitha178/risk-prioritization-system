
from sqlalchemy import (
    Column, String, Text, DateTime, ForeignKey,
    Table, Integer, func
)
from sqlalchemy.orm import relationship
from backend.app.database import Base


case_alerts = Table(
    "case_alerts",
    Base.metadata,

    Column(
        "case_id",
        String(30),
        ForeignKey("cases.case_id"),
        primary_key=True
    ),

    Column(
        "alert_id",
        String(30),
        ForeignKey("alerts.alert_id"),
        primary_key=True
    )
)


class Case(Base):
    __tablename__ = "cases"

    case_id = Column(String(30), primary_key=True)

    case_title = Column(String(200), nullable=False)

    description = Column(Text, nullable=True)

    priority = Column(String(20), nullable=False)

    case_status = Column(
        String(30),
        nullable=False,
        default="OPEN"
    )

    assigned_analyst_id = Column(
        String(30),
        ForeignKey("analysts.analyst_id"),
        nullable=True
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    due_at = Column(DateTime(timezone=True), nullable=True)

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    alerts = relationship(
        "Alert",
        secondary=case_alerts
    )
