#!/usr/bin/env python3
"""
Ticket Booking System Startup Script

This script initializes the database and starts both the FastAPI backend
and Streamlit frontend servers.
"""

import os
import sys
import subprocess
import time
import requests
from pathlib import Path

# Add the current directory to Python path
sys.path.append(str(Path(__file__).parent))

from backend.database import engine, Base
from backend.models import venue, event, ticket_type, booking


def create_database():
    """Create all database tables"""
    print("🗄️  Initializing database...")
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully!")
        return True
    except Exception as e:
        print(f"❌ Failed to create database: {e}")
        return False


def check_backend_health(max_retries=30, delay=1):
    """Check if backend is running and healthy"""
    print("🔍 Checking backend health...")
    
    for attempt in range(max_retries):
        try:
            response = requests.get("http://localhost:8000/health", timeout=5)
            if response.status_code == 200:
                print("✅ Backend is healthy!")
                return True
        except requests.exceptions.RequestException:
            if attempt < max_retries - 1:
                print(f"⏳ Waiting for backend... (attempt {attempt + 1}/{max_retries})")
                time.sleep(delay)
            else:
                print("❌ Backend health check failed")
                return False
    
    return False


def start_backend():
    """Start the FastAPI backend server"""
    print("🚀 Starting FastAPI backend server...")
    try:
        # Start uvicorn server
        backend_process = subprocess.Popen([
            sys.executable, "-m", "uvicorn", 
            "backend.main:app", 
            "--host", "0.0.0.0", 
            "--port", "8000", 
            "--reload"
        ], cwd=Path(__file__).parent)
        
        print("⏳ Backend server starting...")
        return backend_process
    except Exception as e:
        print(f"❌ Failed to start backend: {e}")
        return None


def start_frontend():
    """Start the Streamlit frontend server"""
    print("🎨 Starting Streamlit frontend server...")
    try:
        # Start streamlit server
        frontend_process = subprocess.Popen([
            sys.executable, "-m", "streamlit", "run", 
            "frontend/app.py",
            "--server.port", "8501",
            "--server.address", "localhost",
            "--browser.gatherUsageStats", "false"
        ], cwd=Path(__file__).parent)
        
        print("⏳ Frontend server starting...")
        return frontend_process
    except Exception as e:
        print(f"❌ Failed to start frontend: {e}")
        return None


