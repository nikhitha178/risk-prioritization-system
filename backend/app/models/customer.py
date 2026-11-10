
from sqlalchemy import Column, String, Date, DateTime, func
from backend.app.database import Base


class Customer(Base):
    __tablename__ = "customers"

    customer_id = Column(String(20), primary_key=True, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    date_of_birth = Column(Date, nullable=True)
    email = Column(String(150), unique=True, nullable=True)
    phone = Column(String(20), unique=True, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<Customer(customer_id={self.customer_id})>"
