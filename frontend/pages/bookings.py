import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from ..utils.api_client import (
    get_bookings,
    create_booking,
    get_booking_details,
    update_booking_status,
    cancel_booking,
    search_bookings,
    get_events,
    get_ticket_types
)


def show_bookings():
    """Display bookings management page"""
    st.title("🎫 Bookings Management")
    
    # Tabs for different booking operations
    tab1, tab2, tab3, tab4 = st.tabs(["📋 View Bookings", "➕ New Booking", "🔍 Search Bookings", "📊 Booking Details"])
    
    with tab1:
        show_bookings_list()
    
    with tab2:
        show_add_booking_form()
    
    with tab3:
        show_search_bookings()
    
    with tab4:
        show_booking_details()


def show_bookings_list():
    """Display list of all bookings"""
    st.subheader("All Bookings")
    
    # Filter options
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        status_filter = st.selectbox(
            "Filter by Status:",
            options=["All", "Confirmed", "Pending", "Cancelled"],
            index=0
        )
    
    with col2:
        date_filter = st.selectbox(
            "Filter by Date:",
            options=["All", "Today", "This Week", "This Month", "Last 30 Days"],
            index=0
        )
    
    with col3:
        sort_by = st.selectbox(
            "Sort by:",
            options=["Booking Date", "Event Date", "Customer Name", "Total Price"],
            index=0
        )
    
    with col4:
        sort_order = st.selectbox(
            "Sort Order:",
            options=["Newest First", "Oldest First"],
            index=0
        )
    
    bookings = get_bookings()
    if not bookings:
        st.info("No bookings found. Create your first booking using the 'New Booking' tab.")
        return
    
    # Convert to DataFrame for filtering and sorting
    df = pd.DataFrame(bookings)
    df['booking_date'] = pd.to_datetime(df['booking_date'])
    df['event_date'] = pd.to_datetime(df['event_date'])
    
    # Apply filters
    filtered_df = df.copy()
    
    # Status filter
    if status_filter != "All":
        filtered_df = filtered_df[filtered_df['status'] == status_filter.lower()]
    
    # Date filter
    today = datetime.now().date()
    if date_filter == "Today":
        filtered_df = filtered_df[filtered_df['booking_date'].dt.date == today]
    elif date_filter == "This Week":
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        filtered_df = filtered_df[
            (filtered_df['booking_date'].dt.date >= week_start) & 
            (filtered_df['booking_date'].dt.date <= week_end)
        ]
    elif date_filter == "This Month":
        month_start = today.replace(day=1)
        next_month = (month_start + timedelta(days=32)).replace(day=1)
        filtered_df = filtered_df[
            (filtered_df['booking_date'].dt.date >= month_start) & 
            (filtered_df['booking_date'].dt.date < next_month)
        ]
    elif date_filter == "Last 30 Days":
        thirty_days_ago = today - timedelta(days=30)
        filtered_df = filtered_df[filtered_df['booking_date'].dt.date >= thirty_days_ago]
    
    # Sort
    ascending = sort_order == "Oldest First"
    if sort_by == "Booking Date":
        filtered_df = filtered_df.sort_values('booking_date', ascending=ascending)
    elif sort_by == "Event Date":
        filtered_df = filtered_df.sort_values('event_date', ascending=ascending)
    elif sort_by == "Customer Name":
        filtered_df = filtered_df.sort_values('customer_name', ascending=True)
    elif sort_by == "Total Price":
        filtered_df = filtered_df.sort_values('total_price', ascending=ascending)
    
    if filtered_df.empty:
        st.info("No bookings match the selected filters.")
        return
    
    # Display bookings
    for idx, booking in filtered_df.iterrows():
        with st.container():
            col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 1, 1])
            
            with col1:
                st.markdown(f"**{booking['customer_name']}**")
                st.markdown(f"📧 {booking['customer_email']}")
                st.markdown(f"🎫 #{booking['booking_code']}")
            
            with col2:
                st.markdown(f"🎭 **{booking['event_name']}**")
                st.markdown(f"🏟️ {booking['venue_name']}")
                st.markdown(f"📅 {booking['event_date'].strftime('%Y-%m-%d %H:%M')}")
            
            with col3:
                st.markdown(f"🎟️ {booking['ticket_type_name']} x{booking['quantity']}")
                st.markdown(f"💰 **${booking['total_price']:.2f}**")
                st.markdown(f"🗓️ Booked: {booking['booking_date'].strftime('%Y-%m-%d')}")
            
            with col4:
                # Status with color coding
                status_colors = {
                    'confirmed': '🟢',
                    'pending': '🟡',
                    'cancelled': '🔴'
                }
                status_icon = status_colors.get(booking['status'], '⚪')
                st.markdown(f"{status_icon} **{booking['status'].title()}**")
                
                # Quick status update
                if booking['status'] == 'pending':
                    if st.button("✅ Confirm", key=f"confirm_{booking['id']}"):
                        if update_booking_status(booking['id'], 'confirmed'):
                            st.success("Booking confirmed!")
                            st.experimental_rerun()
                        else:
                            st.error("Failed to confirm booking")
            
            with col5:
                if st.button("View Details", key=f"view_{booking['id']}"):
                    st.session_state.selected_booking_id = booking['id']
                    st.experimental_rerun()
                
                if booking['status'] != 'cancelled':
                    if st.button("❌ Cancel", key=f"cancel_{booking['id']}"):
                        if cancel_booking(booking['id']):
                            st.success("Booking cancelled!")
                            st.experimental_rerun()
                        else:
                            st.error("Failed to cancel booking")
            
            st.markdown("---")
    
    # Summary statistics
    st.subheader("📊 Bookings Summary")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Bookings", len(filtered_df))
    
    with col2:
        total_tickets = filtered_df['quantity'].sum()
        st.metric("Total Tickets", total_tickets)
    
    with col3:
        total_revenue = filtered_df['total_price'].sum()
        st.metric("Total Revenue", f"${total_revenue:.2f}")
    
    with col4:
        confirmed_bookings = len(filtered_df[filtered_df['status'] == 'confirmed'])
        st.metric("Confirmed Bookings", confirmed_bookings)


