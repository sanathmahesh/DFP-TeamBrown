# 📋 Project Overview

## CMU Transportation Comparison Tool

A comprehensive Python-based web application for comparing transportation options at Carnegie Mellon University.

---

## 📂 Project Structure

```
DFP-TeamBrown/
│
├── 📱 Frontend & Main App
│   └── app.py                    # Main Streamlit application (600+ lines)
│
├── 🔧 Core Modules (src/)
│   ├── scraper.py               # CMU shuttle schedule web scraper
│   ├── google_transit.py        # Google Maps Transit API integration
│   ├── uber_api.py              # Uber API integration
│   └── utils.py                 # Utility functions & helpers
│
├── 📚 Documentation
│   ├── README.md                # Comprehensive project documentation
│   ├── QUICKSTART.md            # Quick start guide for users
│   └── PROJECT_OVERVIEW.md      # This file
│
├── ⚙️ Configuration
│   ├── requirements.txt         # Python dependencies
│   ├── config.example.py        # API keys configuration template
│   └── .gitignore              # Git ignore rules
│
├── 🧪 Testing & Scripts
│   ├── test_setup.py            # Setup verification script
│   └── run.sh                   # Launch script (macOS/Linux)
│
└── 💾 Data Storage
    └── data/                    # Directory for cached data
```

---

## 🎯 Features Implemented

### ✅ Phase 1: Complete (Current)

#### 1. Web Scraping
- ✅ Real-time scraping of CMU shuttle schedules
- ✅ Parses all route types (A, B, AB, C, PTC, Mill 19, Bakery Square)
- ✅ Extracts weekday and weekend schedules
- ✅ Route descriptions and paths
- ✅ Handles schedule tables with pandas DataFrames

#### 2. Frontend (Streamlit)
- ✅ Beautiful, modern UI with custom CSS
- ✅ Three main tabs:
  - 📅 Shuttle Schedules
  - 🔍 Compare Options
  - ℹ️ About
- ✅ Responsive design
- ✅ Interactive data tables
- ✅ Real-time data refresh
- ✅ Location presets for CMU
- ✅ Mock data mode (works without API keys)

#### 3. API Integration Modules
- ✅ Google Transit API module (ready for API key)
- ✅ Uber API module (ready for API key)
- ✅ Mock data functions for testing
- ✅ Comparison algorithms

#### 4. Utilities
- ✅ Time parsing and formatting
- ✅ Duration calculations
- ✅ Cost comparison functions
- ✅ CMU location presets with coordinates
- ✅ Day/time utilities

---

## 🚀 How It Works

### 1. Shuttle Schedule Scraping

```python
from scraper import CMUShuttleScraper

scraper = CMUShuttleScraper()
data = scraper.get_all_shuttle_data()

# Returns:
# - routes: Dict of route information
# - schedules: Dict of pandas DataFrames
# - success: Boolean status
```

**Data Flow:**
1. Fetches HTML from CMU Transportation website
2. Parses with BeautifulSoup
3. Extracts route information
4. Converts schedule tables to DataFrames
5. Identifies route types automatically

### 2. Transportation Comparison

```python
# User selects origin & destination
# App compares:
#   - CMU Shuttle (free, parsed schedule)
#   - Public Transit (Google Maps API)
#   - Uber (Uber API)

# Displays:
#   - Cost comparison
#   - Time comparison
#   - Route details
#   - Recommendations
```

### 3. Streamlit Frontend

```python
# Main tabs
tab1: Shuttle Schedules
  - Live data from scraper
  - Filterable by day/route
  - Refresh button

tab2: Compare Options
  - Location selectors
  - Time/date pickers
  - Side-by-side comparison
  - Cost/time analysis

tab3: About
  - Project information
  - Usage instructions
  - Technology stack
```

---

## 🔌 API Integration

### Google Maps Transit API
**Status:** Module ready, requires API key

**Capabilities:**
- Get transit directions
- Calculate travel time
- Show route steps
- Compare with shuttle timings

**Setup:**
1. Get API key from Google Cloud Console
2. Add to `config.py` or app interface
3. Enable Directions API

### Uber API
**Status:** Module ready, requires API token

**Capabilities:**
- Price estimates
- Time estimates
- Different ride types (UberX, Comfort, XL)
- Surge pricing detection

