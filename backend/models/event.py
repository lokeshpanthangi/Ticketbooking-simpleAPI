from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from ..database import Base


class EventStatus(enum.Enum):
    active = "active"
    cancelled = "cancelled"
    completed = "completed"


class Event(Base):
    __tablename__ = "events"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    description = Column(String)
    event_date = Column(DateTime(timezone=True), nullable=False, index=True)
    venue_id = Column(Integer, ForeignKey("venues.id"), nullable=False)
    status = Column(Enum(EventStatus), default=EventStatus.active, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    venue = relationship("Venue", back_populates="events")
    bookings = relationship("Booking", back_populates="event", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Event(id={self.id}, name='{self.name}', date='{self.event_date}', status='{self.status.value}')>"