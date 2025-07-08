# 🎫 Ticket Booking System

A comprehensive ticket booking system similar to BookMyShow/Ticketmaster, built with FastAPI backend, SQLite database, and Streamlit frontend.

## 🌟 Features

### Core Functionality
- **🏟️ Venue Management**: Create and manage venues with capacity tracking
- **🎭 Event Scheduling**: Schedule events at venues with date/time management
- **🎫 Booking System**: Complete booking workflow with customer management
- **🎟️ Ticket Types**: Multiple ticket categories (VIP, Premium, Standard, Economy, Student)
- **📊 Analytics Dashboard**: Comprehensive statistics and reporting

### Advanced Features
- **🔍 Search & Filter**: Advanced search across bookings, events, and venues
- **📈 Real-time Analytics**: Revenue tracking, occupancy rates, popular events
- **💰 Revenue Management**: Status-based revenue tracking (confirmed, pending, cancelled)
- **🎯 Capacity Management**: Automatic capacity validation and sold-out detection
- **📱 Responsive UI**: Modern, mobile-friendly interface

## 🏗️ Architecture

### Backend (FastAPI)
- **Database**: SQLite with SQLAlchemy ORM
- **API**: RESTful API with automatic documentation
- **Models**: Venue, Event, TicketType, Booking
- **Validation**: Pydantic schemas with business logic validation
- **Features**: CORS support, automatic API docs, health checks

### Frontend (Streamlit)
- **Dashboard**: Key metrics and overview statistics
- **Management Pages**: Dedicated pages for each entity type
- **Interactive Charts**: Plotly-powered visualizations
- **Real-time Updates**: Live data synchronization with backend
- **User Experience**: Intuitive navigation and responsive design

## 📋 Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

## 🚀 Quick Start

### Option 1: One-Command Setup (Recommended)

1. **Clone or download the project**
2. **Navigate to the project directory**
3. **Run the startup script**:
   ```bash
   python run.py
   ```

This will automatically:
- Install dependencies
- Initialize the database
- Start both backend and frontend servers
- Populate sample data
- Open the application in your browser

### Option 2: Manual Setup

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Start the backend server**:
   ```bash
   uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
   ```

3. **Start the frontend server** (in a new terminal):
   ```bash
   streamlit run frontend/app.py --server.port 8501
   ```

## 🌐 Access Points

Once running, access the application at:

- **🎨 Frontend (Main App)**: http://localhost:8501
- **🔧 Backend API**: http://localhost:8000
- **📚 API Documentation**: http://localhost:8000/docs
- **🔍 Alternative API Docs**: http://localhost:8000/redoc

## 📖 Usage Guide

### Getting Started
1. **Explore the Dashboard** - Get an overview of the system
2. **Add Venues** - Create venues where events will be held
3. **Set Up Ticket Types** - Define different ticket categories and prices
4. **Create Events** - Schedule events at your venues
5. **Manage Bookings** - Handle customer bookings and reservations

### Key Workflows

#### Creating a Complete Booking Flow
1. **Venues** → Add a new venue with capacity
2. **Ticket Types** → Create ticket categories (VIP, Standard, etc.)
3. **Events** → Schedule an event at the venue
4. **Bookings** → Create customer bookings for the event

#### Monitoring Performance
1. **Dashboard** → View key metrics and trends
2. **Venue Details** → Check occupancy rates
3. **Event Details** → Monitor ticket sales and revenue
4. **Analytics** → Review popular events and busiest venues

## 🗂️ Project Structure

```
ticket-booking-system/
├── backend/
│   ├── models/          # Database models
│   ├── schemas/         # Pydantic schemas
│   ├── routes/          # API endpoints
│   ├── utils/           # Helper functions
│   ├── database.py      # Database configuration
│   └── main.py          # FastAPI application
├── frontend/
│   ├── pages/           # Streamlit pages
│   ├── utils/           # Frontend utilities
│   └── app.py           # Main Streamlit app
├── requirements.txt     # Python dependencies
├── run.py              # Startup script
└── README.md           # This file
```

