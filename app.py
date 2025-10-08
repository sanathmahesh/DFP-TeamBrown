"""
CMU Transportation Comparison Tool
A Streamlit web application for comparing shuttle, public transit, and ride-sharing options.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import sys
import os
from typing import Optional, Tuple
import importlib
import math
import pydeck as pdk

try:
    # Load environment variables from a .env file if present
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except Exception:
    # dotenv is optional; app still works without it
    pass

# Optional config.py support (keys can be stored there locally)
try:  # pragma: no cover - optional file
    import config  # type: ignore
except Exception:
    config = None  # type: ignore

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from scraper import CMUShuttleScraper
from google_transit import GoogleTransitAPI, get_mock_transit_data
from uber_api import UberAPI, get_mock_uber_estimates
from shuttle_routing import plan_shuttle_trip
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
    :root {
        --cmu-red: #C41230;
        --cmu-gray: #F5F6F9;
        --cmu-dark: #1B1B1B;
        --cmu-light: #FFFFFF;
    }

    /* ====== GLOBAL BACKGROUND ====== */
    .stApp, .main, .block-container {
        background-color: var(--cmu-gray) !important;
        color: var(--cmu-dark);
    }
    
    

    /* ====== HERO / TITLE SECTION ====== */
    div:has(> h1:contains("CMU Transportation Comparison Tool")) {
        background-color: var(--cmu-gray) !important;
        color: var(--cmu-dark) !important;
        border-radius: 0 !important;
        padding: 1rem 0 !important;
        box-shadow: none !important;
    }

    h1, h2, h3, h4 {
        color: var(--cmu-dark) !important;
        font-weight: 700;
    }

    /* ====== BUTTONS ====== */
    .stButton>button {
        background-color: var(--cmu-red) !important;
        color: var(--cmu-light) !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        border: none !important;
        padding: 0.6rem 1.2rem !important;
        transition: all 0.2s ease;
    }
    .stButton>button:hover {
        background-color: #a11126 !important;
        transform: translateY(-1px);
    }

    /* ====== ROUTE & INFO BOXES ====== */
    .route-card {
        background-color: #ffffff;
        padding: 1.5rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        border: 1px solid #ddd;
        box-shadow: 0 2px 6px rgba(0,0,0,0.05);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .route-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 10px rgba(0,0,0,0.1);
    }
    .success-box {
        background-color: #e8f5e9;
        padding: 1rem;
        border-radius: 8px;
        border-left: 5px solid #4caf50;
        margin-bottom: 1rem;
    }
    .info-box {
        background-color: #e3f2fd;
        padding: 1rem;
        border-radius: 8px;
        border-left: 5px solid #2196f3;
        margin-bottom: 1rem;
    }

    /* ====== METRICS ====== */
    [data-testid="stMetricValue"] {
        color: var(--cmu-dark) !important;
        font-size: 1.5rem !important;
        font-weight: 600;
    }

    /* ====== TABS ====== */
    .stTabs [role="tablist"] {
        border-bottom: 2px solid #ccc;
    }
    .stTabs [role="tab"][aria-selected="true"] {
        border-bottom: 3px solid #444 !important;
        font-weight: 600 !important;
        color: var(--cmu-dark) !important;
    }

    /* ====== EXPANDER ====== */
    .streamlit-expanderHeader {
        font-weight: 600;
    }

    /* ====== DIVIDERS ====== */
    hr {
        border: 0;
        height: 1px;
        background-color: #ddd;
        margin: 2rem 0;
    }

    /* ====== SIDEBAR BASE ====== */
section[data-testid="stSidebar"] {
    background-color: #2E2E2E !important;
    color: #FFFFFF !important;
    padding-top: 0 !important;
    border-right: none !important;
}

/* ====== LOGO AREA ====== */
section[data-testid="stSidebar"] div[data-testid="stSidebarNav"] {
    background-color: #C41230 !important;
    padding: 1rem 0.5rem !important;
    text-align: center;
}
section[data-testid="stSidebar"] img {
    width: 160px !important;
    border-radius: 4px;
}

/* ====== TITLES ====== */
section[data-testid="stSidebar"] h3, 
section[data-testid="stSidebar"] h4 {
    color: #FFFFFF !important;
    text-align: center;
    margin-bottom: 0.4rem;
}
section[data-testid="stSidebar"] p {
    color: #CCCCCC !important;
    font-size: 0.9rem;
    text-align: center;
    margin-bottom: 1rem;
}

/* ====== LINKS ====== */
section[data-testid="stSidebar"] a {
    color: #FFFFFF !important;
    text-decoration: none !important;
    font-weight: 500;
    display: block;
    padding: 0.4rem 0.6rem;
    border-radius: 6px;
    transition: all 0.2s ease-in-out;
}
section[data-testid="stSidebar"] a:hover {
    background-color: #C41230 !important;
}

/* ====== DIVIDERS ====== */
section[data-testid="stSidebar"] hr {
    border: none !important;
    border-top: 1px solid #444 !important;
    margin: 1.2rem 0 !important;
}

/* ====== ICONS & HEADERS ====== */
section[data-testid="stSidebar"] h4::before {
    margin-right: 6px;
}

/* ====== CONTACT SECTION ====== */
section[data-testid="stSidebar"] .contact-section p {
    text-align: left;
    margin: 0.2rem 0;
}
    </style>
""", unsafe_allow_html=True)






