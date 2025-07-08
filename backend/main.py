from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base
from . import models
from .routes import (
    venues_router,
    events_router,
    ticket_types_router,
    bookings_router,
    stats_router
)

# Create FastAPI app
app = FastAPI(
    title="Ticket Booking System",
    description="A comprehensive ticket booking system for events, venues, and customer management",
    version="1.0.0"
)

# Add CORS middleware to allow Streamlit frontend connection
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://127.0.0.1:8501"],  # Streamlit default ports
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(venues_router)
app.include_router(events_router)
app.include_router(ticket_types_router)
app.include_router(bookings_router)
app.include_router(stats_router)

# Create database tables
@app.on_event("startup")
async def startup_event():
    """Create database tables on startup"""
    Base.metadata.create_all(bind=engine)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {"status": "healthy", "message": "Ticket Booking System is running"}

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Welcome to Ticket Booking System API",
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "venues": "/venues",
            "events": "/events",
            "ticket_types": "/ticket-types",
            "bookings": "/bookings",
            "statistics": "/stats"
        }
    }