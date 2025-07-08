import random
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..models.booking import Booking
from ..models.event import Event, EventStatus
from ..models.venue import Venue
from ..models.ticket_type import TicketType
from typing import Optional


def generate_booking_code() -> str:
    """Generate unique booking code in format BK-YYYYMMDD-XXXX"""
    date_str = datetime.now().strftime("%Y%m%d")
    random_str = str(random.randint(1000, 9999))
    return f"BK-{date_str}-{random_str}"


def check_venue_capacity(db: Session, event_id: int, requested_quantity: int) -> dict:
    """Check if venue has enough capacity for the booking"""
    # Get event with venue information
    event = db.query(Event).join(Venue).filter(Event.id == event_id).first()
    
    if not event:
        return {"valid": False, "message": "Event not found"}
    
    # Calculate total existing bookings for this event
    total_booked = db.query(func.sum(Booking.quantity)).filter(
        Booking.event_id == event_id,
        Booking.status.in_(["pending", "confirmed"])
    ).scalar() or 0
    
    # Check if there's enough capacity
    available_capacity = event.venue.capacity - total_booked
    
    if requested_quantity > available_capacity:
        return {
            "valid": False, 
            "message": f"Not enough capacity. Available: {available_capacity}, Requested: {requested_quantity}",
            "available_capacity": available_capacity,
            "venue_capacity": event.venue.capacity,
            "total_booked": total_booked
        }
    
    return {
        "valid": True, 
        "message": "Capacity available",
        "available_capacity": available_capacity,
        "venue_capacity": event.venue.capacity,
        "total_booked": total_booked
    }


def calculate_total_price(db: Session, ticket_type_id: int, quantity: int) -> Optional[float]:
    """Calculate total price for booking"""
    ticket_type = db.query(TicketType).filter(TicketType.id == ticket_type_id).first()
    
    if not ticket_type:
        return None
    
    return round(ticket_type.price * quantity, 2)


def validate_booking_data(db: Session, event_id: int, ticket_type_id: int, quantity: int) -> dict:
    """Validate all booking data before creating booking"""
    # Check if event exists and is active
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        return {"valid": False, "message": "Event not found"}
    
    if event.status != EventStatus.active:
        return {"valid": False, "message": f"Event is {event.status.value}, cannot book tickets"}
    
    # Check if event date is in the future
    if event.event_date <= datetime.now():
        return {"valid": False, "message": "Cannot book tickets for past events"}
    
    # Check if ticket type exists
    ticket_type = db.query(TicketType).filter(TicketType.id == ticket_type_id).first()
    if not ticket_type:
        return {"valid": False, "message": "Ticket type not found"}
    
    # Check venue capacity
    capacity_check = check_venue_capacity(db, event_id, quantity)
    if not capacity_check["valid"]:
        return capacity_check
    
    # Calculate total price
    total_price = calculate_total_price(db, ticket_type_id, quantity)
    if total_price is None:
        return {"valid": False, "message": "Could not calculate total price"}
    
    return {
        "valid": True, 
        "message": "Booking data is valid",
        "total_price": total_price,
        "capacity_info": capacity_check
    }