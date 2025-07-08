from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from typing import List, Optional
from ..database import get_db
from ..models.booking import Booking, BookingStatus
from ..models.event import Event
from ..models.venue import Venue
from ..models.ticket_type import TicketType
from ..schemas.booking import BookingCreate, BookingResponse, BookingWithDetails, BookingStatusUpdate
from ..utils.helpers import generate_booking_code, validate_booking_data

router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.post("/", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
def create_booking(booking: BookingCreate, db: Session = Depends(get_db)):
    """Create a new booking"""
    # Validate booking data
    validation_result = validate_booking_data(
        db, booking.event_id, booking.ticket_type_id, booking.quantity
    )
    
    if not validation_result["valid"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=validation_result["message"]
        )
    
    # Generate unique booking code
    booking_code = generate_booking_code()
    
    # Ensure booking code is unique
    while db.query(Booking).filter(Booking.booking_code == booking_code).first():
        booking_code = generate_booking_code()
    
    # Create booking
    db_booking = Booking(
        booking_code=booking_code,
        customer_name=booking.customer_name,
        customer_email=booking.customer_email,
        event_id=booking.event_id,
        ticket_type_id=booking.ticket_type_id,
        quantity=booking.quantity,
        total_price=validation_result["total_price"]
    )
    
    db.add(db_booking)
    db.commit()
    db.refresh(db_booking)
    return db_booking


@router.get("/", response_model=List[BookingWithDetails])
def get_bookings(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all bookings with event and ticket type details"""
    bookings = db.query(Booking).join(Event).join(Venue).join(TicketType).offset(skip).limit(limit).all()
    
    result = []
    for booking in bookings:
        booking_dict = {
            "id": booking.id,
            "booking_code": booking.booking_code,
            "customer_name": booking.customer_name,
            "customer_email": booking.customer_email,
            "event_id": booking.event_id,
            "ticket_type_id": booking.ticket_type_id,
            "quantity": booking.quantity,
            "total_price": booking.total_price,
            "status": booking.status,
            "booking_date": booking.booking_date,
            "event_name": booking.event.name,
            "event_date": booking.event.event_date,
            "venue_name": booking.event.venue.name,
            "venue_city": booking.event.venue.city,
            "ticket_type_name": booking.ticket_type.name.value,
            "ticket_type_price": booking.ticket_type.price
        }
        result.append(booking_dict)
    
    return result


@router.get("/{booking_id}", response_model=BookingWithDetails)
def get_booking(booking_id: int, db: Session = Depends(get_db)):
    """Get specific booking details"""
    booking = db.query(Booking).join(Event).join(Venue).join(TicketType).filter(
        Booking.id == booking_id
    ).first()
    
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )
    
    booking_dict = {
        "id": booking.id,
        "booking_code": booking.booking_code,
        "customer_name": booking.customer_name,
        "customer_email": booking.customer_email,
        "event_id": booking.event_id,
        "ticket_type_id": booking.ticket_type_id,
        "quantity": booking.quantity,
        "total_price": booking.total_price,
        "status": booking.status,
        "booking_date": booking.booking_date,
        "event_name": booking.event.name,
        "event_date": booking.event.event_date,
        "venue_name": booking.event.venue.name,
        "venue_city": booking.event.venue.city,
        "ticket_type_name": booking.ticket_type.name.value,
        "ticket_type_price": booking.ticket_type.price
    }
    
    return booking_dict


@router.put("/{booking_id}", response_model=BookingResponse)
def update_booking(booking_id: int, booking_update: BookingCreate, db: Session = Depends(get_db)):
    """Update booking details"""
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )
    
    # Validate new booking data
    validation_result = validate_booking_data(
        db, booking_update.event_id, booking_update.ticket_type_id, booking_update.quantity
    )
    
    if not validation_result["valid"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=validation_result["message"]
        )
    
    # Update booking
    booking.customer_name = booking_update.customer_name
    booking.customer_email = booking_update.customer_email
    booking.event_id = booking_update.event_id
    booking.ticket_type_id = booking_update.ticket_type_id
    booking.quantity = booking_update.quantity
    booking.total_price = validation_result["total_price"]
    
    db.commit()
    db.refresh(booking)
    return booking


@router.delete("/{booking_id}")
def cancel_booking(booking_id: int, db: Session = Depends(get_db)):
    """Cancel a booking (soft delete by changing status)"""
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )
    
    booking.status = BookingStatus.cancelled
    db.commit()
    
    return {"message": "Booking cancelled successfully", "booking_id": booking_id}


@router.patch("/{booking_id}/status", response_model=BookingResponse)
def update_booking_status(booking_id: int, status_update: BookingStatusUpdate, db: Session = Depends(get_db)):
    """Update booking status only"""
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )
    
    booking.status = status_update.status
    db.commit()
    db.refresh(booking)
    return booking


@router.get("/search/", response_model=List[BookingWithDetails])
def search_bookings(
    q: Optional[str] = Query(None, description="Search query for event name, venue, customer name, or booking code"),
    event_name: Optional[str] = Query(None, description="Filter by event name"),
    venue_name: Optional[str] = Query(None, description="Filter by venue name"),
    ticket_type: Optional[str] = Query(None, description="Filter by ticket type"),
    status: Optional[BookingStatus] = Query(None, description="Filter by booking status"),
    customer_email: Optional[str] = Query(None, description="Filter by customer email"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Search bookings with multiple criteria"""
    query = db.query(Booking).join(Event).join(Venue).join(TicketType)
    
    # General search query
    if q:
        query = query.filter(
            or_(
                Event.name.ilike(f"%{q}%"),
                Venue.name.ilike(f"%{q}%"),
                Booking.customer_name.ilike(f"%{q}%"),
                Booking.booking_code.ilike(f"%{q}%")
            )
        )
    
    # Specific filters
    if event_name:
        query = query.filter(Event.name.ilike(f"%{event_name}%"))
    
    if venue_name:
        query = query.filter(Venue.name.ilike(f"%{venue_name}%"))
    
    if ticket_type:
        query = query.filter(TicketType.name == ticket_type)
    
    if status:
        query = query.filter(Booking.status == status)
    
    if customer_email:
        query = query.filter(Booking.customer_email.ilike(f"%{customer_email}%"))
    
    bookings = query.offset(skip).limit(limit).all()
    
    result = []
    for booking in bookings:
        booking_dict = {
            "id": booking.id,
            "booking_code": booking.booking_code,
            "customer_name": booking.customer_name,
            "customer_email": booking.customer_email,
            "event_id": booking.event_id,
            "ticket_type_id": booking.ticket_type_id,
            "quantity": booking.quantity,
            "total_price": booking.total_price,
            "status": booking.status,
            "booking_date": booking.booking_date,
            "event_name": booking.event.name,
            "event_date": booking.event.event_date,
            "venue_name": booking.event.venue.name,
            "venue_city": booking.event.venue.city,
            "ticket_type_name": booking.ticket_type.name.value,
            "ticket_type_price": booking.ticket_type.price
        }
        result.append(booking_dict)
    
    return result