from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional
from ..models.event import EventStatus


class EventCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    event_date: datetime = Field(..., description="Event date and time")
    venue_id: int = Field(..., gt=0)
    
    @validator('event_date')
    def validate_event_date(cls, v):
        if v <= datetime.now():
            raise ValueError('Event date must be in the future')
        return v


class EventResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    event_date: datetime
    venue_id: int
    status: EventStatus
    created_at: datetime
    
    class Config:
        from_attributes = True
        use_enum_values = True


class EventWithDetails(EventResponse):
    venue_name: Optional[str] = None
    venue_city: Optional[str] = None
    venue_capacity: Optional[int] = None
    booking_count: Optional[int] = 0
    total_bookings: Optional[int] = 0
    available_capacity: Optional[int] = None
    
    class Config:
        from_attributes = True
        use_enum_values = True