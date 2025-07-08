from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from ..database import get_db
from ..models.venue import Venue
from ..models.event import Event
from ..models.booking import Booking
from ..schemas.venue import VenueCreate, VenueResponse, VenueWithEvents
from ..schemas.event import EventResponse

router = APIRouter(prefix="/venues", tags=["venues"])


@router.post("/", response_model=VenueResponse, status_code=status.HTTP_201_CREATED)
def create_venue(venue: VenueCreate, db: Session = Depends(get_db)):
    """Create a new venue"""
    # Check if venue name already exists
    existing_venue = db.query(Venue).filter(Venue.name == venue.name).first()
    if existing_venue:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Venue with this name already exists"
        )
    
    db_venue = Venue(**venue.dict())
    db.add(db_venue)
    db.commit()
    db.refresh(db_venue)
    return db_venue


@router.get("/", response_model=List[VenueWithEvents])
def get_venues(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all venues with event counts"""
    venues = db.query(Venue).offset(skip).limit(limit).all()
    
    result = []
    for venue in venues:
        venue_dict = {
            "id": venue.id,
            "name": venue.name,
            "address": venue.address,
            "city": venue.city,
            "capacity": venue.capacity,
            "created_at": venue.created_at,
            "events": venue.events,
            "event_count": len(venue.events)
        }
        result.append(venue_dict)
    
    return result


@router.get("/{venue_id}", response_model=VenueWithEvents)
def get_venue(venue_id: int, db: Session = Depends(get_db)):
    """Get specific venue details"""
    venue = db.query(Venue).filter(Venue.id == venue_id).first()
    if not venue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Venue not found"
        )
    
    venue_dict = {
        "id": venue.id,
        "name": venue.name,
        "address": venue.address,
        "city": venue.city,
        "capacity": venue.capacity,
        "created_at": venue.created_at,
        "events": venue.events,
        "event_count": len(venue.events)
    }
    
    return venue_dict


@router.get("/{venue_id}/events", response_model=List[EventResponse])
def get_venue_events(venue_id: int, db: Session = Depends(get_db)):
    """Get all events at a specific venue"""
    venue = db.query(Venue).filter(Venue.id == venue_id).first()
    if not venue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Venue not found"
        )
    
    events = db.query(Event).filter(Event.venue_id == venue_id).all()
    return events


@router.get("/{venue_id}/occupancy")
def get_venue_occupancy(venue_id: int, db: Session = Depends(get_db)):
    """Calculate occupancy stats for a venue"""
    venue = db.query(Venue).filter(Venue.id == venue_id).first()
    if not venue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Venue not found"
        )
    
    # Get total bookings for all events at this venue
    total_bookings = db.query(func.sum(Booking.quantity)).join(Event).filter(
        Event.venue_id == venue_id,
        Booking.status.in_(["pending", "confirmed"])
    ).scalar() or 0
    
    # Get number of events
    event_count = db.query(Event).filter(Event.venue_id == venue_id).count()
    
    # Calculate occupancy percentage
    if venue.capacity > 0:
        occupancy_percentage = (total_bookings / venue.capacity) * 100
    else:
        occupancy_percentage = 0
    
    return {
        "venue_id": venue_id,
        "venue_name": venue.name,
        "capacity": venue.capacity,
        "total_bookings": total_bookings,
        "available_capacity": venue.capacity - total_bookings,
        "occupancy_percentage": round(occupancy_percentage, 2),
        "event_count": event_count
    }