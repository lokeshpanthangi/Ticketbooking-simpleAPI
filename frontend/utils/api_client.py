import requests
import streamlit as st
from typing import Dict, List, Optional, Any
import json
import time
import random
from functools import wraps
from datetime import datetime, timedelta

# API Base URL
API_BASE_URL = "http://localhost:8000"

# Circuit breaker state
class CircuitBreaker:
    def __init__(self, failure_threshold=5, recovery_timeout=60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
    
    def call(self, func, *args, **kwargs):
        if self.state == 'OPEN':
            if datetime.now() - self.last_failure_time > timedelta(seconds=self.recovery_timeout):
                self.state = 'HALF_OPEN'
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = func(*args, **kwargs)
            if self.state == 'HALF_OPEN':
                self.state = 'CLOSED'
                self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = datetime.now()
            if self.failure_count >= self.failure_threshold:
                self.state = 'OPEN'
            raise e

# Global circuit breaker instance
circuit_breaker = CircuitBreaker()

# Cache for API responses
api_cache = {}
CACHE_DURATION = 30  # seconds

def with_cache(cache_key_func):
    """Decorator to add caching to API calls"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = cache_key_func(*args, **kwargs)
            now = time.time()
            
            # Check cache
            if cache_key in api_cache:
                cached_data, timestamp = api_cache[cache_key]
                if now - timestamp < CACHE_DURATION:
                    return cached_data
            
            # Call function and cache result
            result = func(*args, **kwargs)
            if result is not None:
                api_cache[cache_key] = (result, now)
            return result
        return wrapper
    return decorator

def retry_with_backoff(max_retries=3, base_delay=1, max_delay=10):
    """Decorator for exponential backoff retry logic"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries + 1):
                try:
                    return circuit_breaker.call(func, *args, **kwargs)
                except Exception as e:
                    if attempt == max_retries:
                        raise e
                    
                    # Calculate delay with jitter
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    jitter = random.uniform(0.1, 0.3) * delay
                    time.sleep(delay + jitter)
                    
                    st.warning(f"Retrying API call... (attempt {attempt + 2}/{max_retries + 1})")
            return None
        return wrapper
    return decorator


def handle_api_error(response: requests.Response, show_error: bool = True) -> None:
    """Handle API errors and display appropriate messages"""
    if response.status_code >= 400:
        try:
            error_detail = response.json().get("detail", "Unknown error")
        except:
            error_detail = f"HTTP {response.status_code} Error"
        
        if show_error:
            if response.status_code >= 500:
                st.error(f"🔧 Server Error: {error_detail}. Trying fallback methods...")
            elif response.status_code >= 400:
                st.warning(f"⚠️ Client Error: {error_detail}")
        return None


def make_request_raw(method: str, endpoint: str, data: Optional[Dict] = None, params: Optional[Dict] = None, timeout: int = 10) -> requests.Response:
    """Raw HTTP request without error handling for internal use"""
    url = f"{API_BASE_URL}{endpoint}"
    
    if method.upper() == "GET":
        return requests.get(url, params=params, timeout=timeout)
    elif method.upper() == "POST":
        return requests.post(url, json=data, timeout=timeout)
    elif method.upper() == "PUT":
        return requests.put(url, json=data, timeout=timeout)
    elif method.upper() == "PATCH":
        return requests.patch(url, json=data, timeout=timeout)
    elif method.upper() == "DELETE":
        return requests.delete(url, timeout=timeout)
    else:
        raise ValueError(f"Unsupported HTTP method: {method}")


@retry_with_backoff(max_retries=3)
def make_request(method: str, endpoint: str, data: Optional[Dict] = None, params: Optional[Dict] = None, use_fallback: bool = True) -> Optional[Any]:
    """Make HTTP request to API with comprehensive error handling and fallbacks"""
    try:
        response = make_request_raw(method, endpoint, data, params)
        
        if response.status_code < 400:
            return response.json()
        else:
            handle_api_error(response, show_error=not use_fallback)
            
            # Try fallback strategies for GET requests
            if use_fallback and method.upper() == "GET":
                return try_fallback_strategies(endpoint, params)
            return None
            
    except requests.exceptions.ConnectionError:
        if use_fallback:
            st.warning("🔄 Connection failed, trying fallback strategies...")
            return try_fallback_strategies(endpoint, params) if method.upper() == "GET" else None
        else:
            st.error("❌ Cannot connect to the backend API. Please ensure the FastAPI server is running on http://localhost:8000")
            return None
    except requests.exceptions.Timeout:
        st.warning("⏱️ Request timed out, retrying with longer timeout...")
        raise  # Let retry decorator handle this
    except requests.exceptions.RequestException as e:
        st.error(f"Request failed: {str(e)}")
        return None
    except json.JSONDecodeError:
        st.error("Invalid response format from API")
        return None
    except Exception as e:
        if "Circuit breaker is OPEN" in str(e):
            st.error("🚫 API temporarily unavailable. Please try again in a few minutes.")
            return try_fallback_strategies(endpoint, params) if method.upper() == "GET" else None
        raise


def try_fallback_strategies(endpoint: str, params: Optional[Dict] = None) -> Optional[Any]:
    """Try multiple fallback strategies when primary API fails"""
    # Strategy 1: Return cached data if available
    cache_key = f"{endpoint}_{str(params) if params else 'no_params'}"
    if cache_key in api_cache:
        cached_data, _ = api_cache[cache_key]
        st.info("📋 Showing cached data due to API unavailability")
        return cached_data
    
    # Strategy 2: Return mock/default data for critical endpoints
    fallback_data = get_fallback_data(endpoint)
    if fallback_data:
        st.info("🔧 Showing default data due to API unavailability")
        return fallback_data
    
    # Strategy 3: Return empty but valid structure
    return get_empty_response_structure(endpoint)


def get_fallback_data(endpoint: str) -> Optional[Any]:
    """Return fallback data for critical endpoints"""
    fallback_map = {
        "/venues": [],
        "/events": [],
        "/bookings": [],
        "/ticket-types": [],
        "/stats": {
            "overview": {
                "total_venues": 0,
                "total_events": 0,
                "total_bookings": 0,
                "total_ticket_types": 0,
                "total_tickets_sold": 0
            },
            "revenue": {
                "total_revenue": 0.0,
                "pending_revenue": 0.0,
                "confirmed_revenue": 0.0
            },
            "booking_status_breakdown": {}
        },
        "/stats/busiest-venues": [],
        "/stats/popular-events": [],
        "/stats/ticket-type-analysis": {"ticket_types": [], "summary": {"total_tickets_sold": 0, "total_revenue": 0.0}},
        "/stats/revenue-by-month": []
    }
    
    return fallback_map.get(endpoint)


def get_empty_response_structure(endpoint: str) -> Optional[Any]:
    """Return appropriate empty structure based on endpoint"""
    if "/stats/" in endpoint or endpoint == "/stats":
        return get_fallback_data(endpoint)
    elif endpoint.endswith("s"):  # Plural endpoints typically return lists
        return []
    else:
        return None


# Venue API functions
@with_cache(lambda: "venues")
def get_venues() -> Optional[List[Dict]]:
    """Get all venues with caching"""
    return make_request("GET", "/venues")


def create_venue(venue_data: Dict) -> Optional[Dict]:
    """Create a new venue"""
    # Clear venues cache after creation
    if "venues" in api_cache:
        del api_cache["venues"]
    return make_request("POST", "/venues", data=venue_data, use_fallback=False)


@with_cache(lambda venue_id: f"venue_{venue_id}")
def get_venue(venue_id: int) -> Optional[Dict]:
    """Get specific venue details with caching"""
    return make_request("GET", f"/venues/{venue_id}")


@with_cache(lambda venue_id: f"venue_occupancy_{venue_id}")
def get_venue_occupancy(venue_id: int) -> Optional[Dict]:
    """Get venue occupancy statistics with caching"""
    result = make_request("GET", f"/venues/{venue_id}/occupancy")
    if result is None:
        # Fallback: return basic structure
        return {
            "total_capacity": 0,
            "total_bookings": 0,
            "occupancy_rate": 0.0,
            "available_capacity": 0
        }
    return result


@with_cache(lambda venue_id: f"venue_events_{venue_id}")
def get_venue_events(venue_id: int) -> Optional[List[Dict]]:
    """Get all events at a specific venue with caching"""
    result = make_request("GET", f"/venues/{venue_id}/events")
    if result is None:
        return []
    return result


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


def update_ticket_type(type_id: int, ticket_type_data: Dict) -> Optional[Dict]:
    """Update an existing ticket type"""
    return make_request("PUT", f"/ticket-types/{type_id}", data=ticket_type_data)


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


# Statistics API functions with enhanced error handling
@with_cache(lambda: "stats")
def get_stats() -> Optional[Dict]:
    """Get system statistics with caching and fallback"""
    result = make_request("GET", "/stats")
    if result is None:
        return get_fallback_data("/stats")
    return result


@with_cache(lambda limit=10: f"popular_events_{limit}")
def get_popular_events(limit: int = 10) -> Optional[List[Dict]]:
    """Get popular events with caching and fallback"""
    result = make_request("GET", "/stats/popular-events", params={"limit": limit})
    if result is None:
        return []
    return result


@with_cache(lambda limit=10: f"busiest_venues_{limit}")
def get_busiest_venues(limit: int = 10) -> Optional[List[Dict]]:
    """Get busiest venues with enhanced error handling and fallback"""
    result = make_request("GET", "/stats/busiest-venues", params={"limit": limit})
    if result is None:
        # Try alternative approach: get basic venue list
        venues = get_venues()
        if venues:
            return [{
                "venue_id": venue.get("id", 0),
                "venue_name": venue.get("name", "Unknown"),
                "city": venue.get("city", "Unknown"),
                "capacity": venue.get("capacity", 0),
                "event_count": 0,
                "total_bookings": 0,
                "total_tickets": 0,
                "total_revenue": 0.0,
                "occupancy_rate": 0.0
            } for venue in venues[:limit]]
        return []
    return result


@with_cache(lambda: "ticket_type_analysis")
def get_ticket_type_analysis() -> Optional[Dict]:
    """Get ticket type analysis with caching and fallback"""
    result = make_request("GET", "/stats/ticket-type-analysis")
    if result is None:
        return get_fallback_data("/stats/ticket-type-analysis")
    return result


@with_cache(lambda: "revenue_by_month")
def get_revenue_by_month() -> Optional[List[Dict]]:
    """Get revenue by month with caching and fallback"""
    result = make_request("GET", "/stats/revenue-by-month")
    if result is None:
        return []
    return result


# Health check and monitoring
def check_api_health() -> Dict[str, Any]:
    """Comprehensive API health check with detailed status"""
    health_status = {
        "is_healthy": False,
        "response_time": None,
        "status_code": None,
        "error": None,
        "endpoints_status": {}
    }
    
    try:
        start_time = time.time()
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        response_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        health_status.update({
            "is_healthy": response.status_code == 200,
            "response_time": round(response_time, 2),
            "status_code": response.status_code
        })
        
        # Test critical endpoints
        critical_endpoints = ["/venues", "/events", "/stats"]
        for endpoint in critical_endpoints:
            try:
                test_response = requests.get(f"{API_BASE_URL}{endpoint}", timeout=3)
                health_status["endpoints_status"][endpoint] = {
                    "status": "healthy" if test_response.status_code < 500 else "unhealthy",
                    "status_code": test_response.status_code
                }
            except Exception as e:
                health_status["endpoints_status"][endpoint] = {
                    "status": "error",
                    "error": str(e)
                }
        
    except requests.exceptions.ConnectionError:
        health_status["error"] = "Connection refused - API server may be down"
    except requests.exceptions.Timeout:
        health_status["error"] = "Request timeout - API server is slow"
    except Exception as e:
        health_status["error"] = str(e)
    
    return health_status


def display_api_status():
    """Display API status in Streamlit sidebar"""
    health = check_api_health()
    
    with st.sidebar:
        st.markdown("### 🔧 API Status")
        
        if health["is_healthy"]:
            st.success(f"✅ API Online ({health['response_time']}ms)")
        else:
            st.error(f"❌ API Offline")
            if health["error"]:
                st.error(f"Error: {health['error']}")
        
        # Show circuit breaker status
        if circuit_breaker.state != 'CLOSED':
            st.warning(f"⚠️ Circuit Breaker: {circuit_breaker.state}")
            if circuit_breaker.state == 'OPEN':
                st.info("API calls are temporarily blocked. Showing cached/fallback data.")
        
        # Show cache status
        if api_cache:
            st.info(f"📋 {len(api_cache)} items cached")
            if st.button("Clear Cache"):
                api_cache.clear()
                st.rerun()


def clear_all_caches():
    """Clear all API caches"""
    global api_cache
    api_cache.clear()
    

def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics"""
    return {
        "total_items": len(api_cache),
        "cache_keys": list(api_cache.keys()),
        "circuit_breaker_state": circuit_breaker.state,
        "failure_count": circuit_breaker.failure_count
    }