**Setup:**
1. Register at Uber Developer Portal
2. Get Server Token
3. Add to `config.py` or app interface

---

## 📊 Data Models

### Shuttle Data Structure
```python
{
    'success': True,
    'routes': {
        'A Route': {
            'description': 'North Oakland / West Shadyside',
            'path': 'Morewood > Forbes > S Dithridge > ...'
        },
        # ... more routes
    },
    'schedules': {
        'A_B_AB_Routes_Weekday': DataFrame,
        'A_B_AB_Routes_Weekend': DataFrame,
        'C_Route_Weekday': DataFrame,
        # ... more schedules
    },
    'url': 'https://www.cmu.edu/...'
}
```

### Location Data
```python
CMU_LOCATIONS = {
    'Main Campus': {
        'address': '5000 Forbes Avenue, Pittsburgh, PA 15213',
        'lat': 40.4433,
        'lon': -79.9436
    },
    # ... 5 more locations
}
```

---

## 🛠️ Technologies Used

| Category | Technology | Purpose |
|----------|-----------|---------|
| **Frontend** | Streamlit 1.31.0 | Web interface |
| **Web Scraping** | BeautifulSoup4 4.12.3 | HTML parsing |
| **HTTP** | Requests 2.31.0 | Web requests |
| **Data Processing** | Pandas 2.2.0 | Table handling |
| **APIs** | googlemaps 4.10.0 | Transit data |
| **APIs** | uber-rides 0.3.0 | Ride estimates |
| **Config** | python-dotenv 1.0.1 | Environment vars |

---

## 📈 Future Enhancements (Phase 2 & 3)

### Phase 2: Enhanced Features
- [ ] Real-time shuttle tracking via TripShot API
- [ ] User authentication & saved preferences
- [ ] Lyft API integration
- [ ] Weather-based recommendations
- [ ] Historical data analysis

### Phase 3: Advanced Features
- [ ] Machine learning for wait time predictions
- [ ] Push notifications
- [ ] Mobile app (React Native + Python backend)
- [ ] Carbon footprint calculator
- [ ] Route optimization algorithms

---

## 🧪 Testing

### Current Tests
- ✅ Import verification
- ✅ Module loading
- ✅ Web scraper functionality
- ✅ Mock data generation
- ✅ App file validation

### Run Tests
```bash
python3 test_setup.py
```

### Test Individual Modules
```bash
# Test scraper
python3 src/scraper.py

# Test utilities
python3 src/utils.py

# Test Google Transit (mock)
python3 src/google_transit.py

# Test Uber API (mock)
python3 src/uber_api.py
```

---

## 🎨 UI/UX Design

### Color Scheme
- **Primary:** CMU Red (#c41230)
- **Secondary:** CMU Gray (#666666)
- **Success:** Green (#d4edda)
- **Info:** Blue (#d1ecf1)
- **Background:** Light Gray (#f0f2f6)

### Key UI Elements
1. **Header**: Logo + Title
2. **Sidebar**: Quick links + Current time
3. **Tabs**: Main navigation
4. **Cards**: Information containers
5. **Metrics**: Large numbers with context
6. **Expandable sections**: Details on demand

---

## 📦 Dependencies

### Core Dependencies
```
streamlit==1.31.0
beautifulsoup4==4.12.3
requests==2.31.0
lxml==5.1.0
pandas==2.2.0
```

### API Dependencies
```
googlemaps==4.10.0
uber-rides==0.3.0
```

### Utilities
```
python-dotenv==1.0.1
```

---

## 🔒 Security Considerations

1. **API Keys**: Never commit to version control
2. **User Data**: No sensitive data stored
3. **Web Scraping**: Respectful rate limiting
4. **Input Validation**: Sanitized user inputs

---

## 📞 Support & Contact

- **CMU Transportation**: transportation@andrew.cmu.edu
- **Project Issues**: GitHub Issues
- **Documentation**: See README.md

---

## 📝 License

MIT License - Open source and free to use

---

## 🙏 Acknowledgments

- CMU Transportation Services for public data
- Streamlit team for the amazing framework
- CMU community for inspiration

---

**Version:** 0.1.0  
**Last Updated:** October 6, 2025  
**Status:** ✅ Fully Functional - Phase 1 Complete
