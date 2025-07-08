from pydantic import BaseModel, Field, validator, EmailStr
from datetime import datetime
from typing import Optional
from ..models.booking import BookingStatus


class BookingCreate(BaseModel):
    customer_name: str = Field(..., min_length=1, max_length=100)
    customer_email: EmailStr
    event_id: int = Field(..., gt=0)
    ticket_type_id: int = Field(..., gt=0)
    quantity: int = Field(default=1, ge=1, le=10, description="Quantity must be between 1 and 10")
    
    @validator('quantity')
    def validate_quantity(cls, v):
        if v < 1 or v > 10:
            raise ValueError('Quantity must be between 1 and 10')
        return v


class BookingResponse(BaseModel):
    id: int
    booking_code: str
    customer_name: str
    customer_email: str
    event_id: int
    ticket_type_id: int
    quantity: int
    total_price: float
    status: BookingStatus
    booking_date: datetime
    
    class Config:
        from_attributes = True
        use_enum_values = True


class BookingWithDetails(BookingResponse):
    event_name: Optional[str] = None
    event_date: Optional[datetime] = None
    venue_name: Optional[str] = None
    venue_city: Optional[str] = None
    ticket_type_name: Optional[str] = None
    ticket_type_price: Optional[float] = None
    
    class Config:
        from_attributes = True
        use_enum_values = True


class BookingStatusUpdate(BaseModel):
    status: BookingStatus
    
    class Config:
        use_enum_values = True