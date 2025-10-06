"""
CMU Transportation Comparison Tool
A Streamlit web application for comparing shuttle, public transit, and ride-sharing options.
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from scraper import CMUShuttleScraper
from google_transit import GoogleTransitAPI, get_mock_transit_data
from uber_api import UberAPI, get_mock_uber_estimates
from utils import (
    get_day_of_week, 
    format_duration, 
    calculate_cost_savings,
    calculate_time_savings,
    CMU_LOCATIONS,
    get_current_day_type
)

# Page configuration
st.set_page_config(
    page_title="CMU Transportation Comparison",
    page_icon="🚌",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main {
        padding: 0rem 1rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 1rem 2rem;
        font-size: 1.1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .route-card {
        border: 1px solid #e0e0e0;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 0.5rem 0;
        background-color: white;
    }
    h1 {
        color: #c41230;
        padding-bottom: 1rem;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 1rem 0;
    }
    .info-box {
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 1rem 0;
    }
    </style>
    """, unsafe_allow_html=True)


def initialize_session_state():
    """Initialize session state variables."""
    if 'shuttle_data' not in st.session_state:
        st.session_state.shuttle_data = None
    if 'last_fetch' not in st.session_state:
        st.session_state.last_fetch = None
    if 'use_mock_data' not in st.session_state:
        st.session_state.use_mock_data = True


def display_header():
    """Display the app header."""
    st.title("🚌 CMU Transportation Comparison Tool")
    st.markdown("**Compare shuttle, public transit, and ride-sharing options for Carnegie Mellon University**")
    st.markdown("---")


def fetch_shuttle_data():
    """Fetch shuttle schedule data."""
    with st.spinner("Fetching shuttle schedules..."):
        scraper = CMUShuttleScraper()
        data = scraper.get_all_shuttle_data()
        
        if data['success']:
            st.session_state.shuttle_data = data
            st.session_state.last_fetch = datetime.now()
            return True
        else:
            st.error(f"Failed to fetch shuttle data: {data.get('error', 'Unknown error')}")
            return False


def display_shuttle_schedules():
    """Display shuttle schedules in an organized manner."""
    st.header("📅 Shuttle Schedules")
    
    if st.button("🔄 Refresh Shuttle Data", type="primary"):
        fetch_shuttle_data()
    
    if st.session_state.shuttle_data is None:
        fetch_shuttle_data()
    
    if st.session_state.shuttle_data and st.session_state.shuttle_data['success']:
        data = st.session_state.shuttle_data
        
        # Display last update time
        if st.session_state.last_fetch:
            st.caption(f"Last updated: {st.session_state.last_fetch.strftime('%I:%M %p')}")
        
        # Current day info
        current_day = get_day_of_week()
        day_type = get_current_day_type()
        
        st.markdown(f"""
        <div class="info-box">
            <strong>Today:</strong> {current_day} ({day_type.title()})
        </div>
        """, unsafe_allow_html=True)
        
        # Display routes
        st.subheader("🗺️ Available Routes")
        routes = data.get('routes', {})
        
        if routes:
            for route_name, route_info in routes.items():
                with st.expander(f"📍 {route_name}"):
                    if 'description' in route_info:
                        st.write(f"**Description:** {route_info['description']}")
                    if 'path' in route_info:
                        st.write(f"**Route Path:**")
                        st.code(route_info['path'], language=None)
        else:
            st.info("Route information will be displayed here once available.")
        
        # Display schedules
        st.subheader("⏰ Schedule Tables")
        schedules = data.get('schedules', {})
        
        if schedules:
            # Organize schedules by type
            schedule_tabs = st.tabs(["A/B/AB Routes", "C Route", "PTC & Mill 19", "Bakery Square"])
            
            with schedule_tabs[0]:
                st.markdown("### A, B, and AB Routes (Shadyside)")
                if 'A_B_AB_Routes_Weekday' in schedules:
                    st.write("**Monday - Friday:**")
                    st.dataframe(schedules['A_B_AB_Routes_Weekday'], use_container_width=True)
                if 'A_B_AB_Routes_Weekend' in schedules:
                    st.write("**Saturday & Sunday:**")
                    st.dataframe(schedules['A_B_AB_Routes_Weekend'], use_container_width=True)
            
            with schedule_tabs[1]:
                st.markdown("### C Route (Squirrel Hill)")
                if 'C_Route_Weekday' in schedules:
                    st.write("**Monday - Friday:**")
                    st.dataframe(schedules['C_Route_Weekday'], use_container_width=True)
                else:
                    st.info("No weekend service for C Route")
            
            with schedule_tabs[2]:
                st.markdown("### PTC & Mill 19 Routes")
                if 'PTC_Mill19_Weekday' in schedules:
                    st.write("**Monday - Friday:**")
                    st.dataframe(schedules['PTC_Mill19_Weekday'], use_container_width=True)
                if 'PTC_Mill19_Weekend' in schedules:
                    st.write("**Saturday & Sunday:**")
                    st.dataframe(schedules['PTC_Mill19_Weekend'], use_container_width=True)
            
            with schedule_tabs[3]:
                st.markdown("### Bakery Square Routes")
                if 'Bakery_Square_Weekday' in schedules:
                    st.write("**Monday - Friday:**")
                    st.dataframe(schedules['Bakery_Square_Weekday'], use_container_width=True)
                else:
                    st.info("Bakery Square route operates Monday-Friday only")
        
        # Link to live tracker
        st.markdown("---")
        st.markdown("""
        ### 📱 Live Bus Tracking
        Track shuttles in real-time using the **TripShot app** or view the 
        [web tracker](https://cmu.tripshot.com).
        """)
    else:
        st.warning("Unable to load shuttle data. Please try refreshing.")


