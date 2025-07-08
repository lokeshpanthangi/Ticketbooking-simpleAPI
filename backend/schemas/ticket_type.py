from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional
from ..models.ticket_type import TicketTypeName


class TicketTypeCreate(BaseModel):
    name: TicketTypeName
    price: float = Field(..., gt=0, description="Price must be greater than 0")
    description: Optional[str] = Field(None, max_length=500)
    
    @validator('price')
    def validate_price(cls, v):
        if v <= 0:
            raise ValueError('Price must be greater than 0')
        return round(v, 2)  # Round to 2 decimal places


class TicketTypeResponse(BaseModel):
    id: int
    name: TicketTypeName
    price: float
    description: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True
        use_enum_values = True