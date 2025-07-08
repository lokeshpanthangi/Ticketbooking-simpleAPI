from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, or_
from typing import List, Dict, Any
from ..database import get_db
from ..models.venue import Venue
from ..models.event import Event
from ..models.booking import Booking
from ..models.ticket_type import TicketType

router = APIRouter(prefix="/stats", tags=["statistics"])


@router.get("/")
def get_system_stats(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Get comprehensive system statistics"""
    
    # Basic counts
    total_venues = db.query(Venue).count()
    total_events = db.query(Event).count()
    total_bookings = db.query(Booking).count()
    total_ticket_types = db.query(TicketType).count()
    
    # Revenue statistics
    total_revenue = db.query(func.sum(Booking.total_price)).filter(
        Booking.status == "confirmed"
    ).scalar() or 0
    
    pending_revenue = db.query(func.sum(Booking.total_price)).filter(
        Booking.status == "pending"
    ).scalar() or 0
    
    # Booking statistics by status
    booking_stats = db.query(
        Booking.status,
        func.count(Booking.id).label('count'),
        func.sum(Booking.total_price).label('revenue')
    ).group_by(Booking.status).all()
    
    booking_status_breakdown = {}
    for stat in booking_stats:
        booking_status_breakdown[stat.status.value] = {
            "count": stat.count,
            "revenue": round(stat.revenue or 0, 2)
        }
    
    # Total tickets sold
    total_tickets_sold = db.query(func.sum(Booking.quantity)).filter(
        Booking.status.in_(["pending", "confirmed"])
    ).scalar() or 0
    
    return {
        "overview": {
            "total_venues": total_venues,
            "total_events": total_events,
            "total_bookings": total_bookings,
            "total_ticket_types": total_ticket_types,
            "total_tickets_sold": total_tickets_sold
        },
        "revenue": {
            "total_revenue": round(total_revenue, 2),
            "pending_revenue": round(pending_revenue, 2),
            "confirmed_revenue": round(total_revenue, 2)
        },
        "booking_status_breakdown": booking_status_breakdown
    }


@router.get("/popular-events")
def get_popular_events(limit: int = 10, db: Session = Depends(get_db)):
    """Get most popular events by booking count"""
    popular_events = db.query(
        Event.id,
        Event.name,
        Venue.name.label('venue_name'),
        Venue.city.label('venue_city'),
        func.count(Booking.id).label('booking_count'),
        func.sum(Booking.quantity).label('total_tickets'),
        func.sum(Booking.total_price).label('total_revenue')
    ).join(Venue).outerjoin(Booking).filter(
        Booking.status.in_(["pending", "confirmed"])
    ).group_by(
        Event.id, Event.name, Venue.name, Venue.city
    ).order_by(
        desc('booking_count')
    ).limit(limit).all()
    
    result = []
    for event in popular_events:
        result.append({
            "event_id": event.id,
            "event_name": event.name,
            "venue_name": event.venue_name,
            "venue_city": event.venue_city,
            "booking_count": event.booking_count or 0,
            "total_tickets": event.total_tickets or 0,
            "total_revenue": round(event.total_revenue or 0, 2)
        })
    
    return result


@router.get("/busiest-venues")
def get_busiest_venues(limit: int = 10, db: Session = Depends(get_db)):
    """Get busiest venues by total bookings"""
    try:
        # First approach: Get venues with bookings
        busiest_venues = db.query(
            Venue.id,
            Venue.name,
            Venue.city,
            Venue.capacity,
            func.count(func.distinct(Event.id)).label('event_count'),
            func.count(func.distinct(Booking.id)).label('total_bookings'),
            func.sum(Booking.quantity).label('total_tickets'),
            func.sum(Booking.total_price).label('total_revenue')
        ).outerjoin(Event).outerjoin(Booking).filter(
            or_(Booking.status.in_(["pending", "confirmed"]), Booking.status.is_(None))
        ).group_by(
            Venue.id, Venue.name, Venue.city, Venue.capacity
        ).order_by(
            desc('total_bookings')
        ).limit(limit).all()
        
        # Fallback approach: If no results, get all venues
        if not busiest_venues:
            busiest_venues = db.query(
                Venue.id,
                Venue.name,
                Venue.city,
                Venue.capacity,
                func.count(func.distinct(Event.id)).label('event_count'),
                func.count(func.distinct(Booking.id)).label('total_bookings'),
                func.sum(Booking.quantity).label('total_tickets'),
                func.sum(Booking.total_price).label('total_revenue')
            ).outerjoin(Event).outerjoin(Booking).group_by(
                Venue.id, Venue.name, Venue.city, Venue.capacity
            ).order_by(
                desc('total_bookings')
            ).limit(limit).all()
    except Exception as e:
        # Final fallback: Return basic venue info
        busiest_venues = db.query(
            Venue.id,
            Venue.name,
            Venue.city,
            Venue.capacity
        ).limit(limit).all()
        
        # Convert to expected format
        result = []
        for venue in busiest_venues:
            result.append({
                "venue_id": venue.id,
                "venue_name": venue.name,
                "city": venue.city,
                "capacity": venue.capacity,
                "event_count": 0,
                "total_bookings": 0,
                "total_tickets": 0,
                "total_revenue": 0.0,
                "occupancy_rate": 0.0
            })
        return result
    
    result = []
    for venue in busiest_venues:
        occupancy_rate = 0
        if venue.capacity > 0 and venue.total_tickets:
            occupancy_rate = (venue.total_tickets / venue.capacity) * 100
        
        result.append({
            "venue_id": venue.id,
            "venue_name": venue.name,
            "city": venue.city,
            "capacity": venue.capacity,
            "event_count": venue.event_count or 0,
            "total_bookings": venue.total_bookings or 0,
            "total_tickets": venue.total_tickets or 0,
            "total_revenue": round(venue.total_revenue or 0, 2),
            "occupancy_rate": round(occupancy_rate, 2)
        })
    
    return result


@router.get("/ticket-type-analysis")
def get_ticket_type_analysis(db: Session = Depends(get_db)):
    """Analyze ticket type popularity and revenue"""
    ticket_analysis = db.query(
        TicketType.id,
        TicketType.name,
        TicketType.price,
        func.count(Booking.id).label('booking_count'),
        func.sum(Booking.quantity).label('tickets_sold'),
        func.sum(Booking.total_price).label('total_revenue')
    ).outerjoin(Booking).filter(
        Booking.status.in_(["pending", "confirmed"])
    ).group_by(
        TicketType.id, TicketType.name, TicketType.price
    ).order_by(
        desc('total_revenue')
    ).all()
    
    result = []
    total_tickets = sum(t.tickets_sold or 0 for t in ticket_analysis)
    total_revenue = sum(t.total_revenue or 0 for t in ticket_analysis)
    
    for ticket_type in ticket_analysis:
        tickets_sold = ticket_type.tickets_sold or 0
        revenue = ticket_type.total_revenue or 0
        
        market_share = (tickets_sold / total_tickets * 100) if total_tickets > 0 else 0
        revenue_share = (revenue / total_revenue * 100) if total_revenue > 0 else 0
        
        result.append({
            "ticket_type_id": ticket_type.id,
            "name": ticket_type.name.value,
            "price": ticket_type.price,
            "booking_count": ticket_type.booking_count or 0,
            "tickets_sold": tickets_sold,
            "total_revenue": round(revenue, 2),
            "market_share_percentage": round(market_share, 2),
            "revenue_share_percentage": round(revenue_share, 2)
        })
    
    return {
        "ticket_types": result,
        "summary": {
            "total_tickets_sold": total_tickets,
            "total_revenue": round(total_revenue, 2)
        }
    }


@router.get("/revenue-by-month")
def get_revenue_by_month(db: Session = Depends(get_db)):
    """Get revenue breakdown by month"""
    monthly_revenue = db.query(
        func.strftime('%Y-%m', Booking.booking_date).label('month'),
        func.count(Booking.id).label('booking_count'),
        func.sum(Booking.quantity).label('tickets_sold'),
        func.sum(Booking.total_price).label('revenue')
    ).filter(
        Booking.status.in_(["pending", "confirmed"])
    ).group_by(
        func.strftime('%Y-%m', Booking.booking_date)
    ).order_by('month').all()
    
    result = []
    for month_data in monthly_revenue:
        result.append({
            "month": month_data.month,
            "booking_count": month_data.booking_count,
            "tickets_sold": month_data.tickets_sold,
            "revenue": round(month_data.revenue, 2)
        })
    
    return result