def display_comparison_tool():
    """Display the comparison tool interface."""
    st.header("🔍 Compare Transportation Options")
    
    st.markdown("""
    <div class="info-box">
        Compare travel times and costs between CMU shuttles, public transit (Port Authority), 
        and ride-sharing services (Uber).
    </div>
    """, unsafe_allow_html=True)
    
    # Location selection
    col1, col2 = st.columns(2)
    
    with col1:
        origin = st.selectbox(
            "📍 Starting Location",
            options=list(CMU_LOCATIONS.keys()),
            index=0
        )
        st.caption(f"Address: {CMU_LOCATIONS[origin]['address']}")
    
    with col2:
        destination = st.selectbox(
            "🎯 Destination",
            options=list(CMU_LOCATIONS.keys()),
            index=3  # Default to Shadyside
        )
        st.caption(f"Address: {CMU_LOCATIONS[destination]['address']}")
    
    # Time selection
    col1, col2 = st.columns(2)
    with col1:
        travel_date = st.date_input("📅 Date", datetime.now())
    with col2:
        travel_time = st.time_input("⏰ Time", datetime.now().time())
    
    # API Configuration
    with st.expander("⚙️ API Configuration (Optional)"):
        st.markdown("""
        Enter your API keys to get real-time data. If left empty, mock data will be used for demonstration.
        """)
        google_api_key = st.text_input("Google Maps API Key", type="password")
        uber_token = st.text_input("Uber API Token", type="password")
        
        if google_api_key or uber_token:
            st.session_state.use_mock_data = False
        else:
            st.session_state.use_mock_data = True
    
    if st.button("🔎 Compare Options", type="primary", use_container_width=True):
        compare_transportation_options(origin, destination, travel_date, travel_time)


