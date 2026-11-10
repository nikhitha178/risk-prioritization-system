
from sqlalchemy import (
    Column, String, Date, DateTime,
    ForeignKey, Text, func
)
from backend.app.database import Base


class KYCProfile(Base):
    __tablename__ = "kyc_profiles"

    kyc_id = Column(String(30), primary_key=True)

    customer_id = Column(
        String(20),
        ForeignKey("customers.customer_id"),
        nullable=False,
        index=True
    )

    verification_status = Column(
        String(30),
        nullable=False,
        default="PENDING"
    )

    document_type = Column(String(50), nullable=True)

    verified_at = Column(DateTime(timezone=True), nullable=True)

    expiry_date = Column(Date, nullable=True)

    remarks = Column(Text, nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )
