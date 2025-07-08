from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import List, Optional


class VenueCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    address: str = Field(..., min_length=1, max_length=500)
    city: str = Field(..., min_length=1, max_length=100)
    capacity: int = Field(..., gt=0, description="Venue capacity must be greater than 0")
    
    @validator('capacity')
    def validate_capacity(cls, v):
        if v <= 0:
            raise ValueError('Capacity must be greater than 0')
        return v


class VenueResponse(BaseModel):
    id: int
    name: str
    address: str
    city: str
    capacity: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class VenueWithEvents(VenueResponse):
    events: List['EventResponse'] = []
    event_count: Optional[int] = 0
    
    class Config:
        from_attributes = True


# Forward reference resolution
from .event import EventResponse
VenueWithEvents.model_rebuild()