def initialize_session_state():
    """Initialize session state variables."""
    if 'shuttle_data' not in st.session_state:
        st.session_state.shuttle_data = None
    if 'last_fetch' not in st.session_state:
        st.session_state.last_fetch = None
    # Legacy flag retained for backward compatibility; per-service mock fallback is used now
    if 'use_mock_data' not in st.session_state:
        st.session_state.use_mock_data = True


def resolve_api_keys(
    google_api_key_input: Optional[str],
    uber_token_input: Optional[str]
) -> Tuple[Optional[str], Optional[str]]:
    """Resolve API keys from UI input, environment variables, or config.py.

    Precedence: UI input > config.py > environment variables
    """
    # Google Maps API key resolution
    google_key: Optional[str] = None
    if google_api_key_input and google_api_key_input.strip():
        google_key = google_api_key_input.strip()
    elif config is not None and getattr(config, 'GOOGLE_MAPS_API_KEY', None):
        google_key = getattr(config, 'GOOGLE_MAPS_API_KEY')
    elif os.getenv('GOOGLE_MAPS_API_KEY'):
        google_key = os.getenv('GOOGLE_MAPS_API_KEY')

    # Uber access token resolution
    uber_token: Optional[str] = None
    if uber_token_input and uber_token_input.strip():
        uber_token = uber_token_input.strip()
    elif config is not None and getattr(config, 'UBER_ACCESS_TOKEN', None):
        uber_token = getattr(config, 'UBER_ACCESS_TOKEN')
    elif os.getenv('UBER_ACCESS_TOKEN'):
        uber_token = os.getenv('UBER_ACCESS_TOKEN')

    return google_key, uber_token


def get_address_suggestions(query: str, api_key: Optional[str]) -> list:
    """Return address suggestions using Google Places Autocomplete if available."""
    if not api_key or not query or len(query.strip()) < 3:
        return []
    try:
        googlemaps = importlib.import_module('googlemaps')
        client = googlemaps.Client(key=api_key)
        # Bias around CMU campus
        location_bias = (40.4433, -79.9436)
        predictions = client.places_autocomplete(
            input_text=query.strip(),
            location=location_bias,
            radius=8000,
            types=None
        )
        return [p.get('description') for p in predictions][:5]
    except Exception:
        return []

def recommend_shuttle_route(origin_label: str, destination_label: str) -> Tuple[Optional[str], str]:
    """Heuristic recommendation for the best/fastest CMU shuttle route.

    For preset CMU locations and common neighborhoods, map to the appropriate route.
    For Shadyside, recommend A/B/AB (closest stop). For unknown areas, return None.
    """
    text = f"{origin_label} -> {destination_label}".lower()

    def is_match(s: str) -> bool:
        return s.lower() in text

    # Bakery Square
    if is_match('bakery square') or is_match('6425 penn'):
        return 'Bakery Square', 'Direct Bakery Square shuttle (weekday)'

    # PTC / Mill 19
    if is_match('ptc') or is_match('technology drive') or is_match('mill 19'):
        return 'PTC & Mill 19', 'PTC & Mill 19 shuttle (weekday)'

    # Squirrel Hill
    if is_match('squirrel hill') or is_match('murray ave'):
        return 'C Route', 'C Route to Squirrel Hill'

    # Shadyside (A/B/AB)
    if is_match('shadyside') or is_match('centre ave') or is_match('aiken'):
        return 'A/B/AB', 'Use A, B, or AB (closest stop)'

    # Campus to campus (no shuttle needed)
    if is_match('main campus') and ('main campus' in destination_label.lower() or 'forbes ave' in destination_label.lower()):
        return None, 'On-campus travel: walk or campus shuttle as needed'

    return None, 'No direct shuttle match; consider transit or Uber'


