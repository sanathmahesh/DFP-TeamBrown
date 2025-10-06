"""
Web scraper for CMU shuttle schedule information.
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
from typing import Dict, List, Optional
import re
from io import StringIO


class CMUShuttleScraper:
    """Scraper for CMU Transportation shuttle schedules."""
    
    def __init__(self):
        self.url = "https://www.cmu.edu/transportation/transport/shuttle.html"
        self.soup = None
        
    def fetch_page(self) -> bool:
        """
        Fetch the shuttle schedule page.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            response = requests.get(self.url, timeout=10)
            response.raise_for_status()
            self.soup = BeautifulSoup(response.content, 'html.parser')
            return True
        except requests.RequestException as e:
            print(f"Error fetching page: {e}")
            return False
    
    def extract_route_info(self) -> Dict[str, Dict[str, str]]:
        """
        Extract route information including descriptions and paths.
        
        Returns:
            Dict containing route names and their descriptions
        """
        if not self.soup:
            return {}
        
        routes = {}
        
        # Route patterns to look for
        route_sections = {
            'A Route': 'A Route - North Oakland / West Shadyside',
            'B Route': 'B Route - East Shadyside',
            'AB Route': 'AB Route - North Oakland & Shadyside Combined',
            'C Route': 'C Route - Squirrel Hill',
            'PTC Route': 'PTC Route',
            'PTC & Mill 19 Route': 'PTC & Mill 19 Route',
            'Bakery Square Long Route': 'Bakery Square Long Route',
            'Bakery Square Short Route': 'Bakery Square Short Route'
        }
        
        # Find all strong/bold tags that might contain route info
        for route_name, route_desc in route_sections.items():
            route_info = {}
            
            # Try to find the route description in the page
            for elem in self.soup.find_all(['strong', 'b', 'p']):
                text = elem.get_text(strip=True)
                if route_desc in text or route_name in text:
                    # Get the next paragraph or text that might contain the path
                    next_elem = elem.find_next(['p', 'div'])
                    if next_elem:
                        path_text = next_elem.get_text(strip=True)
                        if '>' in path_text:  # Route paths contain '>' separators
                            route_info['path'] = path_text
                            route_info['description'] = route_desc
                            routes[route_name] = route_info
                            break
        
        return routes
    
    def extract_schedule_tables(self) -> Dict[str, pd.DataFrame]:
        """
        Extract all schedule tables from the page.
        
        Returns:
            Dict of DataFrames containing schedule information for different routes
        """
        if not self.soup:
            return {}
        
        schedules = {}
        
        # Find all tables in the page
        tables = self.soup.find_all('table')
        
        for idx, table in enumerate(tables):
            try:
                # Parse table into DataFrame
                df = pd.read_html(StringIO(str(table)))[0]
                
                # Try to identify which route this table belongs to
                # Look at the preceding headings
                prev_heading = table.find_previous(['h1', 'h2', 'h3', 'h4', 'strong', 'p'])
                route_name = f"Table_{idx}"
                
                if prev_heading:
                    heading_text = prev_heading.get_text(strip=True)
                    
                    # Identify the route type based on heading
                    if 'A, B and AB Routes' in heading_text:
                        if 'Monday - Friday' in heading_text or 'Monday-Friday' in heading_text:
                            route_name = 'A_B_AB_Routes_Weekday'
                        elif 'Saturday & Sunday' in heading_text:
                            route_name = 'A_B_AB_Routes_Weekend'
                    elif 'C Route' in heading_text:
                        route_name = 'C_Route_Weekday'
                    elif 'PTC / Mill 19' in heading_text or 'PTC/Mill 19' in heading_text:
                        if 'Saturday & Sunday' in heading_text:
                            route_name = 'PTC_Mill19_Weekend'
                        else:
                            route_name = 'PTC_Mill19_Weekday'
                    elif 'Bakery Square' in heading_text:
                        route_name = 'Bakery_Square_Weekday'
                
                schedules[route_name] = df
                
            except Exception as e:
                print(f"Error parsing table {idx}: {e}")
                continue
        
        return schedules
    
    def get_all_shuttle_data(self) -> Dict:
        """
        Get all shuttle data including routes and schedules.
        
        Returns:
            Dict containing all shuttle information
        """
        if not self.fetch_page():
            return {
                'success': False,
                'error': 'Failed to fetch shuttle schedule page'
            }
        
        return {
            'success': True,
            'routes': self.extract_route_info(),
            'schedules': self.extract_schedule_tables(),
            'url': self.url
        }
    
    def get_active_shuttles(self, current_time: str, day_of_week: str) -> List[Dict]:
        """
        Get shuttles that are active at a given time.
        
        Args:
            current_time: Time in format "HH:MM AM/PM"
            day_of_week: Day of week (Monday-Sunday)
            
        Returns:
            List of active shuttle routes
        """
        data = self.get_all_shuttle_data()
        if not data['success']:
            return []
        
        active_shuttles = []
        is_weekend = day_of_week in ['Saturday', 'Sunday']
        
        schedules = data['schedules']
        
        # Determine which schedule to check based on day
        if is_weekend:
            relevant_schedules = [
                ('A/B/AB Routes', 'A_B_AB_Routes_Weekend'),
                ('C Route', 'C_Route_Weekday'),  # C route doesn't have weekend service
                ('PTC & Mill 19', 'PTC_Mill19_Weekend'),
            ]
        else:
            relevant_schedules = [
                ('A/B/AB Routes', 'A_B_AB_Routes_Weekday'),
                ('C Route', 'C_Route_Weekday'),
                ('PTC & Mill 19', 'PTC_Mill19_Weekday'),
                ('Bakery Square', 'Bakery_Square_Weekday'),
            ]
        
        # Check each schedule for the given time
        for route_display_name, schedule_key in relevant_schedules:
            if schedule_key in schedules:
                df = schedules[schedule_key]
                # Simple check - in a real implementation, you'd parse times properly
                active_shuttles.append({
                    'route': route_display_name,
                    'schedule': df.to_dict('records')
                })
        
        return active_shuttles


def test_scraper():
    """Test function to demonstrate scraper usage."""
    scraper = CMUShuttleScraper()
    data = scraper.get_all_shuttle_data()
    
    if data['success']:
        print("✓ Successfully scraped shuttle data")
        print(f"\nFound {len(data['routes'])} routes:")
        for route_name in data['routes'].keys():
            print(f"  - {route_name}")
        
        print(f"\nFound {len(data['schedules'])} schedule tables:")
        for schedule_name, df in data['schedules'].items():
            print(f"  - {schedule_name}: {df.shape[0]} rows × {df.shape[1]} columns")
    else:
        print("✗ Failed to scrape shuttle data")
        print(f"Error: {data.get('error', 'Unknown error')}")
    
    return data


if __name__ == "__main__":
    test_scraper()