def show_add_booking_form():
    """Display form to add a new booking"""
    st.subheader("Create New Booking")
    
    # Get events and ticket types
    events = get_events()
    ticket_types = get_ticket_types()
    
    if not events:
        st.error("No events available. Please add an event first.")
        return
    
    if not ticket_types:
        st.error("No ticket types available. Please add ticket types first.")
        return
    
    # Filter active events that are in the future
    active_events = [
        e for e in events 
        if e['status'] == 'active' and 
        datetime.fromisoformat(e['event_date'].replace('Z', '+00:00')).date() >= date.today()
    ]
    
    if not active_events:
        st.warning("No active upcoming events available for booking.")
        return
    
    event_options = {
        f"{e['name']} - {e['event_date'][:10]} at {e['venue_name']}": e['id'] 
        for e in active_events
    }
    
    ticket_type_options = {
        f"{t['name']} - ${t['price']:.2f}": t['id'] 
        for t in ticket_types
    }
    
    with st.form("add_booking_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            customer_name = st.text_input(
                "Customer Name *",
                placeholder="e.g., John Doe",
                help="Enter the customer's full name"
            )
            
            customer_email = st.text_input(
                "Customer Email *",
                placeholder="e.g., john.doe@email.com",
                help="Enter a valid email address"
            )
            
            event_selection = st.selectbox(
                "Event *",
                options=list(event_options.keys()),
                help="Select the event for this booking"
            )
        
        with col2:
            ticket_type_selection = st.selectbox(
                "Ticket Type *",
                options=list(ticket_type_options.keys()),
                help="Select the type of ticket"
            )
            
            quantity = st.number_input(
                "Quantity *",
                min_value=1,
                max_value=10,
                value=1,
                help="Number of tickets (max 10 per booking)"
            )
            
            # Calculate total price
            if ticket_type_selection:
                selected_ticket_type = next(
                    t for t in ticket_types 
                    if t['id'] == ticket_type_options[ticket_type_selection]
                )
                total_price = selected_ticket_type['price'] * quantity
                st.markdown(f"**Total Price: ${total_price:.2f}**")
        
        submitted = st.form_submit_button("🎫 Create Booking", use_container_width=True)
        
        if submitted:
            if not all([customer_name.strip(), customer_email.strip(), event_selection, ticket_type_selection]):
                st.error("Please fill in all required fields.")
            elif '@' not in customer_email or '.' not in customer_email:
                st.error("Please enter a valid email address.")
            else:
                event_id = event_options[event_selection]
                ticket_type_id = ticket_type_options[ticket_type_selection]
                
                booking_data = {
                    "customer_name": customer_name.strip(),
                    "customer_email": customer_email.strip().lower(),
                    "event_id": event_id,
                    "ticket_type_id": ticket_type_id,
                    "quantity": quantity
                }
                
                with st.spinner("Creating booking..."):
                    result = create_booking(booking_data)
                    
                    if result:
                        st.success(f"✅ Booking created successfully!")
                        st.success(f"🎫 Booking Code: **{result['booking_code']}**")
                        st.success(f"💰 Total Amount: **${result['total_price']:.2f}**")
                        st.balloons()
                        # Clear form by rerunning
                        st.experimental_rerun()
                    else:
                        st.error("❌ Failed to create booking. Please check availability and try again.")


