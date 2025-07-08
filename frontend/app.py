import streamlit as st
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pages.dashboard import show_dashboard
from pages.venues import show_venues
from pages.events import show_events
from pages.bookings import show_bookings
from pages.ticket_types import show_ticket_types
from utils.api_client import check_api_health, display_api_status, get_cache_stats


def main():
    """Main Streamlit application"""
    # Page configuration
    st.set_page_config(
        page_title="Ticket Booking System",
        page_icon="🎫",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS for better styling
    st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
        padding: 1rem;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
    }
    
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
    }
    
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #1f77b4;
    }
    
    .status-confirmed {
        color: #28a745;
        font-weight: bold;
    }
    
    .status-pending {
        color: #ffc107;
        font-weight: bold;
    }
    
    .status-cancelled {
        color: #dc3545;
        font-weight: bold;
    }
    
    .stButton > button {
        width: 100%;
        border-radius: 5px;
        border: none;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        font-weight: bold;
    }
    
    .stButton > button:hover {
        background: linear-gradient(90deg, #764ba2 0%, #667eea 100%);
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown('<div class="main-header">🎫 Ticket Booking System</div>', unsafe_allow_html=True)
    
    # Sidebar navigation
    with st.sidebar:
        st.markdown("## 🧭 Navigation")
        
        # Enhanced API status monitoring
        display_api_status()
        
        # Navigation menu
        page = st.selectbox(
            "Select Page:",
            [
                "📊 Dashboard",
                "🏟️ Venues",
                "🎭 Events",
                "🎫 Bookings",
                "🎟️ Ticket Types"
            ],
            index=0
        )
        
        st.markdown("---")
        
        # Quick stats in sidebar
        st.markdown("### 📈 Quick Stats")
        try:
            from utils.api_client import get_stats
            stats = get_stats()
            if stats:
                st.metric("Total Events", stats["overview"]["total_events"])
                st.metric("Total Bookings", stats["overview"]["total_bookings"])
                st.metric("Total Revenue", f"${stats['revenue']['total_revenue']:,.2f}")
            else:
                st.info("Stats unavailable")
        except Exception as e:
            st.info("Stats loading...")
        
        st.markdown("---")
        
        # System information
        st.markdown("### ℹ️ System Info")
        st.markdown("""
        **Version:** 1.0.0  
        **Backend:** FastAPI  
        **Database:** SQLite  
        **Frontend:** Streamlit  
        
        **Features:**
        - 🏟️ Venue Management
        - 🎭 Event Scheduling
        - 🎫 Booking System
        - 🎟️ Ticket Types
        - 📊 Analytics Dashboard
        """)
        
        st.markdown("---")
        
        # Help section
        with st.expander("❓ Help & Support"):
            st.markdown("""
            **Getting Started:**
            1. Add venues first
            2. Create events for venues
            3. Set up ticket types
            4. Start taking bookings!
            
            **Need Help?**
            - Check the dashboard for overview
            - Use search in bookings
            - View detailed analytics
            
            **Troubleshooting:**
            - Ensure backend is running
            - Check network connection
            - Refresh the page if needed
            """)
    
    # Main content area
    if page == "📊 Dashboard":
        show_dashboard()
    elif page == "🏟️ Venues":
        show_venues()
    elif page == "🎭 Events":
        show_events()
    elif page == "🎫 Bookings":
        show_bookings()
    elif page == "🎟️ Ticket Types":
        show_ticket_types()
    
    # Footer
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(
            "<div style='text-align: center; color: #666; font-size: 0.8rem;'>"
            "🎫 Ticket Booking System | Built with FastAPI & Streamlit | © 2024"
            "</div>",
            unsafe_allow_html=True
        )


if __name__ == "__main__":
    main()