# Minimal set of common CMU shuttle stops (name, lat, lon)
SHUTTLE_STOPS = [
    { 'name': 'Morewood & Forbes (Main Campus)', 'lat': 40.4449, 'lon': -79.9429 },
    { 'name': 'Fifth Ave & Aiken Ave (Shadyside)', 'lat': 40.4520, 'lon': -79.9392 },
    { 'name': 'Bakery Square (Penn Ave)', 'lat': 40.4633, 'lon': -79.9214 },
    { 'name': 'PTC (Technology Dr)', 'lat': 40.4542, 'lon': -79.9196 },
    { 'name': 'Mill 19 (Hazelwood Green)', 'lat': 40.4288, 'lon': -79.9465 },
]


def haversine_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return great-circle distance in miles between two points."""
    R = 3958.8
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def geocode_address(address: str, api_key: Optional[str]) -> Optional[Tuple[float, float]]:
    """Geocode an address to (lat, lon) using Google Geocoding via googlemaps client."""
    if not api_key or not address:
        return None
    try:
        googlemaps = importlib.import_module('googlemaps')
        client = googlemaps.Client(key=api_key)
        result = client.geocode(address)
        if result and 'geometry' in result[0]:
            loc = result[0]['geometry']['location']
            return float(loc['lat']), float(loc['lng'])
    except Exception:
        return None
    return None


def get_nearest_shuttle_stop(lat: float, lon: float) -> Tuple[dict, float]:
    """Return nearest shuttle stop and distance (miles) for given coords."""
    nearest = min(
        SHUTTLE_STOPS,
        key=lambda s: haversine_miles(lat, lon, s['lat'], s['lon'])
    )
    dist = haversine_miles(lat, lon, nearest['lat'], nearest['lon'])
    return nearest, dist


def infer_shuttle_route_from_stops(origin_stop_name: str, dest_stop_name: str) -> str:
    """Infer best shuttle route label from stop names."""
    name = f"{origin_stop_name} -> {dest_stop_name}".lower()
    def has(s: str) -> bool:
        return s.lower() in name
    if has('bakery'):
        return 'Bakery Square'
    if has('ptc') or has('mill 19'):
        return 'PTC & Mill 19'
    if has('aiken') or has('shadyside'):
        return 'A/B/AB'
    if has('squirrel'):
        return 'C Route'
    return 'CMU Shuttle'


def display_header():
    st.markdown("""
<div style="
    background-color:#F5F6F9;
    padding:2rem;
    border-radius:12px;
    text-align:center;
    border:1px solid #ddd;
">
    <h1 style="color:#1B1B1B;">🚌 CMU Transportation Comparison Tool</h1>
    <p style="color:#333;">Find the fastest, cheapest, and most sustainable routes around Pittsburgh.</p>
