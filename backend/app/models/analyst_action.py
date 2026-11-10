
from sqlalchemy import (
    Column, String, Text, DateTime,
    ForeignKey, func
)
from backend.app.database import Base


class AnalystAction(Base):
    __tablename__ = "analyst_actions"

    action_id = Column(String(30), primary_key=True)

    case_id = Column(
        String(30),
        ForeignKey("cases.case_id"),
        nullable=False,
        index=True
    )

    analyst_id = Column(
        String(30),
        ForeignKey("analysts.analyst_id"),
        nullable=False
    )

    action_type = Column(String(50), nullable=False)

    previous_status = Column(String(30), nullable=True)

    new_status = Column(String(30), nullable=True)

    comments = Column(Text, nullable=True)

    action_timestamp = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )
