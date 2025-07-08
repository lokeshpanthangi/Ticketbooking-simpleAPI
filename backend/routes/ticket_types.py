from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from ..database import get_db
from ..models.ticket_type import TicketType, TicketTypeName
from ..models.booking import Booking
from ..schemas.ticket_type import TicketTypeCreate, TicketTypeResponse
from ..schemas.booking import BookingResponse

router = APIRouter(prefix="/ticket-types", tags=["ticket-types"])


@router.post("/", response_model=TicketTypeResponse, status_code=status.HTTP_201_CREATED)
def create_ticket_type(ticket_type: TicketTypeCreate, db: Session = Depends(get_db)):
    """Create a new ticket type"""
    # Check if ticket type name already exists
    existing_ticket_type = db.query(TicketType).filter(
        TicketType.name == ticket_type.name
    ).first()
    
    if existing_ticket_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ticket type '{ticket_type.name.value}' already exists"
        )
    
    db_ticket_type = TicketType(**ticket_type.dict())
    db.add(db_ticket_type)
    db.commit()
    db.refresh(db_ticket_type)
    return db_ticket_type


@router.get("/", response_model=List[TicketTypeResponse])
def get_ticket_types(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all ticket types"""
    ticket_types = db.query(TicketType).offset(skip).limit(limit).all()
    return ticket_types


@router.get("/{type_id}", response_model=TicketTypeResponse)
def get_ticket_type(type_id: int, db: Session = Depends(get_db)):
    """Get specific ticket type"""
    ticket_type = db.query(TicketType).filter(TicketType.id == type_id).first()
    if not ticket_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket type not found"
        )
    return ticket_type


@router.get("/{type_id}/bookings", response_model=List[BookingResponse])
def get_ticket_type_bookings(type_id: int, db: Session = Depends(get_db)):
    """Get all bookings for a specific ticket type"""
    ticket_type = db.query(TicketType).filter(TicketType.id == type_id).first()
    if not ticket_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket type not found"
        )
    
    bookings = db.query(Booking).filter(Booking.ticket_type_id == type_id).all()
    return bookings


@router.get("/{type_id}/stats")
def get_ticket_type_stats(type_id: int, db: Session = Depends(get_db)):
    """Get statistics for a specific ticket type"""
    ticket_type = db.query(TicketType).filter(TicketType.id == type_id).first()
    if not ticket_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket type not found"
        )
    
    # Get booking statistics
    booking_stats = db.query(
        func.count(Booking.id).label('total_bookings'),
        func.sum(Booking.quantity).label('total_tickets_sold'),
        func.sum(Booking.total_price).label('total_revenue')
    ).filter(
        Booking.ticket_type_id == type_id,
        Booking.status.in_(["pending", "confirmed"])
    ).first()
    
    # Get booking count by status
    status_stats = db.query(
        Booking.status,
        func.count(Booking.id).label('count'),
        func.sum(Booking.quantity).label('tickets'),
        func.sum(Booking.total_price).label('revenue')
    ).filter(
        Booking.ticket_type_id == type_id
    ).group_by(Booking.status).all()
    
    status_breakdown = {}
    for stat in status_stats:
        status_breakdown[stat.status.value] = {
            "booking_count": stat.count,
            "tickets_sold": stat.tickets or 0,
            "revenue": stat.revenue or 0
        }
    
    return {
        "ticket_type_id": type_id,
        "ticket_type_name": ticket_type.name.value,
        "price": ticket_type.price,
        "total_bookings": booking_stats.total_bookings or 0,
        "total_tickets_sold": booking_stats.total_tickets_sold or 0,
        "total_revenue": round(booking_stats.total_revenue or 0, 2),
        "status_breakdown": status_breakdown
    }


@router.put("/{type_id}", response_model=TicketTypeResponse)
def update_ticket_type(type_id: int, ticket_type_update: TicketTypeCreate, db: Session = Depends(get_db)):
    """Update a ticket type"""
    ticket_type = db.query(TicketType).filter(TicketType.id == type_id).first()
    if not ticket_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket type not found"
        )
    
    # Check if new name conflicts with existing ticket type (excluding current one)
    if ticket_type_update.name != ticket_type.name:
        existing_ticket_type = db.query(TicketType).filter(
            TicketType.name == ticket_type_update.name,
            TicketType.id != type_id
        ).first()
        
        if existing_ticket_type:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ticket type '{ticket_type_update.name.value}' already exists"
            )
    
    # Update ticket type
    for field, value in ticket_type_update.dict().items():
        setattr(ticket_type, field, value)
    
    db.commit()
    db.refresh(ticket_type)
    return ticket_type