
from sqlalchemy import (
    Column, String, DateTime, ForeignKey, Boolean, func
)
from backend.app.database import Base


class Device(Base):
    __tablename__ = "devices"

    device_id = Column(String(30), primary_key=True, index=True)

    customer_id = Column(
        String(20),
        ForeignKey("customers.customer_id"),
        nullable=False,
        index=True
    )

    device_type = Column(String(30), nullable=False)

    operating_system = Column(String(50), nullable=True)

    browser = Column(String(50), nullable=True)

    ip_address = Column(String(45), nullable=True)

    registered_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    is_trusted = Column(Boolean, nullable=False, default=False)

    is_active = Column(Boolean, nullable=False, default=True)
