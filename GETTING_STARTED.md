# 🎉 Getting Started with CMU Transportation Comparison Tool

## ✅ Setup Complete!

Your project is fully set up and ready to run. All tests have passed! 🚀

---

## 🏃 Run the Application

### Option 1: Simple Command (Recommended)
```bash
streamlit run app.py
```

### Option 2: Using the Launch Script
```bash
./run.sh
```

### Option 3: Full Python Command
```bash
python3 -m streamlit run app.py
```

The app will open automatically in your browser at: **http://localhost:8501**

---

## 🎯 What You Can Do Now

### 1. View Live Shuttle Schedules
- Click the **"Shuttle Schedules"** tab
- See all CMU routes (A, B, AB, C, PTC, Mill 19, Bakery Square)
- View weekday and weekend schedules
- Refresh data in real-time

### 2. Compare Transportation Options
- Click the **"Compare Options"** tab
- Select your origin and destination
- Choose date and time
- See side-by-side comparison of:
  - 🚌 CMU Shuttle (FREE!)
  - 🚍 Public Transit
  - 🚗 Uber

### 3. Test the Scraper
```bash
python3 src/scraper.py
```

### 4. Run System Tests
```bash
python3 test_setup.py
```

---

## 🔑 Optional: Add API Keys

The app works with **mock data** by default, but you can enable **real-time data**:

1. **Copy the config template:**
   ```bash
   cp config.example.py config.py
   ```

2. **Add your API keys to `config.py`:**
   - Google Maps API key → [Get it here](https://console.cloud.google.com/)
   - Uber API token → [Get it here](https://developer.uber.com/)

3. **Or enter them directly in the app:**
   - Go to "Compare Options" tab
   - Expand "⚙️ API Configuration"
   - Enter your keys

---

## 📚 Documentation

- **README.md** - Full project documentation
- **QUICKSTART.md** - Quick setup guide
- **PROJECT_OVERVIEW.md** - Technical details and architecture
- **GETTING_STARTED.md** - This file

---

## 🎨 What's Built

### ✅ Complete Features

1. **Web Scraping Module**
   - Live scraping from CMU website
   - All routes and schedules parsed
   - 6 routes, multiple schedules

2. **Streamlit Frontend**
   - Beautiful, modern UI
   - Responsive design
   - 3 main tabs with rich content
   - Custom CSS styling

3. **API Integration Modules**
   - Google Transit API (ready)
   - Uber API (ready)
   - Mock data for testing

4. **Utility Functions**
   - Time/date handling
   - Cost calculations
   - Location presets
   - Duration formatting

---

## 🛠️ File Structure

```
DFP-TeamBrown/
├── app.py                    # Main Streamlit app
├── requirements.txt          # Dependencies
├── run.sh                    # Launch script
├── test_setup.py            # Verification tests
│
├── src/                      # Source modules
│   ├── scraper.py           # Shuttle scraper
│   ├── google_transit.py    # Google API
│   ├── uber_api.py          # Uber API
│   └── utils.py             # Utilities
│
├── data/                     # Data storage
│
└── docs/                     # Documentation
    ├── README.md
    ├── QUICKSTART.md
    └── PROJECT_OVERVIEW.md
```

---

## 🧪 Verify Everything Works

```bash
# 1. Test all components
python3 test_setup.py

# 2. Test the scraper
python3 src/scraper.py

# 3. Run the app
streamlit run app.py
```

---

## 🎓 Example Usage Flow

1. **Start the app:** `streamlit run app.py`
2. **Browser opens automatically** at localhost:8501
3. **View shuttles:** Check "Shuttle Schedules" tab
4. **Compare options:**
   - Go to "Compare Options"
   - Select "Main Campus" → "Shadyside"
   - See all options compared
5. **Read about it:** Check "About" tab

---

## 💡 Tips

- **Refresh shuttle data:** Click the refresh button in the Shuttle Schedules tab
- **Mock vs Real data:** Toggle by adding/removing API keys
- **Multiple locations:** 6 CMU locations pre-configured
- **Responsive design:** Works on desktop, tablet, and mobile

---

## 🐛 Troubleshooting

**App won't start?**
```bash
pip3 install -r requirements.txt
```

**Port already in use?**
```bash
streamlit run app.py --server.port 8502
```

**Import errors?**
```bash
python3 test_setup.py
```

---

## 📈 Next Steps (Future)

Phase 2 & 3 (when you're ready):
- [ ] Real-time bus tracking
- [ ] User accounts & saved routes
- [ ] Lyft integration
- [ ] Weather-based suggestions
- [ ] Mobile app version

---

## 🎉 You're All Set!

The CMU Transportation Comparison Tool is ready to use. Enjoy comparing your transportation options! 🚌🚍🚗

**Questions?** Check the README.md or PROJECT_OVERVIEW.md

---

**Happy Commuting! 🎓**