def compare_transportation_options(origin, destination, travel_date, travel_time):
    """Compare different transportation options."""
    
    st.markdown("---")
    st.subheader("📊 Comparison Results")
    
    # Create three columns for results
    col1, col2, col3 = st.columns(3)
    
    # CMU Shuttle
    with col1:
        st.markdown("### 🚌 CMU Shuttle")
        st.markdown('<div class="route-card">', unsafe_allow_html=True)
        st.metric("Cost", "$0.00", "Free for CMU!")
        st.metric("Estimated Time", "15-20 mins", help="Approximate based on route")
        st.success("✅ Available")
        st.markdown("**Benefits:**")
        st.markdown("- Free with CMU ID\n- Direct campus routes\n- Frequent service")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Public Transit
    with col2:
        st.markdown("### 🚍 Public Transit")
        st.markdown('<div class="route-card">', unsafe_allow_html=True)
        
        if st.session_state.use_mock_data:
            transit_data = get_mock_transit_data(origin, destination)
            st.info("Using mock data (no API key provided)")
        else:
            # Use real API
            google_api = GoogleTransitAPI()
            transit_data = google_api.get_transit_directions(
                CMU_LOCATIONS[origin]['address'],
                CMU_LOCATIONS[destination]['address']
            )
        
        if transit_data['success'] and transit_data['routes']:
            route = transit_data['routes'][0]
            st.metric("Cost", "$2.75", "Standard fare")
            st.metric("Travel Time", route['duration'])
            st.metric("Distance", route['distance'])
            
            with st.expander("View Route Details"):
                for step in route['steps']:
                    st.write(f"**{step['travel_mode']}** - {step['duration']}")
                    if 'transit' in step:
                        st.write(f"  Line: {step['transit']['line']}")
                        st.write(f"  From: {step['transit']['departure_stop']}")
                        st.write(f"  To: {step['transit']['arrival_stop']}")
        else:
            st.warning("Transit data unavailable")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Uber
    with col3:
        st.markdown("### 🚗 Uber")
        st.markdown('<div class="route-card">', unsafe_allow_html=True)
        
        if st.session_state.use_mock_data:
            uber_data = get_mock_uber_estimates(origin, destination)
            st.info("Using mock data (no API key provided)")
        else:
            # Use real API
            uber_api = UberAPI()
            origin_coords = CMU_LOCATIONS[origin]
            dest_coords = CMU_LOCATIONS[destination]
            uber_data = uber_api.get_price_estimates(
                origin_coords['lat'], origin_coords['lon'],
                dest_coords['lat'], dest_coords['lon']
            )
        
        if uber_data['success'] and uber_data['estimates']:
            for estimate in uber_data['estimates'][:3]:  # Show top 3 options
                with st.expander(f"{estimate['product_name']}"):
                    st.metric("Estimate", estimate['estimate'])
                    st.metric("Duration", format_duration(estimate['duration']))
                    st.metric("Distance", f"{estimate['distance']:.1f} miles")
                    if estimate['surge_multiplier'] > 1:
                        st.warning(f"⚠️ Surge pricing: {estimate['surge_multiplier']}x")
        else:
            st.warning("Uber data unavailable")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Summary comparison
    st.markdown("---")
    st.subheader("💡 Summary & Recommendations")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div class="success-box">
        <strong>💰 Best Value:</strong> CMU Shuttle (Free!)<br>
        <strong>⚡ Fastest:</strong> Uber (13 mins)<br>
        <strong>🌱 Most Sustainable:</strong> Public Transit / Shuttle
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        **Recommendation:**
        - Use **CMU Shuttle** when schedules align - it's free!
        - **Public Transit** is affordable and reliable
        - **Uber** for urgent trips or off-peak hours
        """)


def display_about():
    """Display about information."""
    st.header("ℹ️ About")
    
    st.markdown("""
    ### CMU Transportation Comparison Tool
    
    This tool helps Carnegie Mellon University students, faculty, and staff make informed 
    decisions about transportation options around Pittsburgh.
    
    #### Features:
    - 📅 **Live Shuttle Schedules**: Real-time CMU shuttle timings scraped from official sources
    - 🚍 **Public Transit Comparison**: Compare with Port Authority bus/transit options
    - 🚗 **Ride-sharing Estimates**: Get Uber pricing and timing estimates
    - 💰 **Cost Analysis**: See how much you can save with different options
    - ⏱️ **Time Comparison**: Find the fastest route for your journey
    
    #### Data Sources:
    - CMU Shuttle schedules: [CMU Transportation Services](https://www.cmu.edu/transportation/transport/shuttle.html)
    - Public transit: Google Maps API
    - Ride-sharing: Uber API
    
    #### How to Use:
    1. Check shuttle schedules in the **Shuttle Schedules** tab
    2. Use the **Compare** tab to compare all transportation options
    3. Optionally add your own API keys for real-time data
    
    #### Technologies:
    - **Frontend**: Streamlit (Python)
    - **Web Scraping**: BeautifulSoup4, Requests
    - **Data Processing**: Pandas
    - **APIs**: Google Maps, Uber
    
    ---
    
    Made with ❤️ for the CMU community
    
    *Version 0.1.0*
    """)


def main():
    """Main application entry point."""
    initialize_session_state()
    display_header()
    
    # Sidebar
    with st.sidebar:
        st.markdown("## 🎓 CMU Transport")
        st.markdown("*Transportation Comparison Tool*")
        st.markdown("---")
        
        st.markdown("### 🎯 Quick Links")
        st.markdown("""
        - [TripShot Bus Tracker](https://cmu.tripshot.com)
        - [CMU Transportation](https://www.cmu.edu/transportation/)
        - [Port Authority](https://www.portauthority.org/)
        """)
        
        st.markdown("---")
        st.markdown("### 📞 Contact")
        st.markdown("""
        **Transportation Services**  
        📧 transportation@andrew.cmu.edu  
        📞 (412) 268-2052
        """)
        
        st.markdown("---")
        current_time = datetime.now().strftime("%I:%M %p")
        current_day = get_day_of_week()
        st.caption(f"🕐 {current_time}")
        st.caption(f"📅 {current_day}")
    
    # Main content tabs
    tab1, tab2, tab3 = st.tabs(["📅 Shuttle Schedules", "🔍 Compare Options", "ℹ️ About"])
    
    with tab1:
        display_shuttle_schedules()
    
    with tab2:
        display_comparison_tool()
    
    with tab3:
        display_about()
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 1rem;'>
        <small>
        CMU Transportation Comparison Tool | Data updated in real-time<br>
        Not affiliated with CMU Transportation Services - For informational purposes only
        </small>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