## 🔧 API Endpoints

### Venues
- `GET /venues/` - List all venues
- `POST /venues/` - Create a new venue
- `GET /venues/{id}` - Get venue details
- `GET /venues/{id}/events` - Get venue events
- `GET /venues/{id}/occupancy` - Get occupancy stats

### Events
- `GET /events/` - List all events
- `POST /events/` - Create a new event
- `GET /events/{id}` - Get event details
- `GET /events/{id}/bookings` - Get event bookings
- `GET /events/{id}/available-tickets` - Check availability
- `GET /events/{id}/revenue` - Get revenue stats

### Bookings
- `GET /bookings/` - List all bookings
- `POST /bookings/` - Create a new booking
- `GET /bookings/{id}` - Get booking details
- `PUT /bookings/{id}` - Update booking
- `DELETE /bookings/{id}` - Cancel booking
- `GET /bookings/search/` - Search bookings

### Ticket Types
- `GET /ticket-types/` - List all ticket types
- `POST /ticket-types/` - Create a new ticket type
- `GET /ticket-types/{id}` - Get ticket type details
- `PUT /ticket-types/{id}` - Update ticket type
- `GET /ticket-types/{id}/stats` - Get type statistics

### Statistics
- `GET /stats/` - System overview statistics
- `GET /stats/popular-events` - Most popular events
- `GET /stats/busiest-venues` - Busiest venues
- `GET /stats/revenue-by-month` - Monthly revenue

## 🎯 Key Features Explained

### Capacity Management
- Automatic validation of venue capacity
- Real-time availability checking
- Sold-out detection and warnings
- Occupancy rate calculations

### Revenue Tracking
- Status-based revenue (confirmed, pending, cancelled)
- Real-time revenue calculations
- Monthly revenue trends
- Revenue breakdown by ticket types

### Search & Filtering
- Multi-criteria booking search
- Event filtering by date and status
- Venue filtering and sorting
- Advanced analytics filtering

### Data Validation
- Email format validation
- Future date validation for events
- Capacity constraint enforcement
- Unique booking code generation

## 🛠️ Development

### Adding New Features
1. **Backend**: Add models, schemas, and routes
2. **Frontend**: Create corresponding UI components
3. **API Client**: Update the API client functions
4. **Testing**: Test the new functionality

### Database Schema
- **Venues**: id, name, address, city, capacity, created_at
- **Events**: id, name, description, event_date, venue_id, status, created_at
- **TicketTypes**: id, name, price, description, created_at
- **Bookings**: id, booking_code, customer_name, customer_email, event_id, ticket_type_id, quantity, total_price, status, booking_date

## 🔍 Troubleshooting

### Common Issues

1. **Backend not starting**:
   - Check if port 8000 is available
   - Ensure all dependencies are installed
   - Check Python version (3.8+ required)

2. **Frontend not connecting**:
   - Verify backend is running on port 8000
   - Check network connectivity
   - Refresh the browser page

3. **Database issues**:
   - Delete `ticket_booking.db` and restart
   - Check file permissions
   - Ensure SQLite is available

4. **Sample data not loading**:
   - Backend must be running first
   - Check API endpoint accessibility
   - Manual data entry is always available

### Performance Tips
- Use filters to limit large data sets
- Refresh pages if data seems stale
- Monitor system resources for large venues

## 📊 Sample Data

The system includes sample data for demonstration:
- **3 Venues**: Madison Square Garden, Hollywood Bowl, Red Rocks
- **5 Ticket Types**: VIP, Premium, Standard, Economy, Student
- **3 Events**: Rock Concert, Jazz Festival, Classical Symphony
- **Sample Bookings**: Various customer bookings

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is open source and available under the MIT License.

## 🆘 Support

For support or questions:
1. Check the troubleshooting section
2. Review the API documentation at `/docs`
3. Examine the sample data for examples
4. Use the built-in help sections in the UI

---

**Built with ❤️ using FastAPI and Streamlit**