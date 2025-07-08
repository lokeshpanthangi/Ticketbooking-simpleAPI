import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from ..utils.api_client import (
    get_stats,
    get_popular_events,
    get_busiest_venues,
    get_revenue_by_month,
    get_bookings
)


def show_dashboard():
    """Display the main dashboard with key metrics and charts"""
    st.title("📊 Dashboard")
    st.markdown("Welcome to the Ticket Booking System Dashboard")
    
    # Get system statistics
    stats = get_stats()
    if not stats:
        st.error("Failed to load dashboard data")
        return
    
    # Key Metrics Row
    st.subheader("📈 Key Metrics")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Total Events",
            value=stats["overview"]["total_events"],
            delta=None
        )
    
    with col2:
        st.metric(
            label="Total Venues",
            value=stats["overview"]["total_venues"],
            delta=None
        )
    
    with col3:
        st.metric(
            label="Total Bookings",
            value=stats["overview"]["total_bookings"],
            delta=None
        )
    
    with col4:
        st.metric(
            label="Total Revenue",
            value=f"${stats['revenue']['total_revenue']:,.2f}",
            delta=f"${stats['revenue']['pending_revenue']:,.2f} pending"
        )
    
    # Revenue and Booking Status
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("💰 Revenue Breakdown")
        revenue_data = {
            "Status": ["Confirmed", "Pending"],
            "Revenue": [
                stats["revenue"]["confirmed_revenue"],
                stats["revenue"]["pending_revenue"]
            ]
        }
        
        if sum(revenue_data["Revenue"]) > 0:
            fig_revenue = px.pie(
                values=revenue_data["Revenue"],
                names=revenue_data["Status"],
                title="Revenue by Status",
                color_discrete_map={"Confirmed": "#2E8B57", "Pending": "#FFD700"}
            )
            st.plotly_chart(fig_revenue, use_container_width=True)
        else:
            st.info("No revenue data available")
    
    with col2:
        st.subheader("📋 Booking Status Distribution")
        if stats["booking_status_breakdown"]:
            status_data = []
            for status, data in stats["booking_status_breakdown"].items():
                status_data.append({
                    "Status": status.title(),
                    "Count": data["count"],
                    "Revenue": data["revenue"]
                })
            
            if status_data:
                df_status = pd.DataFrame(status_data)
                fig_status = px.bar(
                    df_status,
                    x="Status",
                    y="Count",
                    title="Bookings by Status",
                    color="Status",
                    color_discrete_map={
                        "Confirmed": "#2E8B57",
                        "Pending": "#FFD700",
                        "Cancelled": "#DC143C"
                    }
                )
                st.plotly_chart(fig_status, use_container_width=True)
            else:
                st.info("No booking status data available")
        else:
            st.info("No booking data available")
    
    # Popular Events and Busiest Venues
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🔥 Popular Events")
        popular_events = get_popular_events(limit=5)
        if popular_events:
            events_df = pd.DataFrame(popular_events)
            if not events_df.empty:
                # Display as a styled table
                for idx, event in events_df.iterrows():
                    with st.container():
                        st.markdown(f"**{event['event_name']}**")
                        st.markdown(f"📍 {event['venue_name']}, {event['venue_city']}")
                        st.markdown(f"🎫 {event['total_tickets']} tickets | 💰 ${event['total_revenue']:.2f}")
                        st.markdown("---")
            else:
                st.info("No popular events data available")
        else:
            st.info("No events data available")
    
    with col2:
        st.subheader("🏟️ Busiest Venues")
        busiest_venues = get_busiest_venues(limit=5)
        if busiest_venues:
            venues_df = pd.DataFrame(busiest_venues)
            if not venues_df.empty:
                # Display as a styled table
                for idx, venue in venues_df.iterrows():
                    with st.container():
                        st.markdown(f"**{venue['venue_name']}**")
                        st.markdown(f"📍 {venue['city']}")
                        st.markdown(f"🎪 {venue['event_count']} events | 🎫 {venue['total_tickets']} tickets")
                        st.markdown(f"📊 {venue['occupancy_rate']:.1f}% occupancy | 💰 ${venue['total_revenue']:.2f}")
                        st.markdown("---")
            else:
                st.info("No venue data available")
        else:
            st.info("No venues data available")
    
    # Revenue Trend Chart
    st.subheader("📈 Revenue Trend by Month")
    monthly_revenue = get_revenue_by_month()
    if monthly_revenue:
        df_monthly = pd.DataFrame(monthly_revenue)
        if not df_monthly.empty:
            fig_trend = px.line(
                df_monthly,
                x="month",
                y="revenue",
                title="Monthly Revenue Trend",
                markers=True
            )
            fig_trend.update_layout(
                xaxis_title="Month",
                yaxis_title="Revenue ($)",
                hovermode="x unified"
            )
            st.plotly_chart(fig_trend, use_container_width=True)
        else:
            st.info("No monthly revenue data available")
    else:
        st.info("No revenue trend data available")
    
    # Recent Bookings
    st.subheader("📋 Recent Bookings")
    recent_bookings = get_bookings()
    if recent_bookings:
        # Sort by booking date and take the most recent 10
        df_bookings = pd.DataFrame(recent_bookings)
        if not df_bookings.empty:
            df_bookings['booking_date'] = pd.to_datetime(df_bookings['booking_date'])
            df_recent = df_bookings.sort_values('booking_date', ascending=False).head(10)
            
            # Display in a nice format
            for idx, booking in df_recent.iterrows():
                col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
                
                with col1:
                    st.markdown(f"**{booking['customer_name']}**")
                    st.markdown(f"📧 {booking['customer_email']}")
                
                with col2:
                    st.markdown(f"🎭 {booking['event_name']}")
                    st.markdown(f"📍 {booking['venue_name']}")
                
                with col3:
                    status_color = {
                        'confirmed': '🟢',
                        'pending': '🟡',
                        'cancelled': '🔴'
                    }
                    st.markdown(f"{status_color.get(booking['status'], '⚪')} {booking['status'].title()}")
                    st.markdown(f"🎫 {booking['quantity']} tickets")
                
                with col4:
                    st.markdown(f"**${booking['total_price']:.2f}**")
                    st.markdown(f"🗓️ {booking['booking_date'].strftime('%m/%d/%Y')}")
                
                st.markdown("---")
        else:
            st.info("No recent bookings available")
    else:
        st.info("No bookings data available")
    
    # Auto-refresh option
    if st.button("🔄 Refresh Dashboard"):
        st.experimental_rerun()