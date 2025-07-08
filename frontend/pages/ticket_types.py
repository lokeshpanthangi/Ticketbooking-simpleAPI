import streamlit as st
import pandas as pd
import plotly.express as px
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.api_client import (
    get_ticket_types,
    create_ticket_type,
    update_ticket_type,
    get_ticket_type_stats
)


def show_ticket_types():
    """Display ticket types management page"""
    st.title("🎟️ Ticket Types Management")
    
    # Tabs for different ticket type operations
    tab1, tab2, tab3, tab4 = st.tabs(["📋 View Ticket Types", "➕ Add Ticket Type", "✏️ Edit Ticket Type", "📊 Type Details"])
    
    with tab1:
        show_ticket_types_list()
    
    with tab2:
        show_add_ticket_type_form()
    
    with tab3:
        show_edit_ticket_type_form()
    
    with tab4:
        show_ticket_type_details()


def show_ticket_types_list():
    """Display list of all ticket types"""
    st.subheader("All Ticket Types")
    
    ticket_types = get_ticket_types()
    if not ticket_types:
        st.info("No ticket types found. Add your first ticket type using the 'Add Ticket Type' tab.")
        return
    
    # Convert to DataFrame for better display
    df = pd.DataFrame(ticket_types)
    
    # Sort by price
    df = df.sort_values('price')
    
    # Display ticket types in cards
    for idx, ticket_type in df.iterrows():
        with st.container():
            col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
            
            with col1:
                # Color coding based on ticket type
                type_colors = {
                    'VIP': '🟣',
                    'Premium': '🟠',
                    'Standard': '🔵',
                    'Economy': '🟢',
                    'Student': '🟡'
                }
                type_icon = type_colors.get(ticket_type['name'], '⚪')
                st.markdown(f"### {type_icon} {ticket_type['name']}")
                
                if ticket_type.get('description'):
                    st.markdown(f"📝 {ticket_type['description']}")
            
            with col2:
                st.markdown(f"**Price:** ${ticket_type['price']:.2f}")
                st.markdown(f"**Created:** {ticket_type['created_at'][:10]}")
            
            with col3:
                # Get stats for this ticket type
                stats = get_ticket_type_stats(ticket_type['id'])
                if stats:
                    st.markdown(f"**Total Bookings:** {stats['total_bookings']}")
                    st.markdown(f"**Tickets Sold:** {stats['total_tickets_sold']}")
                    st.markdown(f"**Revenue:** ${stats['total_revenue']:.2f}")
                else:
                    st.markdown("**Total Bookings:** 0")
                    st.markdown("**Tickets Sold:** 0")
                    st.markdown("**Revenue:** $0.00")
            
            with col4:
                if st.button(f"View Details", key=f"view_type_{ticket_type['id']}"):
                    st.session_state.selected_ticket_type_id = ticket_type['id']
                    st.rerun()
                
                if st.button(f"Edit", key=f"edit_type_{ticket_type['id']}"):
                    st.session_state.edit_ticket_type_id = ticket_type['id']
                    st.rerun()
            
            st.markdown("---")
    
    # Summary statistics
    st.subheader("📊 Ticket Types Summary")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Types", len(df))
    
    with col2:
        avg_price = df['price'].mean()
        st.metric("Average Price", f"${avg_price:.2f}")
    
    with col3:
        min_price = df['price'].min()
        st.metric("Lowest Price", f"${min_price:.2f}")
    
    with col4:
        max_price = df['price'].max()
        st.metric("Highest Price", f"${max_price:.2f}")
    
    # Price distribution chart
    if len(df) > 1:
        st.subheader("💰 Price Distribution")
        fig = px.bar(
            df,
            x='name',
            y='price',
            title="Ticket Type Prices",
            color='price',
            color_continuous_scale='viridis'
        )
        fig.update_layout(
            xaxis_title="Ticket Type",
            yaxis_title="Price ($)",
            showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)


def show_add_ticket_type_form():
    """Display form to add a new ticket type"""
    st.subheader("Add New Ticket Type")
    
    # Predefined ticket type options
    predefined_types = {
        "VIP": {"description": "Premium seating with exclusive amenities", "suggested_price": 150.00},
        "Premium": {"description": "Enhanced seating with additional perks", "suggested_price": 100.00},
        "Standard": {"description": "Regular seating with standard amenities", "suggested_price": 50.00},
        "Economy": {"description": "Budget-friendly seating option", "suggested_price": 25.00},
        "Student": {"description": "Discounted tickets for students", "suggested_price": 20.00},
        "Custom": {"description": "", "suggested_price": 50.00}
    }
    
    with st.form("add_ticket_type_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            type_selection = st.selectbox(
                "Ticket Type *",
                options=list(predefined_types.keys()),
                help="Select a predefined type or choose 'Custom' to create your own"
            )
            
            if type_selection == "Custom":
                name = st.text_input(
                    "Custom Type Name *",
                    placeholder="e.g., Family Pack",
                    help="Enter a custom name for this ticket type"
                )
            else:
                name = type_selection
                st.markdown(f"**Selected Type:** {name}")
        
        with col2:
            suggested_price = predefined_types[type_selection]["suggested_price"]
            price = st.number_input(
                "Price *",
                min_value=0.01,
                max_value=10000.00,
                value=suggested_price,
                step=0.01,
                format="%.2f",
                help="Enter the price for this ticket type"
            )
        
        # Description with suggested text
        suggested_description = predefined_types[type_selection]["description"]
        description = st.text_area(
            "Description",
            value=suggested_description,
            placeholder="Enter a description for this ticket type...",
            help="Optional description of the ticket type and its benefits",
            height=100
        )
        
        submitted = st.form_submit_button("🎟️ Create Ticket Type", use_container_width=True)
        
        if submitted:
            final_name = name if type_selection == "Custom" else type_selection
            
            if not final_name.strip():
                st.error("Please provide a name for the ticket type.")
            elif price <= 0:
                st.error("Price must be greater than 0.")
            else:
                ticket_type_data = {
                    "name": final_name.strip(),
                    "price": round(price, 2),
                    "description": description.strip() if description.strip() else None
                }
                
                with st.spinner("Creating ticket type..."):
                    result = create_ticket_type(ticket_type_data)
                    
                    if result:
                        st.success(f"✅ Ticket type '{final_name}' created successfully!")
                        st.balloons()
                        # Clear form by rerunning
                        st.rerun()
                    else:
                        st.error("❌ Failed to create ticket type. Please check if the name already exists.")


def show_edit_ticket_type_form():
    """Display form to edit an existing ticket type"""
    st.subheader("Edit Ticket Type")
    
    ticket_types = get_ticket_types()
    if not ticket_types:
        st.info("No ticket types available to edit.")
        return
    
    type_options = {f"{t['name']} - ${t['price']:.2f}": t['id'] for t in ticket_types}
    
    # Check if ticket type is selected from the list view
    default_type = None
    if hasattr(st.session_state, 'edit_ticket_type_id'):
        for name, tid in type_options.items():
            if tid == st.session_state.edit_ticket_type_id:
                default_type = name
                break
    
    selected_type_name = st.selectbox(
        "Select ticket type to edit:",
        options=list(type_options.keys()),
        index=list(type_options.keys()).index(default_type) if default_type else 0
    )
    
    if selected_type_name:
        type_id = type_options[selected_type_name]
        
        # Get current ticket type details
        current_type = next(t for t in ticket_types if t['id'] == type_id)
        
        with st.form("edit_ticket_type_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                new_name = st.text_input(
                    "Ticket Type Name *",
                    value=current_type['name'],
                    help="Update the name of this ticket type"
                )
            
            with col2:
                new_price = st.number_input(
                    "Price *",
                    min_value=0.01,
                    max_value=10000.00,
                    value=float(current_type['price']),
                    step=0.01,
                    format="%.2f",
                    help="Update the price for this ticket type"
                )
            
            new_description = st.text_area(
                "Description",
                value=current_type.get('description', ''),
                placeholder="Enter a description for this ticket type...",
                help="Update the description of the ticket type",
                height=100
            )
            
            submitted = st.form_submit_button("💾 Update Ticket Type", use_container_width=True)
            
            if submitted:
                if not new_name.strip():
                    st.error("Please provide a name for the ticket type.")
                elif new_price <= 0:
                    st.error("Price must be greater than 0.")
                else:
                    updated_data = {
                        "name": new_name.strip(),
                        "price": round(new_price, 2),
                        "description": new_description.strip() if new_description.strip() else None
                    }
                    
                    with st.spinner("Updating ticket type..."):
                        result = update_ticket_type(type_id, updated_data)
                        
                        if result:
                            st.success(f"✅ Ticket type '{new_name}' updated successfully!")
                            # Clear edit selection
                            if hasattr(st.session_state, 'edit_ticket_type_id'):
                                del st.session_state.edit_ticket_type_id
                            st.rerun()
                        else:
                            st.error("❌ Failed to update ticket type. Please check if the name conflicts with existing types.")
        
        # Clear edit selection
        if hasattr(st.session_state, 'edit_ticket_type_id'):
            if st.button("🔄 Cancel Edit"):
                del st.session_state.edit_ticket_type_id
                st.rerun()


