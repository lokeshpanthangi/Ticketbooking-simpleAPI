import requests
import streamlit as st
from typing import Dict, List, Optional, Any
import json

# API Base URL
API_BASE_URL = "http://localhost:8000"


def handle_api_error(response: requests.Response) -> None:
    """Handle API errors and display appropriate messages"""
    if response.status_code >= 400:
        try:
            error_detail = response.json().get("detail", "Unknown error")
        except:
            error_detail = f"HTTP {response.status_code} Error"
        st.error(f"API Error: {error_detail}")
        return None


def make_request(method: str, endpoint: str, data: Optional[Dict] = None, params: Optional[Dict] = None) -> Optional[Any]:
    """Make HTTP request to API with error handling"""
    url = f"{API_BASE_URL}{endpoint}"
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, params=params)
        elif method.upper() == "POST":
            response = requests.post(url, json=data)
        elif method.upper() == "PUT":
            response = requests.put(url, json=data)
        elif method.upper() == "PATCH":
            response = requests.patch(url, json=data)
        elif method.upper() == "DELETE":
            response = requests.delete(url)
        else:
            st.error(f"Unsupported HTTP method: {method}")
            return None
        
        if response.status_code < 400:
            return response.json()
        else:
            handle_api_error(response)
            return None
            
    except requests.exceptions.ConnectionError:
        st.error("❌ Cannot connect to the backend API. Please ensure the FastAPI server is running on http://localhost:8000")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Request failed: {str(e)}")
        return None
    except json.JSONDecodeError:
        st.error("Invalid response format from API")
        return None


# Venue API functions
def get_venues() -> Optional[List[Dict]]:
    """Get all venues"""
    return make_request("GET", "/venues")


def create_venue(venue_data: Dict) -> Optional[Dict]:
    """Create a new venue"""
    return make_request("POST", "/venues", data=venue_data)


def get_venue(venue_id: int) -> Optional[Dict]:
    """Get specific venue details"""
    return make_request("GET", f"/venues/{venue_id}")


def get_venue_occupancy(venue_id: int) -> Optional[Dict]:
    """Get venue occupancy statistics"""
    return make_request("GET", f"/venues/{venue_id}/occupancy")


# Event API functions
def get_events() -> Optional[List[Dict]]:
    """Get all events"""
    return make_request("GET", "/events")


def create_event(event_data: Dict) -> Optional[Dict]:
    """Create a new event"""
    return make_request("POST", "/events", data=event_data)


def get_event(event_id: int) -> Optional[Dict]:
    """Get specific event details"""
    return make_request("GET", f"/events/{event_id}")


def get_event_revenue(event_id: int) -> Optional[Dict]:
    """Get event revenue statistics"""
    return make_request("GET", f"/events/{event_id}/revenue")


def get_available_tickets(event_id: int) -> Optional[Dict]:
    """Get available tickets for an event"""
    return make_request("GET", f"/events/{event_id}/available-tickets")


# Ticket Type API functions
def get_ticket_types() -> Optional[List[Dict]]:
    """Get all ticket types"""
    return make_request("GET", "/ticket-types")


def create_ticket_type(ticket_type_data: Dict) -> Optional[Dict]:
    """Create a new ticket type"""
    return make_request("POST", "/ticket-types", data=ticket_type_data)


def get_ticket_type_stats(type_id: int) -> Optional[Dict]:
    """Get ticket type statistics"""
    return make_request("GET", f"/ticket-types/{type_id}/stats")


# Booking API functions
def get_bookings() -> Optional[List[Dict]]:
    """Get all bookings"""
    return make_request("GET", "/bookings")


def create_booking(booking_data: Dict) -> Optional[Dict]:
    """Create a new booking"""
    return make_request("POST", "/bookings", data=booking_data)


def get_booking(booking_id: int) -> Optional[Dict]:
    """Get specific booking details"""
    return make_request("GET", f"/bookings/{booking_id}")


def update_booking_status(booking_id: int, status: str) -> Optional[Dict]:
    """Update booking status"""
    return make_request("PATCH", f"/bookings/{booking_id}/status", data={"status": status})


def cancel_booking(booking_id: int) -> Optional[Dict]:
    """Cancel a booking"""
    return make_request("DELETE", f"/bookings/{booking_id}")


def search_bookings(search_params: Dict) -> Optional[List[Dict]]:
    """Search bookings with filters"""
    return make_request("GET", "/bookings/search/", params=search_params)


# Statistics API functions
def get_stats() -> Optional[Dict]:
    """Get system statistics"""
    return make_request("GET", "/stats")


def get_popular_events(limit: int = 10) -> Optional[List[Dict]]:
    """Get popular events"""
    return make_request("GET", "/stats/popular-events", params={"limit": limit})


def get_busiest_venues(limit: int = 10) -> Optional[List[Dict]]:
    """Get busiest venues"""
    return make_request("GET", "/stats/busiest-venues", params={"limit": limit})


def get_ticket_type_analysis() -> Optional[Dict]:
    """Get ticket type analysis"""
    return make_request("GET", "/stats/ticket-type-analysis")


def get_revenue_by_month() -> Optional[List[Dict]]:
    """Get revenue by month"""
    return make_request("GET", "/stats/revenue-by-month")


# Health check
def check_api_health() -> bool:
    """Check if API is running"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False