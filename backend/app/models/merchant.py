
from sqlalchemy import Column, String, DateTime, Boolean, func
from backend.app.database import Base


class Merchant(Base):
    __tablename__ = "merchants"

    merchant_id = Column(String(20), primary_key=True, index=True)

    merchant_name = Column(String(150), nullable=False)

    merchant_category = Column(String(50), nullable=False)

    merchant_location = Column(String(100), nullable=True)

    country = Column(String(50), nullable=False, default="India")

    is_active = Column(Boolean, nullable=False, default=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )
