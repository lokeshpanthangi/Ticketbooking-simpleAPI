import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.api_client import (
    get_events,
    create_event,
    get_event,
    get_available_tickets,
    get_event_revenue,
    get_venues
)


def show_events():
    """Display events management page"""
    st.title("🎭 Events Management")
    
    # Tabs for different event operations
    tab1, tab2, tab3 = st.tabs(["📋 View Events", "➕ Add Event", "📊 Event Details"])
    
    with tab1:
        show_events_list()
    
    with tab2:
        show_add_event_form()
    
    with tab3:
        show_event_details()


def show_events_list():
    """Display list of all events"""
    st.subheader("All Events")
    
    # Filter options
    col1, col2, col3 = st.columns(3)
    
    with col1:
        status_filter = st.selectbox(
            "Filter by Status:",
            options=["All", "Active", "Cancelled", "Completed"],
            index=0
        )
    
    with col2:
        # Date range filter
        date_filter = st.selectbox(
            "Filter by Date:",
            options=["All", "Upcoming", "This Week", "This Month", "Past Events"],
            index=1  # Default to "Upcoming"
        )
    
    with col3:
        sort_by = st.selectbox(
            "Sort by:",
            options=["Event Date", "Created Date", "Name", "Venue"],
            index=0
        )
    
    events = get_events()
    if not events:
        st.info("No events found. Add your first event using the 'Add Event' tab.")
        return
    
    # Convert to DataFrame for filtering and sorting
    df = pd.DataFrame(events)
    df['event_date'] = pd.to_datetime(df['event_date'])
    df['created_at'] = pd.to_datetime(df['created_at'])
    
    # Apply filters
    filtered_df = df.copy()
    
    # Status filter
    if status_filter != "All":
        filtered_df = filtered_df[filtered_df['status'] == status_filter.lower()]
    
    # Date filter
    today = datetime.now().date()
    if date_filter == "Upcoming":
        filtered_df = filtered_df[filtered_df['event_date'].dt.date >= today]
    elif date_filter == "This Week":
        week_end = today + timedelta(days=7)
        filtered_df = filtered_df[
            (filtered_df['event_date'].dt.date >= today) & 
            (filtered_df['event_date'].dt.date <= week_end)
        ]
    elif date_filter == "This Month":
        month_start = today.replace(day=1)
        next_month = (month_start + timedelta(days=32)).replace(day=1)
        filtered_df = filtered_df[
            (filtered_df['event_date'].dt.date >= month_start) & 
            (filtered_df['event_date'].dt.date < next_month)
        ]
    elif date_filter == "Past Events":
        filtered_df = filtered_df[filtered_df['event_date'].dt.date < today]
    
    # Sort
    if sort_by == "Event Date":
        filtered_df = filtered_df.sort_values('event_date')
    elif sort_by == "Created Date":
        filtered_df = filtered_df.sort_values('created_at', ascending=False)
    elif sort_by == "Name":
        filtered_df = filtered_df.sort_values('name')
    elif sort_by == "Venue":
        filtered_df = filtered_df.sort_values('venue_name')
    
    if filtered_df.empty:
        st.info("No events match the selected filters.")
        return
    
    # Display events
    for idx, event in filtered_df.iterrows():
        with st.container():
            col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
            
            with col1:
                st.markdown(f"### {event['name']}")
                if 'description' in event and event['description']:
                    description = event['description'][:100] + "..." if len(event['description']) > 100 else event['description']
                    st.markdown(f"📝 {description}")
            
            with col2:
                st.markdown(f"🏟️ **Venue:** {event['venue_name']}")
                st.markdown(f"📍 **City:** {event['venue_city']}")
                st.markdown(f"📅 **Date:** {event['event_date'].strftime('%Y-%m-%d %H:%M')}")
            
            with col3:
                # Status with color coding
                status_colors = {
                    'active': '🟢',
                    'cancelled': '🔴',
                    'completed': '🔵'
                }
                status_icon = status_colors.get(event['status'], '⚪')
                st.markdown(f"**Status:** {status_icon} {event['status'].title()}")
                
                if 'booking_count' in event:
                    st.markdown(f"🎫 **Bookings:** {event['booking_count']}")
                if 'available_capacity' in event:
                    st.markdown(f"💺 **Available:** {event['available_capacity']}")
            
            with col4:
                if st.button(f"View Details", key=f"view_event_{event['id']}"):
                    st.session_state.selected_event_id = event['id']
                    st.rerun()
            
            st.markdown("---")
    
    # Summary statistics
    st.subheader("📊 Events Summary")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Events", len(filtered_df))
    
    with col2:
        active_events = len(filtered_df[filtered_df['status'] == 'active'])
        st.metric("Active Events", active_events)
    
    with col3:
        total_bookings = filtered_df['booking_count'].sum() if 'booking_count' in filtered_df.columns else 0
        st.metric("Total Bookings", total_bookings)
    
    with col4:
        upcoming_events = len(filtered_df[filtered_df['event_date'].dt.date >= today])
        st.metric("Upcoming Events", upcoming_events)


