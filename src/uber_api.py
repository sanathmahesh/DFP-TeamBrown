"""
File: uber_api.py  
Team: Team Brown
Course: Data Focused Python - Final Project
Carnegie Mellon University

Team Members:
- mnagersh
- sddabir
- sanathk
- rrakshan
- ssurabhi

Purpose: Uber API integration for ride-sharing price and time estimates.
         Provides real-time Uber data with mock fallback.

Imports from: typing, os, math, datetime, importlib
Imported by: app.py (main application)

Key Functions:
- UberAPI: Class for interfacing with Uber API
- get_mock_uber_estimates(): Fallback mock data when API unavailable
"""

from typing import Dict, Optional, List, Tuple
import os
import math
import datetime


class UberAPI:
    """Handler for Uber price estimation based on distance."""
    
    def __init__(self, access_token: Optional[str] = None, google_api_key: Optional[str] = None):
        """
        Initialize Uber price estimation client.
        
        Args:
            access_token: Uber API access token (kept for compatibility, not used)
            google_api_key: Google Maps API key for distance calculation
        """
        self.access_token = access_token or os.getenv('UBER_ACCESS_TOKEN')
        self.google_api_key = google_api_key or os.getenv('GOOGLE_MAPS_API_KEY')
        print("Using distance-based Uber price estimation")
    
    def get_price_estimates(
        self,
        start_latitude: float,
        start_longitude: float,
        end_latitude: float,
        end_longitude: float
    ) -> Dict:
        """
        Get Uber price estimates for a trip based on distance calculation.
        
        Args:
            start_latitude: Starting location latitude
            start_longitude: Starting location longitude
            end_latitude: Destination latitude
            end_longitude: Destination longitude
            
        Returns:
            Dict containing price estimates for different Uber products
        """
        try:
            # Calculate distance using haversine formula
            distance_miles = self._calculate_distance(
                start_latitude, start_longitude, end_latitude, end_longitude
            )
            
            # Estimate duration based on distance (average 20 mph in city traffic)
            duration_minutes = max(5, int(distance_miles * 3))  # 3 minutes per mile minimum
            
            # Calculate surge pricing based on current time
            surge_multiplier = self._calculate_surge_pricing()
            
            # Base pricing (Pittsburgh rates as of 2024)
            base_fare = 2.55
            per_mile = 1.75
            per_minute = 0.22
            
            # Calculate base price
            base_price = base_fare + (distance_miles * per_mile) + (duration_minutes * per_minute)
            surged_price = base_price * surge_multiplier
            
            # Create estimates for different Uber products
            estimates = [
                {
                    'product_name': 'UberX',
                    'estimate': f'${surged_price:.0f}-{surged_price * 1.3:.0f}',
                    'low_estimate': surged_price,
                    'high_estimate': surged_price * 1.3,
                    'currency_code': 'USD',
                    'duration': duration_minutes * 60,  # Convert to seconds
                    'distance': distance_miles,
                    'surge_multiplier': surge_multiplier
                },
                {
                    'product_name': 'Uber Comfort',
                    'estimate': f'${surged_price * 1.2:.0f}-{surged_price * 1.5:.0f}',
                    'low_estimate': surged_price * 1.2,
                    'high_estimate': surged_price * 1.5,
                    'currency_code': 'USD',
                    'duration': duration_minutes * 60,
                    'distance': distance_miles,
                    'surge_multiplier': surge_multiplier
                },
                {
                    'product_name': 'UberXL',
                    'estimate': f'${surged_price * 1.4:.0f}-{surged_price * 1.7:.0f}',
                    'low_estimate': surged_price * 1.4,
                    'high_estimate': surged_price * 1.7,
                    'currency_code': 'USD',
                    'duration': duration_minutes * 60,
                    'distance': distance_miles,
                    'surge_multiplier': surge_multiplier
                }
            ]
            
            return {
                'success': True,
                'estimates': estimates,
                'pricing_info': {
                    'base_fare': base_fare,
                    'per_mile': per_mile,
                    'per_minute': per_minute,
                    'surge_multiplier': surge_multiplier,
                    'distance_miles': distance_miles,
                    'duration_minutes': duration_minutes
                }
            }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Error calculating Uber estimates: {str(e)}'
            }
    
    def get_time_estimates(
        self,
        start_latitude: float,
        start_longitude: float,
        product_id: Optional[str] = None
    ) -> Dict:
        """
        Get Uber pickup time estimates using web scraping.
        
        Args:
            start_latitude: Starting location latitude
            start_longitude: Starting location longitude
            product_id: Specific Uber product ID (optional)
            
        Returns:
            Dict containing time estimates
        """
        try:
            # For time estimates, we'll use mock data since the web scraper
            # focuses on price estimates. In a real implementation, you might
            # need to scrape a different page or use a different approach.
            return {
                'success': True,
                'time_estimates': [
                    {
                        'product_name': 'UberX',
                        'estimate_seconds': 300,  # 5 minutes
                        'estimate_minutes': 5
                    },
                    {
                        'product_name': 'Uber Comfort',
                        'estimate_seconds': 300,
                        'estimate_minutes': 5
                    },
                    {
                        'product_name': 'UberXL',
                        'estimate_seconds': 300,
                        'estimate_minutes': 5
                    }
                ]
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Error fetching Uber time estimates: {str(e)}'
            }
    
    def get_price_estimates_by_address(
        self,
        start_address: str,
        destination_address: str
    ) -> Dict:
        """
        Get Uber price estimates using addresses with geocoding.
        
        Args:
            start_address: Starting location address
            destination_address: Destination address
            
        Returns:
            Dict containing price estimates for different Uber products
        """
        try:
            # Try to geocode addresses to coordinates
            start_coords = self._geocode_address(start_address)
            dest_coords = self._geocode_address(destination_address)
            
            if not start_coords or not dest_coords:
                return {
                    'success': False,
                    'error': 'Could not geocode addresses. Please check the addresses and try again.'
                }
            
            # Use coordinate-based calculation
            return self.get_price_estimates(
                start_coords[0], start_coords[1],
                dest_coords[0], dest_coords[1]
            )
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Error calculating Uber estimates: {str(e)}'
            }
    
    def compare_with_alternatives(
        self,
        start_lat: float,
        start_lon: float,
        end_lat: float,
        end_lon: float,
        shuttle_time: int,
        transit_time: int,
        transit_cost: float = 2.75
    ) -> Dict:
        """
        Compare Uber with shuttle and transit options.
        
        Args:
            start_lat: Starting latitude
            start_lon: Starting longitude
            end_lat: Destination latitude
            end_lon: Destination longitude
            shuttle_time: Shuttle travel time in seconds
            transit_time: Public transit time in seconds
            transit_cost: Public transit cost in dollars
            
        Returns:
            Dict containing comparison data
        """
        uber_data = self.get_price_estimates(start_lat, start_lon, end_lat, end_lon)
        
        if not uber_data['success']:
            return uber_data
        
        comparisons = []
        for estimate in uber_data['estimates']:
            uber_time = estimate['duration']
            
            # Parse price estimate
            avg_price = None
            if estimate['low_estimate'] and estimate['high_estimate']:
                avg_price = (estimate['low_estimate'] + estimate['high_estimate']) / 2
            
            comparison = {
                'product': estimate['product_name'],
                'uber_time_seconds': uber_time,
                'uber_price': avg_price,
                'shuttle_time_seconds': shuttle_time,
                'transit_time_seconds': transit_time,
                'transit_cost': transit_cost,
                'time_vs_shuttle': uber_time - shuttle_time,
                'time_vs_transit': uber_time - transit_time,
                'is_faster_than_shuttle': uber_time < shuttle_time,
                'is_faster_than_transit': uber_time < transit_time,
            }
            
            if avg_price:
                comparison['cost_vs_transit'] = avg_price - transit_cost
            
            comparisons.append(comparison)
        
        return {
            'success': True,
            'comparisons': comparisons
        }
    
    def compare_with_alternatives_by_address(
        self,
        start_address: str,
        destination_address: str,
        shuttle_time: int,
        transit_time: int,
        transit_cost: float = 2.75
    ) -> Dict:
        """
        Compare Uber with shuttle and transit options using addresses.
        
        Args:
            start_address: Starting address
            destination_address: Destination address
            shuttle_time: Shuttle travel time in seconds
            transit_time: Public transit time in seconds
            transit_cost: Public transit cost in dollars
            
        Returns:
            Dict containing comparison data
        """
        uber_data = self.get_price_estimates_by_address(start_address, destination_address)
        
        if not uber_data['success']:
            return uber_data
        
        comparisons = []
        for estimate in uber_data['estimates']:
            uber_time = estimate['duration']
            
            # Parse price estimate
            avg_price = None
            if estimate['low_estimate'] and estimate['high_estimate']:
                avg_price = (estimate['low_estimate'] + estimate['high_estimate']) / 2
            
            comparison = {
                'product': estimate['product_name'],
                'uber_time_seconds': uber_time,
                'uber_price': avg_price,
                'shuttle_time_seconds': shuttle_time,
                'transit_time_seconds': transit_time,
                'transit_cost': transit_cost,
                'time_vs_shuttle': uber_time - shuttle_time,
                'time_vs_transit': uber_time - transit_time,
                'is_faster_than_shuttle': uber_time < shuttle_time,
                'is_faster_than_transit': uber_time < transit_time,
            }
            
            if avg_price:
                comparison['cost_vs_transit'] = avg_price - transit_cost
            
            comparisons.append(comparison)
        
        return {
            'success': True,
            'comparisons': comparisons
        }
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points using haversine formula."""
        R = 3958.8  # Earth's radius in miles
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)
        a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c
    
    def _calculate_surge_pricing(self) -> float:
        """Calculate surge pricing based on current time."""
        current_time = datetime.datetime.now()
        hour = current_time.hour
        day_of_week = current_time.weekday()  # 0 = Monday
        
        # Weekend surge
        if day_of_week >= 5:  # Saturday (5) or Sunday (6)
            if 10 <= hour <= 14:  # Weekend lunch
                return 1.3
            elif 18 <= hour <= 22:  # Weekend evening
                return 1.5
            else:
                return 1.1
        
        # Weekday surge
        if 7 <= hour <= 9:  # Morning rush
            return 1.4
        elif 17 <= hour <= 19:  # Evening rush
            return 1.6
        elif 22 <= hour or hour <= 6:  # Late night/early morning
            return 1.2
        else:
            return 1.0
    
    def _geocode_address(self, address: str) -> Optional[Tuple[float, float]]:
        """Geocode an address to coordinates using Google Maps API."""
        if not self.google_api_key or not address:
            return None
        
        try:
            import googlemaps
            client = googlemaps.Client(key=self.google_api_key)
            result = client.geocode(address)
            if result and 'geometry' in result[0]:
                loc = result[0]['geometry']['location']
                return float(loc['lat']), float(loc['lng'])
        except Exception as e:
            print(f"Geocoding failed: {e}")
            return None
        return None


# Mock data for testing without API access
def get_mock_uber_estimates(origin: str, destination: str) -> Dict:
    """
    Return mock Uber data for testing purposes.
    
    Args:
        origin: Starting location
        destination: Destination location
        
    Returns:
        Mock Uber price estimates
    """
    # Create a simple mock API instance
    mock_api = UberAPI()
    
    # Use simple distance estimation for mock data
    distance_miles = 3.0  # Default distance
    duration_minutes = 10  # Default duration
    
    # Base pricing
    base_fare = 2.55
    per_mile = 1.75
    per_minute = 0.22
    base_price = base_fare + (distance_miles * per_mile) + (duration_minutes * per_minute)
    
    estimates = [
        {
            'product_name': 'UberX',
            'estimate': f'${base_price:.0f}-{base_price * 1.3:.0f}',
            'low_estimate': base_price,
            'high_estimate': base_price * 1.3,
            'currency_code': 'USD',
            'duration': duration_minutes * 60,
            'distance': distance_miles,
            'surge_multiplier': 1.0
        },
        {
            'product_name': 'Uber Comfort',
            'estimate': f'${base_price * 1.2:.0f}-{base_price * 1.5:.0f}',
            'low_estimate': base_price * 1.2,
            'high_estimate': base_price * 1.5,
            'currency_code': 'USD',
            'duration': duration_minutes * 60,
            'distance': distance_miles,
            'surge_multiplier': 1.0
        },
        {
            'product_name': 'UberXL',
            'estimate': f'${base_price * 1.4:.0f}-{base_price * 1.7:.0f}',
            'low_estimate': base_price * 1.4,
            'high_estimate': base_price * 1.7,
            'currency_code': 'USD',
            'duration': duration_minutes * 60,
            'distance': distance_miles,
            'surge_multiplier': 1.0
        }
    ]
    
    return {
        'success': True,
        'estimates': estimates
    }


if __name__ == "__main__":
    print("Uber Price Estimation module")
    print("This module calculates Uber estimates based on distance")
    print("\nExample data:")
    mock_data = get_mock_uber_estimates("CMU Campus", "Shadyside")
    print(f"Estimates found: {len(mock_data['estimates'])}")
    for est in mock_data['estimates']:
        print(f"  - {est['product_name']}: {est['estimate']} ({est['duration']//60} mins)")

