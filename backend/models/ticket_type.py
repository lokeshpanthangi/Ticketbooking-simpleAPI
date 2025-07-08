from sqlalchemy import Column, Integer, String, Float, DateTime, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from ..database import Base


class TicketTypeName(enum.Enum):
    VIP = "VIP"
    Standard = "Standard"
    Economy = "Economy"


class TicketType(Base):
    __tablename__ = "ticket_types"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(Enum(TicketTypeName), nullable=False, unique=True, index=True)
    price = Column(Float, nullable=False)
    description = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship to bookings
    bookings = relationship("Booking", back_populates="ticket_type")
    
    def __repr__(self):
        return f"<TicketType(id={self.id}, name='{self.name.value}', price={self.price})>"