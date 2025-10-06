"""
Test script to verify all components of the CMU Transportation Comparison Tool.
Run this to ensure everything is set up correctly.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_imports():
    """Test that all required modules can be imported."""
    print("Testing imports...")
    try:
        import streamlit
        import requests
        import pandas
        from bs4 import BeautifulSoup
        import lxml
        import googlemaps
        print("✓ All required packages are installed")
        return True
    except ImportError as e:
        print(f"✗ Import error: {e}")
        print("Run: pip install -r requirements.txt")
        return False

def test_scraper():
    """Test the shuttle scraper."""
    print("\nTesting shuttle scraper...")
    try:
        from scraper import CMUShuttleScraper
        
        scraper = CMUShuttleScraper()
        data = scraper.get_all_shuttle_data()
        
        if data['success']:
            print(f"✓ Scraper working! Found {len(data['routes'])} routes and {len(data['schedules'])} schedules")
            return True
        else:
            print(f"✗ Scraper failed: {data.get('error')}")
            return False
    except Exception as e:
        print(f"✗ Scraper error: {e}")
        return False

def test_modules():
    """Test that all custom modules load correctly."""
    print("\nTesting custom modules...")
    try:
        from scraper import CMUShuttleScraper
        from google_transit import GoogleTransitAPI, get_mock_transit_data
        from uber_api import UberAPI, get_mock_uber_estimates
        from utils import (
            get_day_of_week, 
            format_duration, 
            CMU_LOCATIONS
        )
        
        print("✓ All modules imported successfully")
        print(f"  - Found {len(CMU_LOCATIONS)} CMU locations")
        print(f"  - Current day: {get_day_of_week()}")
        print(f"  - Duration format test: {format_duration(1500)}")
        
        # Test mock data
        transit = get_mock_transit_data("Main Campus", "Shadyside")
        uber = get_mock_uber_estimates("Main Campus", "Shadyside")
        
        if transit['success'] and uber['success']:
            print("✓ Mock data functions working")
        
        return True
    except Exception as e:
        print(f"✗ Module error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_streamlit_app():
    """Check if the Streamlit app file exists and is readable."""
    print("\nTesting Streamlit app...")
    try:
        if os.path.exists('app.py'):
            with open('app.py', 'r') as f:
                content = f.read()
                if 'def main():' in content:
                    print("✓ Streamlit app file is valid")
                    return True
                else:
                    print("✗ app.py missing main() function")
                    return False
        else:
            print("✗ app.py not found")
            return False
    except Exception as e:
        print(f"✗ Error reading app.py: {e}")
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("CMU Transportation Comparison Tool - Setup Test")
    print("=" * 60)
    
    results = []
    
    results.append(("Imports", test_imports()))
    results.append(("Modules", test_modules()))
    results.append(("Scraper", test_scraper()))
    results.append(("Streamlit App", test_streamlit_app()))
    
    print("\n" + "=" * 60)
    print("TEST RESULTS")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{test_name:.<30} {status}")
    
    all_passed = all(result[1] for result in results)
    
    print("=" * 60)
    if all_passed:
        print("🎉 All tests passed! You're ready to run the app.")
        print("\nTo start the app, run:")
        print("  streamlit run app.py")
        print("\nOr use the launch script:")
        print("  ./run.sh")
    else:
        print("⚠️  Some tests failed. Please fix the issues above.")
    print("=" * 60)
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