</div>
""", unsafe_allow_html=True)



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
                    st.data_editor(schedules['A_B_AB_Routes_Weekday'], use_container_width=True)
                if 'A_B_AB_Routes_Weekend' in schedules:
                    st.write("**Saturday & Sunday:**")
                    st.data_editor(schedules['A_B_AB_Routes_Weekend'], use_container_width=True)
            
            with schedule_tabs[1]:
                st.markdown("### C Route (Squirrel Hill)")
                if 'C_Route_Weekday' in schedules:
                    st.write("**Monday - Friday:**")
                    st.data_editor(schedules['C_Route_Weekday'], use_container_width=True)
                else:
                    st.info("No weekend service for C Route")
            
            with schedule_tabs[2]:
                st.markdown("### PTC & Mill 19 Routes")
                if 'PTC_Mill19_Weekday' in schedules:
                    st.write("**Monday - Friday:**")
                    st.data_editor(schedules['PTC_Mill19_Weekday'], use_container_width=True)
                if 'PTC_Mill19_Weekend' in schedules:
                    st.write("**Saturday & Sunday:**")
                    st.data_editor(schedules['PTC_Mill19_Weekend'], use_container_width=True)
            
            with schedule_tabs[3]:
                st.markdown("### Bakery Square Routes")
                if 'Bakery_Square_Weekday' in schedules:
                    st.write("**Monday - Friday:**")
                    st.data_editor(schedules['Bakery_Square_Weekday'], use_container_width=True)
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
        use_custom_addresses = st.checkbox("Use exact addresses", value=False)
        if use_custom_addresses:
            origin_address = st.text_input(
                "📍 Origin address",
                placeholder="e.g., 5000 Forbes Ave, Pittsburgh, PA",
                key="origin_address_input"
            )
            # Live suggestions for origin address
            # Resolve a key for suggestions (UI overrides config/env)
            temp_google_key, _ = resolve_api_keys(st.session_state.get('google_api_key', ''), st.session_state.get('uber_token', '')) if 'google_api_key' in st.session_state else (None, None)
            # Fallback to config/env if UI field not tracked
            if not temp_google_key:
                temp_google_key, _ = resolve_api_keys('', '')
            suggestions = get_address_suggestions(origin_address, temp_google_key)
            if suggestions:
                selected = st.selectbox("Suggestions for origin", options=["(keep typed)"] + suggestions, index=0)
                if selected != "(keep typed)":
                    origin_address = selected
        else:
            origin = st.selectbox(
                "📍 Starting Location",
                options=list(CMU_LOCATIONS.keys()),
                index=0
            )
            st.caption(f"Address: {CMU_LOCATIONS[origin]['address']}")
    
    with col2:
        if use_custom_addresses:
            destination_address = st.text_input(
                "🎯 Destination address",
                placeholder="e.g., 6425 Penn Ave, Pittsburgh, PA",
                key="destination_address_input"
            )
            # Live suggestions for destination address
            temp_google_key, _ = resolve_api_keys(st.session_state.get('google_api_key', ''), st.session_state.get('uber_token', '')) if 'google_api_key' in st.session_state else (None, None)
            if not temp_google_key:
                temp_google_key, _ = resolve_api_keys('', '')
            suggestions = get_address_suggestions(destination_address, temp_google_key)
            if suggestions:
                selected = st.selectbox("Suggestions for destination", options=["(keep typed)"] + suggestions, index=0)
                if selected != "(keep typed)":
                    destination_address = selected
        else:
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
        
        # Show where keys will be resolved from (informational hint only)
        resolved_google_key, resolved_uber_token = resolve_api_keys(google_api_key, uber_token)
        if not resolved_google_key:
            st.caption("Using mock Public Transit data (no Google Maps API key provided)")
        if not resolved_uber_token:
            st.caption("Using mock Uber data (no Uber API token provided)")
    
    if st.button("🔎 Compare Options", type="primary", use_container_width=True):
        # Resolve keys again at click time to ensure latest values
        resolved_google_key, resolved_uber_token = resolve_api_keys(google_api_key, uber_token)
        if 'use_custom_addresses' in locals() and use_custom_addresses:
            compare_transportation_options(
                origin_address.strip(), destination_address.strip(), travel_date, travel_time,
                resolved_google_key, resolved_uber_token
            )
        else:
            compare_transportation_options(
                origin, destination, travel_date, travel_time,
                resolved_google_key, resolved_uber_token
            )


def compare_transportation_options(
    origin,
    destination,
    travel_date,
    travel_time,
    google_api_key: Optional[str],
    uber_access_token: Optional[str]
):
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
        st.success("✅ Available")
        st.markdown("**Benefits:**")
        st.markdown("- Free with CMU ID\n- Direct campus routes\n- Frequent service")
        

                # --- Map preview for shuttle route ---
        if origin in CMU_LOCATIONS and destination in CMU_LOCATIONS:
            o_coords = (CMU_LOCATIONS[origin]['lat'], CMU_LOCATIONS[origin]['lon'])
            d_coords = (CMU_LOCATIONS[destination]['lat'], CMU_LOCATIONS[destination]['lon'])

            st.markdown("**🗺️ Route Preview:**")
            map_data = pd.DataFrame([
                {'lat': o_coords[0], 'lon': o_coords[1]},
                {'lat': d_coords[0], 'lon': d_coords[1]}
            ])
            st.map(map_data, use_container_width=True)
        else:
            st.info("Map preview available only for preset CMU locations.")
            # Ensure shuttle routes are available and displayed
        if st.session_state.get('shuttle_data') is None:
            fetch_shuttle_data()
        shuttle_data = st.session_state.get('shuttle_data')
        if shuttle_data and shuttle_data.get('success') and shuttle_data.get('routes'):
            with st.expander("View CMU shuttle routes"):
                for route_name, route_info in shuttle_data['routes'].items():
                    st.write(f"**{route_name}**")
                    if 'description' in route_info:
                        st.caption(route_info['description'])
        else:
            st.caption("Shuttle routes will appear once schedules are fetched.")
        
        # Nearest stops and estimated shuttle leg time
        o_coords = None
        d_coords = None
        # origin/destination may be labels or free-form text
        if origin in CMU_LOCATIONS and destination in CMU_LOCATIONS:
            o_coords = (CMU_LOCATIONS[origin]['lat'], CMU_LOCATIONS[origin]['lon'])
            d_coords = (CMU_LOCATIONS[destination]['lat'], CMU_LOCATIONS[destination]['lon'])
        else:
            o_coords = geocode_address(origin if isinstance(origin, str) else str(origin), google_api_key)
            d_coords = geocode_address(destination if isinstance(destination, str) else str(destination), google_api_key)

        shuttle_total_minutes = None
        if o_coords and d_coords:
            # Build a schedule-aware plan with walking and wait time
            try:
                departure_dt = datetime.combine(travel_date, travel_time)
            except Exception:
                departure_dt = datetime.now()
            plan = plan_shuttle_trip(
                origin_coords=(o_coords[0], o_coords[1]),
                dest_coords=(d_coords[0], d_coords[1]),
                when=departure_dt,
                google_api_key=google_api_key,
            )
            if plan.get('success'):
                totals = plan['totals']
                shuttle_total_minutes = totals.get('minutes')
                st.metric("Estimated Total Time", f"{shuttle_total_minutes} mins")
                with st.expander(f"Shuttle plan: {plan['route_name']}"):
                    st.write(f"Origin stop: {plan['origin_stop']}")
                    st.write(f"Destination stop: {plan['dest_stop']}")
                    if 'times' in plan:
                        st.write(f"Boarding time: {plan['times'].get('board_time')}")
                        st.write(f"Arrival time: {plan['times'].get('arrival_time')}")
                    st.markdown("**Steps:**")
                    for step in plan['steps']:
                        if step['type'] == 'WALK':
                            st.write(f"Walk {step['minutes']} mins: {step['from']} → {step['to']}")
                        elif step['type'] == 'WAIT':
                            st.write(f"Wait {step['minutes']} mins at {step['at']} for {step['route']}")
                        elif step['type'] == 'SHUTTLE':
                            miles_txt = f" ({step['miles']} mi)" if 'miles' in step else ""
                            st.write(f"Ride {step['minutes']} mins on {step['route']}: {step['from']} → {step['to']}{miles_txt}")
                    st.markdown("**Breakdown:**")
                    st.write(f"Walking: {totals.get('walk_minutes')} mins")
                    st.write(f"Waiting: {totals.get('wait_minutes')} mins")
                    st.write(f"In-vehicle: {totals.get('in_vehicle_minutes')} mins")
            else:
                st.caption("No direct shuttle route found or not operating at the selected time.")

        st.markdown('</div>', unsafe_allow_html=True)
    


        # Public Transit
    with col2:
        st.markdown("### 🚍 Public Transit")
        st.markdown('<div class="route-card">', unsafe_allow_html=True)
        st.markdown("**Benefits:** Extensive network, frequent service")

        transit_data = None
        used_transit_mock = False
        used_transit_live = False
        transit_error_message = None

        # --- Fetch transit data (real or mock) ---
        if google_api_key:
            google_api = GoogleTransitAPI(api_key=google_api_key)
            try:
                departure_dt = datetime.combine(travel_date, travel_time)
            except Exception:
                departure_dt = datetime.now()
            
            if origin in CMU_LOCATIONS and destination in CMU_LOCATIONS:
                origin_str = CMU_LOCATIONS[origin]['address']
                dest_str = CMU_LOCATIONS[destination]['address']
            else:
                origin_str = origin
                dest_str = destination

            transit_data = google_api.get_transit_directions(
                origin_str,
                dest_str,
                departure_time=departure_dt
            )

            if transit_data.get('success'):
                used_transit_live = True
            else:
                transit_error_message = (
                    transit_data.get('error') 
                    or 'Unknown error from Google Maps Directions API'
                )
        else:
            transit_data = get_mock_transit_data(origin, destination)
            used_transit_mock = True

        # --- Display results ---
        if transit_data and transit_data.get('success') and transit_data.get('routes'):
            route = transit_data['routes'][0]
            st.metric("Cost", "$2.75", "Standard fare")
            st.metric("Travel Time", route['duration'])
            st.metric("Distance", route['distance'])

            if 'departure_time' in route and 'arrival_time' in route:
                st.caption(
                    f"Departs at {route['departure_time']} • Arrives by {route['arrival_time']}"
                )

            with st.expander("View Route Details"):
                for step in route['steps']:
                    st.write(f"**{step['travel_mode']}** - {step['duration']}")
                    if 'transit' in step:
                        st.write(f"  Line: {step['transit']['line']}")
                        st.write(f"  From: {step['transit']['departure_stop']}")
                        st.write(f"  To: {step['transit']['arrival_stop']}")

            # --- Show nearest shuttle stops for reference ---
            origin_coords = None
            dest_coords = None
            if origin in CMU_LOCATIONS and destination in CMU_LOCATIONS:
                origin_coords = (
                    CMU_LOCATIONS[origin]['lat'],
                    CMU_LOCATIONS[origin]['lon']
                )
                dest_coords = (
                    CMU_LOCATIONS[destination]['lat'],
                    CMU_LOCATIONS[destination]['lon']
                )
            else:
                origin_coords = geocode_address(origin, google_api_key)
                dest_coords = geocode_address(destination, google_api_key)

            if origin_coords:
                nearest_origin = min(
                    SHUTTLE_STOPS,
                    key=lambda s: haversine_miles(
                        origin_coords[0], origin_coords[1], s['lat'], s['lon']
                    ),
                )
                st.caption(f"Nearest shuttle stop from origin: {nearest_origin['name']}")

            if dest_coords:
                nearest_dest = min(
                    SHUTTLE_STOPS,
                    key=lambda s: haversine_miles(
                        dest_coords[0], dest_coords[1], s['lat'], s['lon']
                    ),
                )
                st.caption(f"Nearest shuttle stop to destination: {nearest_dest['name']}")

        elif transit_error_message:
            st.error("Transit data error: " + transit_error_message)
            with st.expander("Troubleshoot Google Maps API"):
                st.markdown("- Ensure Directions API is enabled for your project")
                st.markdown("- Verify billing is active on the project")
                st.markdown("- Temporarily set key restrictions to None while testing")
                st.markdown("- Confirm the key in config.py or UI matches your Google Console key")

        else:
            st.warning("Transit data unavailable")

        if used_transit_live:
            st.caption("Live Google Maps transit data")
        elif used_transit_mock:
            st.info("Using mock Public Transit data (no Google Maps API key provided)")

        st.markdown('</div>', unsafe_allow_html=True)

    
    # Uber
    with col3:
        st.markdown("### 🚗 Uber")
        st.markdown('<div class="route-card">', unsafe_allow_html=True)
        
        uber_data = None
        used_uber_mock = False
        # Only attempt real Uber estimates for preset CMU locations
        if uber_access_token and (origin in CMU_LOCATIONS and destination in CMU_LOCATIONS):
            uber_api = UberAPI(access_token=uber_access_token)
            origin_coords = CMU_LOCATIONS[origin]
            dest_coords = CMU_LOCATIONS[destination]
            uber_data = uber_api.get_price_estimates(
                origin_coords['lat'], origin_coords['lon'],
                dest_coords['lat'], dest_coords['lon']
            )
            if not uber_data.get('success'):
                uber_data = get_mock_uber_estimates(origin, destination)
                used_uber_mock = True
        else:
            # For custom addresses, show mock Uber estimates
            uber_data = get_mock_uber_estimates(
                origin if isinstance(origin, str) else str(origin),
                destination if isinstance(destination, str) else str(destination)
            )
            used_uber_mock = True
        
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
        
        if used_uber_mock:
            st.info("Using mock Uber data (no valid Uber API token)")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Summary comparison
    st.markdown("---")
    st.subheader("💡 Summary & Recommendations")
    
    # Compute fastest option dynamically from available data
    fastest_label = None
    fastest_time = None
    details = []

    # Transit time
    transit_time_seconds = None
    if transit_data and transit_data.get('success') and transit_data.get('routes'):
        transit_time_seconds = transit_data['routes'][0].get('duration_seconds')
        if isinstance(transit_time_seconds, int):
            fastest_label = 'Public Transit'
            fastest_time = transit_time_seconds
            details.append(("Public Transit", transit_time_seconds))

    # Uber time (best among estimates)
    uber_best_seconds = None
    # Shuttle time from plan
    if 'shuttle_total_minutes' in locals() and isinstance(shuttle_total_minutes, int):
        s_secs = shuttle_total_minutes * 60
        details.append(("Shuttle", s_secs))
        if fastest_time is None or s_secs < fastest_time:
            fastest_label = 'Shuttle'
            fastest_time = s_secs
    if uber_data and uber_data.get('success') and uber_data.get('estimates'):
        try:
            uber_best_seconds = min(e.get('duration') for e in uber_data['estimates'] if isinstance(e.get('duration'), int))
        except ValueError:
            uber_best_seconds = None
        if isinstance(uber_best_seconds, int):
            details.append(("Uber", uber_best_seconds))
            if fastest_time is None or uber_best_seconds < fastest_time:
                fastest_label = 'Uber'
                fastest_time = uber_best_seconds

    # Build summary UI
    col1, col2 = st.columns(2)
    with col1:
        fastest_text = f"{fastest_label} ({format_duration(fastest_time)})" if fastest_label and isinstance(fastest_time, int) else "Depends on time"
        st.markdown(f"""
        <div class=\"success-box\"> 
        <strong>💰 Best Value:</strong> CMU Shuttle (Free!)<br>
        <strong>⚡ Fastest:</strong> {fastest_text}<br>
        <strong>🌱 Most Sustainable:</strong> Public Transit / Shuttle
        </div>
        """, unsafe_allow_html=True)

    with col2:
        # Shuttle recommendation based on origin/destination labels
        if origin in CMU_LOCATIONS and destination in CMU_LOCATIONS:
            origin_label = CMU_LOCATIONS[origin]['address']
            destination_label = CMU_LOCATIONS[destination]['address']
        else:
            origin_label = origin if isinstance(origin, str) else str(origin)
            destination_label = destination if isinstance(destination, str) else str(destination)
        shuttle_rec, shuttle_note = recommend_shuttle_route(origin_label, destination_label)

        if details:
            st.markdown("**Observed travel times:**")
            for name, secs in details:
                st.markdown(f"- {name}: {format_duration(secs)}")
        st.markdown("**Recommendation:**")
        if shuttle_rec:
            st.markdown(f"- Best CMU Shuttle: **{shuttle_rec}** — {shuttle_note}")
        else:
            st.markdown(f"- {shuttle_note}")
        st.markdown("- Public Transit for cost-effective trips")
        st.markdown("- Uber for urgency or off-peak hours")


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
    
    import base64

    # --- Load and encode your local logo file ---
    with open("cmu_logo.png", "rb") as image_file:
        encoded_logo = base64.b64encode(image_file.read()).decode()
    # Sidebar
    with st.sidebar:
        with st.sidebar:
    # Logo at the top
            st.markdown(
    f"""
    <div style="
        background-color: #2E2E2E;
        padding: 0;
        margin: 0;
        text-align: center;
    ">
        <img src="data:image/png;base64,{encoded_logo}"
             style="width:100%; height:auto; display:block; border:none; border-radius:0;">
    </div>
    """,
    unsafe_allow_html=True
)

    
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
    st.markdown("""
        <hr style="margin-top:2rem;">
        <div style='text-align:center;color:#666;padding:1rem 0;'>
            <small>
                © 2025 CMU Transportation Comparison Tool — Made with ❤️ by CMU Students<br>
                Not officially affiliated with CMU Transportation Services
            </small>
        </div>
        """, unsafe_allow_html=True)



if __name__ == "__main__":
    main()
