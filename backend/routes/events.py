from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from datetime import datetime
from ..database import get_db
from ..models.event import Event, EventStatus
from ..models.venue import Venue
from ..models.booking import Booking
from ..schemas.event import EventCreate, EventResponse, EventWithDetails
from ..schemas.booking import BookingResponse

router = APIRouter(prefix="/events", tags=["events"])


@router.post("/", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
def create_event(event: EventCreate, db: Session = Depends(get_db)):
    """Create a new event"""
    # Check if venue exists
    venue = db.query(Venue).filter(Venue.id == event.venue_id).first()
    if not venue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Venue not found"
        )
    
    # Validate event date is in the future
    if event.event_date <= datetime.now():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Event date must be in the future"
        )
    
    db_event = Event(**event.dict())
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event


@router.get("/", response_model=List[EventWithDetails])
def get_events(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all events with venue and booking info"""
    events = db.query(Event).join(Venue).offset(skip).limit(limit).all()
    
    result = []
    for event in events:
        # Get booking count and total bookings
        booking_stats = db.query(
            func.count(Booking.id).label('booking_count'),
            func.sum(Booking.quantity).label('total_bookings')
        ).filter(
            Booking.event_id == event.id,
            Booking.status.in_(["pending", "confirmed"])
        ).first()
        
        booking_count = booking_stats.booking_count or 0
        total_bookings = booking_stats.total_bookings or 0
        available_capacity = event.venue.capacity - total_bookings
        
        event_dict = {
            "id": event.id,
            "name": event.name,
            "description": event.description,
            "event_date": event.event_date,
            "venue_id": event.venue_id,
            "status": event.status,
            "created_at": event.created_at,
            "venue_name": event.venue.name,
            "venue_city": event.venue.city,
            "venue_capacity": event.venue.capacity,
            "booking_count": booking_count,
            "total_bookings": total_bookings,
            "available_capacity": available_capacity
        }
        result.append(event_dict)
    
    return result


@router.get("/{event_id}", response_model=EventWithDetails)
def get_event(event_id: int, db: Session = Depends(get_db)):
    """Get specific event details"""
    event = db.query(Event).join(Venue).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    # Get booking statistics
    booking_stats = db.query(
        func.count(Booking.id).label('booking_count'),
        func.sum(Booking.quantity).label('total_bookings')
    ).filter(
        Booking.event_id == event_id,
        Booking.status.in_(["pending", "confirmed"])
    ).first()
    
    booking_count = booking_stats.booking_count or 0
    total_bookings = booking_stats.total_bookings or 0
    available_capacity = event.venue.capacity - total_bookings
    
    event_dict = {
        "id": event.id,
        "name": event.name,
        "description": event.description,
        "event_date": event.event_date,
        "venue_id": event.venue_id,
        "status": event.status,
        "created_at": event.created_at,
        "venue_name": event.venue.name,
        "venue_city": event.venue.city,
        "venue_capacity": event.venue.capacity,
        "booking_count": booking_count,
        "total_bookings": total_bookings,
        "available_capacity": available_capacity
    }
    
    return event_dict


@router.get("/{event_id}/bookings", response_model=List[BookingResponse])
def get_event_bookings(event_id: int, db: Session = Depends(get_db)):
    """Get all bookings for an event"""
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    bookings = db.query(Booking).filter(Booking.event_id == event_id).all()
    return bookings


@router.get("/{event_id}/available-tickets")
def get_available_tickets(event_id: int, db: Session = Depends(get_db)):
    """Calculate available capacity for an event"""
    event = db.query(Event).join(Venue).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    # Calculate total booked tickets
    total_booked = db.query(func.sum(Booking.quantity)).filter(
        Booking.event_id == event_id,
        Booking.status.in_(["pending", "confirmed"])
    ).scalar() or 0
    
    available_capacity = event.venue.capacity - total_booked
    
    return {
        "event_id": event_id,
        "event_name": event.name,
        "venue_capacity": event.venue.capacity,
        "total_booked": total_booked,
        "available_capacity": available_capacity,
        "is_sold_out": available_capacity <= 0
    }


@router.get("/{event_id}/revenue")
def get_event_revenue(event_id: int, db: Session = Depends(get_db)):
    """Calculate total revenue for an event"""
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    # Calculate total revenue from confirmed bookings
    total_revenue = db.query(func.sum(Booking.total_price)).filter(
        Booking.event_id == event_id,
        Booking.status == "confirmed"
    ).scalar() or 0
    
    # Calculate pending revenue
    pending_revenue = db.query(func.sum(Booking.total_price)).filter(
        Booking.event_id == event_id,
        Booking.status == "pending"
    ).scalar() or 0
    
    # Get booking count by status
    booking_stats = db.query(
        Booking.status,
        func.count(Booking.id).label('count'),
        func.sum(Booking.total_price).label('revenue')
    ).filter(
        Booking.event_id == event_id
    ).group_by(Booking.status).all()
    
    status_breakdown = {}
    for stat in booking_stats:
        status_breakdown[stat.status.value] = {
            "count": stat.count,
            "revenue": stat.revenue or 0
        }
    
    return {
        "event_id": event_id,
        "event_name": event.name,
        "total_revenue": round(total_revenue, 2),
        "pending_revenue": round(pending_revenue, 2),
        "confirmed_revenue": round(total_revenue, 2),
        "status_breakdown": status_breakdown
    }