def show_ticket_type_details():
    """Display detailed information about a selected ticket type"""
    st.subheader("Ticket Type Details")
    
    ticket_types = get_ticket_types()
    if not ticket_types:
        st.info("No ticket types available.")
        return
    
    type_options = {f"{t['name']} - ${t['price']:.2f}": t['id'] for t in ticket_types}
    
    # Check if ticket type is selected from the list view
    default_type = None
    if hasattr(st.session_state, 'selected_ticket_type_id'):
        for name, tid in type_options.items():
            if tid == st.session_state.selected_ticket_type_id:
                default_type = name
                break
    
    selected_type_name = st.selectbox(
        "Select a ticket type to view details:",
        options=list(type_options.keys()),
        index=list(type_options.keys()).index(default_type) if default_type else 0
    )
    
    if selected_type_name:
        type_id = type_options[selected_type_name]
        
        # Get ticket type details - Feature temporarily unavailable
        # type_details = get_ticket_type_details(type_id)
        # if not type_details:
        #     st.error("Failed to load ticket type details.")
        #     return
        
        # Temporary workaround - get basic info from ticket types list
        ticket_types = get_ticket_types()
        type_details = next((t for t in ticket_types if t['id'] == type_id), None)
        if not type_details:
            st.error("Failed to load ticket type details.")
            return
        
        # Display ticket type information
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🎟️ Ticket Type Information")
            
            # Color coding based on ticket type
            type_colors = {
                'VIP': '🟣',
                'Premium': '🟠',
                'Standard': '🔵',
                'Economy': '🟢',
                'Student': '🟡'
            }
            type_icon = type_colors.get(type_details['name'], '⚪')
            
            st.markdown(f"**Name:** {type_icon} {type_details['name']}")
            st.markdown(f"**Price:** ${type_details['price']:.2f}")
            if type_details.get('description'):
                st.markdown(f"**Description:** {type_details['description']}")
            st.markdown(f"**Created:** {type_details['created_at'][:10]}")
        
        with col2:
            # Get statistics for this ticket type
            stats = get_ticket_type_stats(type_id)
            if stats:
                st.markdown("### 📊 Performance Statistics")
                st.markdown(f"**Total Bookings:** {stats['total_bookings']:,}")
                st.markdown(f"**Tickets Sold:** {stats['total_tickets_sold']:,}")
                st.markdown(f"**Total Revenue:** ${stats['total_revenue']:.2f}")
                
                if stats.get('market_share_percentage'):
                    st.markdown(f"**Market Share:** {stats['market_share_percentage']:.1f}%")
                if stats.get('revenue_share_percentage'):
                    st.markdown(f"**Revenue Share:** {stats['revenue_share_percentage']:.1f}%")
                
                # Status breakdown
                if stats.get('booking_status_breakdown'):
                    st.markdown("**Booking Status Breakdown:**")
                    for status, data in stats['booking_status_breakdown'].items():
                        st.markdown(f"  - {status.title()}: {data['count']} bookings (${data['revenue']:.2f})")
            else:
                st.markdown("### 📊 Performance Statistics")
                st.info("No bookings yet for this ticket type.")
        
        # Bookings for this ticket type - Feature temporarily unavailable
        st.markdown("### 📋 Recent Bookings")
        # type_bookings = get_ticket_type_bookings(type_id)
        type_bookings = []  # Temporarily disabled
        
        if type_bookings:
            bookings_df = pd.DataFrame(type_bookings)
            
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
            
            # Display recent bookings
            st.markdown("#### Recent Bookings (Last 10)")
            for idx, booking in bookings_df.head(10).iterrows():
                with st.container():
                    col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
                    
                    with col1:
                        st.markdown(f"**{booking['customer_name']}**")
                        st.markdown(f"📧 {booking['customer_email']}")
                    
                    with col2:
                        st.markdown(f"🎭 **{booking['event_name']}**")
                        st.markdown(f"🏟️ {booking['venue_name']}")
                    
                    with col3:
                        status_colors = {
                            'confirmed': '🟢',
                            'pending': '🟡',
                            'cancelled': '🔴'
                        }
                        status_icon = status_colors.get(booking['status'], '⚪')
                        st.markdown(f"{status_icon} {booking['status'].title()}")
                        st.markdown(f"🎫 x{booking['quantity']}")
                    
                    with col4:
                        st.markdown(f"**${booking['total_price']:.2f}**")
                        st.markdown(f"🗓️ {booking['booking_date'][:10]}")
                    
                    st.markdown("---")
            
            if len(bookings_df) > 10:
                st.info(f"Showing 10 of {len(bookings_df)} bookings. Use the Bookings page to view all.")
            
            # Booking trend chart if there are multiple bookings
            if len(bookings_df) > 1:
                st.markdown("#### 📈 Booking Trend")
                bookings_df['booking_date'] = pd.to_datetime(bookings_df['booking_date'])
                daily_bookings = bookings_df.groupby(bookings_df['booking_date'].dt.date).agg({
                    'quantity': 'sum',
                    'total_price': 'sum'
                }).reset_index()
                
                fig = px.line(
                    daily_bookings,
                    x='booking_date',
                    y='quantity',
                    title=f"Daily Ticket Sales for {type_details['name']}",
                    markers=True
                )
                fig.update_layout(
                    xaxis_title="Date",
                    yaxis_title="Tickets Sold",
                    hovermode="x unified"
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No bookings for this ticket type yet.")
        
        # Clear selected ticket type from session state
        if hasattr(st.session_state, 'selected_ticket_type_id'):
            if st.button("🔄 Clear Selection"):
                del st.session_state.selected_ticket_type_id
                st.rerun()