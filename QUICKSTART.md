# 🚀 Quick Start Guide

Get the CMU Transportation Comparison Tool up and running in 3 simple steps!

## Step 1: Install Dependencies

```bash
pip3 install -r requirements.txt
```

Or if you prefer using a virtual environment (recommended):

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate     # On Windows

# Install dependencies
pip install -r requirements.txt
```

## Step 2: Run the Application

### Option A: Using Streamlit directly
```bash
streamlit run app.py
```

### Option B: Using the launch script (macOS/Linux)
```bash
./run.sh
```

### Option C: Using Python
```bash
python3 -m streamlit run app.py
```

## Step 3: Open Your Browser

The app will automatically open at: **http://localhost:8501**

If it doesn't open automatically, just copy and paste that URL into your browser.

---

## 🎉 That's It!

You should now see the CMU Transportation Comparison Tool running with three main tabs:

1. **📅 Shuttle Schedules** - View all CMU shuttle routes and timings
2. **🔍 Compare Options** - Compare shuttle, transit, and Uber options
3. **ℹ️ About** - Learn more about the tool

---

## 🔑 Optional: Add API Keys for Real-Time Data

The app works with mock data by default, but you can enable real-time data:

1. Copy `config.example.py` to `config.py`
2. Add your API keys:
   - Google Maps API key
   - Uber API token
3. In the app, expand "⚙️ API Configuration" and enter your keys

---

## 🐛 Troubleshooting

**Problem: Module not found errors**
```bash
pip3 install -r requirements.txt
```

**Problem: Port 8501 already in use**
```bash
streamlit run app.py --server.port 8502
```

**Problem: Permission denied on run.sh**
```bash
chmod +x run.sh
./run.sh
```

---

## 📚 Next Steps

- Check out the full [README.md](README.md) for more details
- Test the web scraper: `python3 src/scraper.py`
- Explore the source code in the `src/` directory

**Happy commuting! 🚌🚍🚗**
