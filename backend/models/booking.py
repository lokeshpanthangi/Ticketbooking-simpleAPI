from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
import random
from datetime import datetime
from ..database import Base


class BookingStatus(enum.Enum):
    pending = "pending"
    confirmed = "confirmed"
    cancelled = "cancelled"


class Booking(Base):
    __tablename__ = "bookings"
    
    id = Column(Integer, primary_key=True, index=True)
    booking_code = Column(String, unique=True, nullable=False, index=True)
    customer_name = Column(String, nullable=False)
    customer_email = Column(String, nullable=False, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    ticket_type_id = Column(Integer, ForeignKey("ticket_types.id"), nullable=False)
    quantity = Column(Integer, default=1, nullable=False)
    total_price = Column(Float, nullable=False)
    status = Column(Enum(BookingStatus), default=BookingStatus.pending, nullable=False)
    booking_date = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    event = relationship("Event", back_populates="bookings")
    ticket_type = relationship("TicketType", back_populates="bookings")
    
    def __repr__(self):
        return f"<Booking(id={self.id}, code='{self.booking_code}', customer='{self.customer_name}', status='{self.status.value}')>"
    
    @staticmethod
    def generate_booking_code():
        """Generate unique booking code in format BK-YYYYMMDD-XXXX"""
        date_str = datetime.now().strftime("%Y%m%d")
        random_str = str(random.randint(1000, 9999))
        return f"BK-{date_str}-{random_str}"