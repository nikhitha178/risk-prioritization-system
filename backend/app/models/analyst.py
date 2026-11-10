
from sqlalchemy import Column, String, Boolean, DateTime, func
from backend.app.database import Base


class Analyst(Base):
    __tablename__ = "analysts"

    analyst_id = Column(String(30), primary_key=True)

    full_name = Column(String(150), nullable=False)

    email = Column(String(150), unique=True, nullable=False)

    role = Column(String(30), nullable=False, default="ANALYST")

    is_active = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