def populate_sample_data():
    """Populate the database with sample data for demonstration"""
    print("📊 Adding sample data...")
    
    try:
        import requests
        import json
        from datetime import datetime, timedelta
        
        base_url = "http://localhost:8000"
        
        # Sample venues
        venues_data = [
            {
                "name": "Madison Square Garden",
                "address": "4 Pennsylvania Plaza, New York, NY 10001",
                "city": "New York",
                "capacity": 20000
            },
            {
                "name": "Hollywood Bowl",
                "address": "2301 Highland Ave, Los Angeles, CA 90068",
                "city": "Los Angeles",
                "capacity": 17500
            },
            {
                "name": "Red Rocks Amphitheatre",
                "address": "18300 W Alameda Pkwy, Morrison, CO 80465",
                "city": "Morrison",
                "capacity": 9525
            }
        ]
        
        # Create venues
        venue_ids = []
        for venue_data in venues_data:
            response = requests.post(f"{base_url}/venues/", json=venue_data)
            if response.status_code == 200:
                venue_ids.append(response.json()["id"])
                print(f"✅ Created venue: {venue_data['name']}")
        
        # Sample ticket types
        ticket_types_data = [
            {"name": "VIP", "price": 150.00, "description": "Premium seating with exclusive amenities"},
            {"name": "Premium", "price": 100.00, "description": "Enhanced seating with additional perks"},
            {"name": "Standard", "price": 50.00, "description": "Regular seating with standard amenities"},
            {"name": "Economy", "price": 25.00, "description": "Budget-friendly seating option"},
            {"name": "Student", "price": 20.00, "description": "Discounted tickets for students"}
        ]
        
        # Create ticket types
        ticket_type_ids = []
        for ticket_data in ticket_types_data:
            response = requests.post(f"{base_url}/ticket-types/", json=ticket_data)
            if response.status_code == 200:
                ticket_type_ids.append(response.json()["id"])
                print(f"✅ Created ticket type: {ticket_data['name']}")
        
        # Sample events
        events_data = [
            {
                "name": "Rock Concert 2024",
                "description": "An amazing rock concert featuring top artists",
                "event_date": (datetime.now() + timedelta(days=30)).isoformat(),
                "venue_id": venue_ids[0] if venue_ids else 1
            },
            {
                "name": "Jazz Festival",
                "description": "Annual jazz festival with renowned musicians",
                "event_date": (datetime.now() + timedelta(days=45)).isoformat(),
                "venue_id": venue_ids[1] if len(venue_ids) > 1 else 1
            },
            {
                "name": "Classical Symphony",
                "description": "Beautiful classical music performance",
                "event_date": (datetime.now() + timedelta(days=60)).isoformat(),
                "venue_id": venue_ids[2] if len(venue_ids) > 2 else 1
            }
        ]
        
        # Create events
        event_ids = []
        for event_data in events_data:
            response = requests.post(f"{base_url}/events/", json=event_data)
            if response.status_code == 200:
                event_ids.append(response.json()["id"])
                print(f"✅ Created event: {event_data['name']}")
        
        # Sample bookings
        bookings_data = [
            {
                "customer_name": "John Doe",
                "customer_email": "john.doe@email.com",
                "event_id": event_ids[0] if event_ids else 1,
                "ticket_type_id": ticket_type_ids[0] if ticket_type_ids else 1,
                "quantity": 2
            },
            {
                "customer_name": "Jane Smith",
                "customer_email": "jane.smith@email.com",
                "event_id": event_ids[1] if len(event_ids) > 1 else 1,
                "ticket_type_id": ticket_type_ids[2] if len(ticket_type_ids) > 2 else 1,
                "quantity": 4
            },
            {
                "customer_name": "Bob Johnson",
                "customer_email": "bob.johnson@email.com",
                "event_id": event_ids[0] if event_ids else 1,
                "ticket_type_id": ticket_type_ids[1] if len(ticket_type_ids) > 1 else 1,
                "quantity": 1
            }
        ]
        
        # Create bookings
        for booking_data in bookings_data:
            response = requests.post(f"{base_url}/bookings/", json=booking_data)
            if response.status_code == 200:
                booking_code = response.json()["booking_code"]
                print(f"✅ Created booking: {booking_code} for {booking_data['customer_name']}")
        
        print("✅ Sample data populated successfully!")
        
    except Exception as e:
        print(f"⚠️  Warning: Could not populate sample data: {e}")
        print("   You can add data manually through the web interface.")


def main():
    """Main function to start the ticket booking system"""
    print("🎫 Welcome to the Ticket Booking System!")
    print("=" * 50)
    
    # Step 1: Initialize database
    if not create_database():
        print("❌ Failed to initialize database. Exiting.")
        return
    
    # Step 2: Start backend server
    backend_process = start_backend()
    if not backend_process:
        print("❌ Failed to start backend server. Exiting.")
        return
    
    # Step 3: Wait for backend to be healthy
    if not check_backend_health():
        print("❌ Backend is not responding. Terminating backend process.")
        backend_process.terminate()
        return
    
    # Step 4: Populate sample data
    populate_sample_data()
    
    # Step 5: Start frontend server
    frontend_process = start_frontend()
    if not frontend_process:
        print("❌ Failed to start frontend server. Terminating backend.")
        backend_process.terminate()
        return
    
    # Success message
    print("\n" + "=" * 50)
    print("🎉 Ticket Booking System is now running!")
    print("\n📍 Access Points:")
    print("   🎨 Frontend (Streamlit): http://localhost:8501")
    print("   🔧 Backend API (FastAPI): http://localhost:8000")
    print("   📚 API Documentation: http://localhost:8000/docs")
    print("\n⚡ Features Available:")
    print("   🏟️  Venue Management")
    print("   🎭 Event Scheduling")
    print("   🎫 Booking System")
    print("   🎟️  Ticket Types")
    print("   📊 Analytics Dashboard")
    print("\n💡 Tips:")
    print("   - Start by exploring the Dashboard")
    print("   - Sample data has been loaded for demonstration")
    print("   - Use Ctrl+C to stop both servers")
    print("=" * 50)
    
    try:
        # Keep the script running
        print("\n⏳ Servers are running. Press Ctrl+C to stop...")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down servers...")
        
        # Terminate processes
        if frontend_process:
            frontend_process.terminate()
            print("✅ Frontend server stopped")
        
        if backend_process:
            backend_process.terminate()
            print("✅ Backend server stopped")
        
        print("👋 Thank you for using the Ticket Booking System!")


if __name__ == "__main__":
    main()