def show_add_event_form():
    """Display form to add a new event"""
    st.subheader("Add New Event")
    
    # Get venues for selection
    venues = get_venues()
    if not venues:
        st.error("No venues available. Please add a venue first before creating events.")
        return
    
    venue_options = {f"{v['name']} - {v['city']} (Capacity: {v['capacity']:,})": v['id'] for v in venues}
    
    with st.form("add_event_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input(
                "Event Name *",
                placeholder="e.g., Rock Concert 2024",
                help="Enter the name of the event"
            )
            
            venue_selection = st.selectbox(
                "Venue *",
                options=list(venue_options.keys()),
                help="Select the venue for this event"
            )
        
        with col2:
            event_date = st.date_input(
                "Event Date *",
                min_value=date.today(),
                value=date.today() + timedelta(days=7),
                help="Select the date for the event (must be in the future)"
            )
            
            event_time = st.time_input(
                "Event Time *",
                value=datetime.strptime("19:00", "%H:%M").time(),
                help="Select the time for the event"
            )
        
        description = st.text_area(
            "Description",
            placeholder="Enter a description of the event...",
            help="Optional description of the event",
            height=100
        )
        
        submitted = st.form_submit_button("🎭 Create Event", use_container_width=True)
        
        if submitted:
            if not all([name.strip(), venue_selection]):
                st.error("Please fill in all required fields.")
            else:
                # Combine date and time
                event_datetime = datetime.combine(event_date, event_time)
                
                # Check if the datetime is in the future
                if event_datetime <= datetime.now():
                    st.error("Event date and time must be in the future.")
                else:
                    venue_id = venue_options[venue_selection]
                    
                    event_data = {
                        "name": name.strip(),
                        "description": description.strip() if description.strip() else None,
                        "event_date": event_datetime.isoformat(),
                        "venue_id": venue_id
                    }
                    
                    with st.spinner("Creating event..."):
                        result = create_event(event_data)
                        
                        if result:
                            st.success(f"✅ Event '{name}' created successfully!")
                            st.balloons()
                            # Clear form by rerunning
                            st.rerun()
                        else:
                            st.error("❌ Failed to create event. Please try again.")


