#!/bin/bash

# CMU Transportation Comparison Tool Launch Script

echo "🚌 Starting CMU Transportation Comparison Tool..."
echo ""

# Uncomment below lines if virtual environment needs to be created
# # Check if virtual environment exists
# if [ ! -d "venv" ]; then
#     echo "⚠️  Virtual environment not found. Creating one..."
#     python3 -m venv venv
#     echo "✓ Virtual environment created"
# fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Uncomment below lines if dependencies need to be installed
# # Check if dependencies are installed
# if ! python -c "import streamlit" 2>/dev/null; then
#     echo "📦 Installing dependencies..."
#     pip install -r requirements.txt
#     echo "✓ Dependencies installed"
# fi

# Run the application
echo "🚀 Launching Streamlit app..."
echo ""
streamlit run app.py
