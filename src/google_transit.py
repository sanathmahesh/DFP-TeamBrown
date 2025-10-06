"""
Google Maps Transit API integration.
Module for fetching public transportation options and comparing with shuttle timings.
"""

import googlemaps
from datetime import datetime
from typing import Dict, List, Optional
import os


class GoogleTransitAPI:
    """Handler for Google Maps Transit API requests."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Google Transit API client.
        
        Args:
            api_key: Google Maps API key (if None, reads from environment)
        """
        self.api_key = api_key or os.getenv('GOOGLE_MAPS_API_KEY')
        self.client = None
        
        if self.api_key:
            try:
                self.client = googlemaps.Client(key=self.api_key)
            except Exception as e:
                print(f"Error initializing Google Maps client: {e}")
    
    def get_transit_directions(
        self, 
        origin: str, 
        destination: str, 
        departure_time: Optional[datetime] = None
    ) -> Dict:
        """
        Get transit directions between two locations.
        
        Args:
            origin: Starting location (address or coordinates)
            destination: Destination location (address or coordinates)
            departure_time: Desired departure time (defaults to now)
            
        Returns:
            Dict containing transit route information
        """
        if not self.client:
            return {
                'success': False,
                'error': 'Google Maps API key not configured'
            }
        
        try:
            if departure_time is None:
                departure_time = datetime.now()
            
            directions = self.client.directions(
                origin,
                destination,
                mode="transit",
                departure_time=departure_time
            )
            
            if not directions:
                return {
                    'success': False,
                    'error': 'No transit routes found'
                }
            
            # Parse and format the response
            routes = []
            for route in directions:
                leg = route['legs'][0]
                routes.append({
                    'duration': leg['duration']['text'],
                    'duration_seconds': leg['duration']['value'],
                    'distance': leg['distance']['text'],
                    'steps': self._parse_steps(leg['steps']),
                    'departure_time': leg['departure_time']['text'],
                    'arrival_time': leg['arrival_time']['text']
                })
            
            return {
                'success': True,
                'routes': routes
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Error fetching transit directions: {str(e)}'
            }
    
    def _parse_steps(self, steps: List[Dict]) -> List[Dict]:
        """Parse transit steps into a simplified format."""
        parsed_steps = []
        
        for step in steps:
            step_info = {
                'travel_mode': step['travel_mode'],
                'distance': step['distance']['text'],
                'duration': step['duration']['text'],
                'instructions': step.get('html_instructions', '')
            }
            
            # Add transit-specific information
            if 'transit_details' in step:
                transit = step['transit_details']
                step_info['transit'] = {
                    'line': transit['line']['short_name'],
                    'departure_stop': transit['departure_stop']['name'],
                    'arrival_stop': transit['arrival_stop']['name'],
                    'num_stops': transit.get('num_stops', 0)
                }
            
            parsed_steps.append(step_info)
        
        return parsed_steps
    
    def compare_with_shuttle(
        self,
        origin: str,
        destination: str,
        shuttle_time: int
    ) -> Dict:
        """
        Compare public transit with shuttle timing.
        
        Args:
            origin: Starting location
            destination: Destination location
            shuttle_time: Shuttle travel time in seconds
            
        Returns:
            Dict containing comparison data
        """
        transit_data = self.get_transit_directions(origin, destination)
        
        if not transit_data['success']:
            return transit_data
        
        comparisons = []
        for route in transit_data['routes']:
            transit_time = route['duration_seconds']
            time_diff = transit_time - shuttle_time
            
            comparisons.append({
                'route': route,
                'shuttle_time_seconds': shuttle_time,
                'time_difference_seconds': time_diff,
                'is_faster': time_diff < 0,
                'percentage_difference': (time_diff / shuttle_time) * 100
            })
        
        return {
            'success': True,
            'comparisons': comparisons
        }


# Placeholder for testing without API key
def get_mock_transit_data(origin: str, destination: str) -> Dict:
    """
    Return mock transit data for testing purposes.
    
    Args:
        origin: Starting location
        destination: Destination location
        
    Returns:
        Mock transit data
    """
    return {
        'success': True,
        'routes': [
            {
                'duration': '25 mins',
                'duration_seconds': 1500,
                'distance': '3.2 miles',
                'departure_time': '10:30 AM',
                'arrival_time': '10:55 AM',
                'steps': [
                    {
                        'travel_mode': 'WALKING',
                        'distance': '0.2 miles',
                        'duration': '4 mins',
                        'instructions': 'Walk to bus stop'
                    },
                    {
                        'travel_mode': 'TRANSIT',
                        'distance': '2.8 miles',
                        'duration': '18 mins',
                        'instructions': 'Take bus 61C',
                        'transit': {
                            'line': '61C',
                            'departure_stop': 'Forbes Ave at Morewood Ave',
                            'arrival_stop': 'Fifth Ave at Aiken Ave',
                            'num_stops': 8
                        }
                    },
                    {
                        'travel_mode': 'WALKING',
                        'distance': '0.2 miles',
                        'duration': '3 mins',
                        'instructions': 'Walk to destination'
                    }
                ]
            }
        ]
    }


if __name__ == "__main__":
    print("Google Transit API module")
    print("To use this module, set your GOOGLE_MAPS_API_KEY environment variable")
    print("\nExample mock data:")
    mock_data = get_mock_transit_data("CMU Campus", "Shadyside")
    print(f"Routes found: {len(mock_data['routes'])}")