def show_event_details():
    """Display detailed information about a selected event"""
    st.subheader("Event Details")
    
    # Event selection
    events = get_events()
    if not events:
        st.info("No events available. Please add an event first.")
        return
    
    event_options = {f"{e['name']} - {e['event_date'][:10]} at {e['venue_name']}": e['id'] for e in events}
    
    # Check if event is selected from the list view
    default_event = None
    if hasattr(st.session_state, 'selected_event_id'):
        for name, eid in event_options.items():
            if eid == st.session_state.selected_event_id:
                default_event = name
                break
    
    selected_event_name = st.selectbox(
        "Select an event to view details:",
        options=list(event_options.keys()),
        index=list(event_options.keys()).index(default_event) if default_event else 0
    )
    
    if selected_event_name:
        event_id = event_options[selected_event_name]
        
        # Get event details
        event_details = get_event(event_id)
        if not event_details:
            st.error("Failed to load event details.")
            return
        
        # Display event information
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🎭 Event Information")
            st.markdown(f"**Name:** {event_details['name']}")
            if event_details.get('description'):
                st.markdown(f"**Description:** {event_details['description']}")
            st.markdown(f"**Date:** {event_details['event_date'][:16]}")
            st.markdown(f"**Status:** {event_details['status'].title()}")
            st.markdown(f"**Created:** {event_details['created_at'][:10]}")
            
            # Venue information
            st.markdown("### 🏟️ Venue Information")
            st.markdown(f"**Venue:** {event_details['venue_name']}")
            if event_details.get('venue_address'):
                st.markdown(f"**Address:** {event_details['venue_address']}")
            st.markdown(f"**City:** {event_details['venue_city']}")
            st.markdown(f"**Capacity:** {event_details['venue_capacity']:,} seats")
        
        with col2:
            # Get availability and revenue data
            availability = get_available_tickets(event_id)
            revenue = get_event_revenue(event_id)
            
            if availability:
                st.markdown("### 🎫 Ticket Availability")
                st.markdown(f"**Total Capacity:** {event_details['venue_capacity']:,}")
                st.markdown(f"**Tickets Booked:** {availability['total_booked']:,}")
                st.markdown(f"**Available Tickets:** {availability['available_capacity']:,}")
                
                # Availability percentage with progress bar
                booked_pct = (availability['total_booked'] / event_details['venue_capacity']) * 100
                st.markdown(f"**Sold:** {booked_pct:.1f}%")
                st.progress(booked_pct / 100)
                
                # Sold out status
                if availability['sold_out']:
                    st.error("🔴 SOLD OUT")
                elif booked_pct >= 90:
                    st.warning("🟡 Nearly Sold Out")
                elif booked_pct >= 70:
                    st.info("🟢 High Demand")
                else:
                    st.success("🟢 Tickets Available")
            
            if revenue:
                st.markdown("### 💰 Revenue Information")
                st.markdown(f"**Total Revenue:** ${revenue['total_revenue']:.2f}")
                st.markdown(f"**Confirmed Revenue:** ${revenue['confirmed_revenue']:.2f}")
                st.markdown(f"**Pending Revenue:** ${revenue['pending_revenue']:.2f}")
                
                # Revenue breakdown by status
                if revenue.get('revenue_by_status'):
                    st.markdown("**Revenue Breakdown:**")
                    for status, amount in revenue['revenue_by_status'].items():
                        st.markdown(f"  - {status.title()}: ${amount:.2f}")
        
        # Bookings for this event (temporarily disabled)
        st.markdown("### 📋 Event Bookings")
        st.info("Event bookings feature is temporarily unavailable.")
        # event_bookings = get_event_bookings(event_id)
        
        if False:  # event_bookings:
            bookings_df = pd.DataFrame(event_bookings)
            
            # Summary stats
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Bookings", len(bookings_df))
            with col2:
                st.metric("Total Tickets", bookings_df['quantity'].sum())
            with col3:
                confirmed_bookings = len(bookings_df[bookings_df['status'] == 'confirmed'])
                st.metric("Confirmed Bookings", confirmed_bookings)
            with col4:
                total_revenue = bookings_df['total_price'].sum()
                st.metric("Total Revenue", f"${total_revenue:.2f}")
            
            # Display bookings
            st.markdown("#### Recent Bookings")
            for idx, booking in bookings_df.head(10).iterrows():
                with st.container():
                    col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
                    
                    with col1:
                        st.markdown(f"**{booking['customer_name']}**")
                        st.markdown(f"📧 {booking['customer_email']}")
                    
                    with col2:
                        st.markdown(f"🎫 {booking['ticket_type_name']} x{booking['quantity']}")
                        st.markdown(f"🗓️ {booking['booking_date'][:10]}")
                    
                    with col3:
                        status_colors = {
                            'confirmed': '🟢',
                            'pending': '🟡',
                            'cancelled': '🔴'
                        }
                        status_icon = status_colors.get(booking['status'], '⚪')
                        st.markdown(f"{status_icon} {booking['status'].title()}")
                    
                    with col4:
                        st.markdown(f"**${booking['total_price']:.2f}**")
                        st.markdown(f"#{booking['booking_code']}")
                    
                    st.markdown("---")
            
            if len(bookings_df) > 10:
                st.info(f"Showing 10 of {len(bookings_df)} bookings. Use the Bookings page to view all.")
        else:
            st.info("No bookings for this event yet.")
        
        # Clear selected event from session state
        if hasattr(st.session_state, 'selected_event_id'):
            if st.button("🔄 Clear Selection"):
                del st.session_state.selected_event_id
                st.rerun()