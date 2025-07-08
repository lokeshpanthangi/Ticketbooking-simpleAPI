import streamlit as st
import pandas as pd
from ..utils.api_client import (
    get_venues,
    create_venue,
    get_venue_details,
    get_venue_events,
    get_venue_occupancy
)


def show_venues():
    """Display venues management page"""
    st.title("🏟️ Venues Management")
    
    # Tabs for different venue operations
    tab1, tab2, tab3 = st.tabs(["📋 View Venues", "➕ Add Venue", "📊 Venue Details"])
    
    with tab1:
        show_venues_list()
    
    with tab2:
        show_add_venue_form()
    
    with tab3:
        show_venue_details()


def show_venues_list():
    """Display list of all venues"""
    st.subheader("All Venues")
    
    venues = get_venues()
    if not venues:
        st.info("No venues found. Add your first venue using the 'Add Venue' tab.")
        return
    
    # Convert to DataFrame for better display
    df = pd.DataFrame(venues)
    
    # Display venues in cards
    for idx, venue in df.iterrows():
        with st.container():
            col1, col2, col3 = st.columns([3, 2, 1])
            
            with col1:
                st.markdown(f"### {venue['name']}")
                st.markdown(f"📍 **Address:** {venue['address']}")
                st.markdown(f"🏙️ **City:** {venue['city']}")
            
            with col2:
                st.markdown(f"**Capacity:** {venue['capacity']:,} seats")
                st.markdown(f"**Events:** {venue['event_count']} events")
                st.markdown(f"**Created:** {venue['created_at'][:10]}")
            
            with col3:
                if st.button(f"View Details", key=f"view_{venue['id']}"):
                    st.session_state.selected_venue_id = venue['id']
                    st.experimental_rerun()
            
            st.markdown("---")
    
    # Summary statistics
    st.subheader("📊 Venues Summary")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Venues", len(df))
    
    with col2:
        st.metric("Total Capacity", f"{df['capacity'].sum():,}")
    
    with col3:
        st.metric("Average Capacity", f"{df['capacity'].mean():.0f}")
    
    with col4:
        st.metric("Total Events", df['event_count'].sum())


def show_add_venue_form():
    """Display form to add a new venue"""
    st.subheader("Add New Venue")
    
    with st.form("add_venue_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input(
                "Venue Name *",
                placeholder="e.g., Madison Square Garden",
                help="Enter the name of the venue"
            )
            
            city = st.text_input(
                "City *",
                placeholder="e.g., New York",
                help="Enter the city where the venue is located"
            )
        
        with col2:
            capacity = st.number_input(
                "Capacity *",
                min_value=1,
                max_value=100000,
                value=1000,
                help="Enter the maximum seating capacity"
            )
        
        address = st.text_area(
            "Address *",
            placeholder="e.g., 4 Pennsylvania Plaza, New York, NY 10001",
            help="Enter the full address of the venue"
        )
        
        submitted = st.form_submit_button("🏟️ Create Venue", use_container_width=True)
        
        if submitted:
            if not all([name.strip(), address.strip(), city.strip()]):
                st.error("Please fill in all required fields.")
            else:
                venue_data = {
                    "name": name.strip(),
                    "address": address.strip(),
                    "city": city.strip(),
                    "capacity": capacity
                }
                
                with st.spinner("Creating venue..."):
                    result = create_venue(venue_data)
                    
                    if result:
                        st.success(f"✅ Venue '{name}' created successfully!")
                        st.balloons()
                        # Clear form by rerunning
                        st.experimental_rerun()
                    else:
                        st.error("❌ Failed to create venue. Please check if the venue name already exists.")


def show_venue_details():
    """Display detailed information about a selected venue"""
    st.subheader("Venue Details")
    
    # Venue selection
    venues = get_venues()
    if not venues:
        st.info("No venues available. Please add a venue first.")
        return
    
    venue_options = {f"{v['name']} - {v['city']}": v['id'] for v in venues}
    
    # Check if venue is selected from the list view
    default_venue = None
    if hasattr(st.session_state, 'selected_venue_id'):
        for name, vid in venue_options.items():
            if vid == st.session_state.selected_venue_id:
                default_venue = name
                break
    
    selected_venue_name = st.selectbox(
        "Select a venue to view details:",
        options=list(venue_options.keys()),
        index=list(venue_options.keys()).index(default_venue) if default_venue else 0
    )
    
    if selected_venue_name:
        venue_id = venue_options[selected_venue_name]
        
        # Get venue details
        venue_details = get_venue_details(venue_id)
        if not venue_details:
            st.error("Failed to load venue details.")
            return
        
        # Display venue information
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🏟️ Venue Information")
            st.markdown(f"**Name:** {venue_details['name']}")
            st.markdown(f"**Address:** {venue_details['address']}")
            st.markdown(f"**City:** {venue_details['city']}")
            st.markdown(f"**Capacity:** {venue_details['capacity']:,} seats")
            st.markdown(f"**Created:** {venue_details['created_at'][:10]}")
        
        with col2:
            # Get occupancy data
            occupancy = get_venue_occupancy(venue_id)
            if occupancy:
                st.markdown("### 📊 Occupancy Statistics")
                st.markdown(f"**Total Bookings:** {occupancy['total_bookings']:,}")
                st.markdown(f"**Available Capacity:** {occupancy['available_capacity']:,}")
                
                # Occupancy percentage with progress bar
                occupancy_pct = occupancy['occupancy_percentage']
                st.markdown(f"**Occupancy Rate:** {occupancy_pct:.1f}%")
                st.progress(occupancy_pct / 100)
                
                # Color-coded status
                if occupancy_pct >= 90:
                    st.error("🔴 Nearly Full")
                elif occupancy_pct >= 70:
                    st.warning("🟡 High Occupancy")
                elif occupancy_pct >= 30:
                    st.info("🟢 Moderate Occupancy")
                else:
                    st.success("🟢 Low Occupancy")
        
        # Events at this venue
        st.markdown("### 🎭 Events at this Venue")
        venue_events = get_venue_events(venue_id)
        
        if venue_events:
            events_df = pd.DataFrame(venue_events)
            
            # Display events in a nice format
            for idx, event in events_df.iterrows():
                with st.container():
                    col1, col2, col3 = st.columns([3, 2, 1])
                    
                    with col1:
                        st.markdown(f"**{event['name']}**")
                        if 'description' in event and event['description']:
                            st.markdown(f"📝 {event['description'][:100]}..." if len(event['description']) > 100 else f"📝 {event['description']}")
                    
                    with col2:
                        st.markdown(f"📅 **Date:** {event['event_date'][:10]}")
                        st.markdown(f"📊 **Status:** {event['status'].title()}")
                    
                    with col3:
                        if 'booking_count' in event:
                            st.markdown(f"🎫 {event['booking_count']} bookings")
                        st.markdown(f"🗓️ Created: {event['created_at'][:10]}")
                    
                    st.markdown("---")
        else:
            st.info("No events scheduled at this venue yet.")
        
        # Clear selected venue from session state
        if hasattr(st.session_state, 'selected_venue_id'):
            if st.button("🔄 Clear Selection"):
                del st.session_state.selected_venue_id
                st.experimental_rerun()