def show_search_bookings():
    """Display booking search functionality"""
    st.subheader("Search Bookings")
    
    with st.form("search_bookings_form"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            customer_name = st.text_input(
                "Customer Name",
                placeholder="Search by customer name"
            )
            
            customer_email = st.text_input(
                "Customer Email",
                placeholder="Search by email"
            )
        
        with col2:
            booking_code = st.text_input(
                "Booking Code",
                placeholder="Search by booking code"
            )
            
            event_name = st.text_input(
                "Event Name",
                placeholder="Search by event name"
            )
        
        with col3:
            venue_name = st.text_input(
                "Venue Name",
                placeholder="Search by venue name"
            )
            
            status = st.selectbox(
                "Status",
                options=["", "confirmed", "pending", "cancelled"],
                format_func=lambda x: "All Statuses" if x == "" else x.title()
            )
        
        search_submitted = st.form_submit_button("🔍 Search Bookings", use_container_width=True)
    
    if search_submitted:
        # Build search parameters
        search_params = {}
        if customer_name.strip():
            search_params['customer_name'] = customer_name.strip()
        if customer_email.strip():
            search_params['customer_email'] = customer_email.strip()
        if booking_code.strip():
            search_params['booking_code'] = booking_code.strip()
        if event_name.strip():
            search_params['event_name'] = event_name.strip()
        if venue_name.strip():
            search_params['venue_name'] = venue_name.strip()
        if status:
            search_params['status'] = status
        
        if not search_params:
            st.warning("Please enter at least one search criteria.")
        else:
            with st.spinner("Searching bookings..."):
                search_results = search_bookings(search_params)
                
                if search_results:
                    st.success(f"Found {len(search_results)} booking(s)")
                    
                    # Display search results
                    for booking in search_results:
                        with st.container():
                            col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
                            
                            with col1:
                                st.markdown(f"**{booking['customer_name']}**")
                                st.markdown(f"📧 {booking['customer_email']}")
                                st.markdown(f"🎫 #{booking['booking_code']}")
                            
                            with col2:
                                st.markdown(f"🎭 **{booking['event_name']}**")
                                st.markdown(f"🏟️ {booking['venue_name']}")
                                st.markdown(f"📅 {booking['event_date'][:10]}")
                            
                            with col3:
                                st.markdown(f"🎟️ {booking['ticket_type_name']} x{booking['quantity']}")
                                st.markdown(f"💰 **${booking['total_price']:.2f}**")
                                
                                status_colors = {
                                    'confirmed': '🟢',
                                    'pending': '🟡',
                                    'cancelled': '🔴'
                                }
                                status_icon = status_colors.get(booking['status'], '⚪')
                                st.markdown(f"{status_icon} {booking['status'].title()}")
                            
                            with col4:
                                if st.button("View Details", key=f"search_view_{booking['id']}"):
                                    st.session_state.selected_booking_id = booking['id']
                                    st.experimental_rerun()
                            
                            st.markdown("---")
                else:
                    st.info("No bookings found matching your search criteria.")


def show_booking_details():
    """Display detailed information about a selected booking"""
    st.subheader("Booking Details")
    
    # Booking selection
    bookings = get_bookings()
    if not bookings:
        st.info("No bookings available.")
        return
    
    booking_options = {
        f"#{b['booking_code']} - {b['customer_name']} - {b['event_name']}": b['id'] 
        for b in bookings
    }
    
    # Check if booking is selected from other views
    default_booking = None
    if hasattr(st.session_state, 'selected_booking_id'):
        for name, bid in booking_options.items():
            if bid == st.session_state.selected_booking_id:
                default_booking = name
                break
    
    selected_booking_name = st.selectbox(
        "Select a booking to view details:",
        options=list(booking_options.keys()),
        index=list(booking_options.keys()).index(default_booking) if default_booking else 0
    )
    
    if selected_booking_name:
        booking_id = booking_options[selected_booking_name]
        
        # Get booking details
        booking_details = get_booking_details(booking_id)
        if not booking_details:
            st.error("Failed to load booking details.")
            return
        
        # Display booking information
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🎫 Booking Information")
            st.markdown(f"**Booking Code:** #{booking_details['booking_code']}")
            st.markdown(f"**Customer Name:** {booking_details['customer_name']}")
            st.markdown(f"**Customer Email:** {booking_details['customer_email']}")
            st.markdown(f"**Quantity:** {booking_details['quantity']} tickets")
            st.markdown(f"**Total Price:** ${booking_details['total_price']:.2f}")
            st.markdown(f"**Booking Date:** {booking_details['booking_date'][:10]}")
            
            # Status with color coding
            status_colors = {
                'confirmed': '🟢',
                'pending': '🟡',
                'cancelled': '🔴'
            }
            status_icon = status_colors.get(booking_details['status'], '⚪')
            st.markdown(f"**Status:** {status_icon} {booking_details['status'].title()}")
        
        with col2:
            st.markdown("### 🎭 Event Information")
            st.markdown(f"**Event Name:** {booking_details['event_name']}")
            if booking_details.get('event_description'):
                st.markdown(f"**Description:** {booking_details['event_description']}")
            st.markdown(f"**Event Date:** {booking_details['event_date'][:16]}")
            st.markdown(f"**Event Status:** {booking_details['event_status'].title()}")
            
            st.markdown("### 🏟️ Venue Information")
            st.markdown(f"**Venue:** {booking_details['venue_name']}")
            st.markdown(f"**Address:** {booking_details['venue_address']}")
            st.markdown(f"**City:** {booking_details['venue_city']}")
            
            st.markdown("### 🎟️ Ticket Information")
            st.markdown(f"**Ticket Type:** {booking_details['ticket_type_name']}")
            st.markdown(f"**Price per Ticket:** ${booking_details['ticket_type_price']:.2f}")
            if booking_details.get('ticket_type_description'):
                st.markdown(f"**Description:** {booking_details['ticket_type_description']}")
        
        # Booking actions
        st.markdown("### ⚙️ Booking Actions")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if booking_details['status'] == 'pending':
                if st.button("✅ Confirm Booking", use_container_width=True):
                    if update_booking_status(booking_id, 'confirmed'):
                        st.success("Booking confirmed successfully!")
                        st.experimental_rerun()
                    else:
                        st.error("Failed to confirm booking")
        
        with col2:
            if booking_details['status'] == 'confirmed':
                if st.button("⏸️ Set to Pending", use_container_width=True):
                    if update_booking_status(booking_id, 'pending'):
                        st.success("Booking status updated to pending!")
                        st.experimental_rerun()
                    else:
                        st.error("Failed to update booking status")
        
        with col3:
            if booking_details['status'] != 'cancelled':
                if st.button("❌ Cancel Booking", use_container_width=True):
                    if cancel_booking(booking_id):
                        st.success("Booking cancelled successfully!")
                        st.experimental_rerun()
                    else:
                        st.error("Failed to cancel booking")
        
        # Clear selected booking from session state
        if hasattr(st.session_state, 'selected_booking_id'):
            if st.button("🔄 Clear Selection"):
                del st.session_state.selected_booking_id
                st.experimental_rerun()