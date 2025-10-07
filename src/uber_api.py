"""
Uber API integration.
Module for fetching Uber ride estimates and comparing costs/times with other transport options.
"""

from typing import Dict, Optional, List
import os
import importlib


class UberAPI:
    """Handler for Uber API requests."""
    
    def __init__(self, access_token: Optional[str] = None):
        """
        Initialize Uber API client.
        
        Args:
            access_token: Uber API access token (if None, reads from environment)
        """
        self.access_token = access_token or os.getenv('UBER_ACCESS_TOKEN')
        self.client = None
        
        if self.access_token:
            try:
                # Lazy import to avoid ImportError when package is absent
                uber_rides_session = importlib.import_module('uber_rides.session')
                uber_rides_client = importlib.import_module('uber_rides.client')
                session = uber_rides_session.Session(server_token=self.access_token)
                self.client = uber_rides_client.UberRidesClient(session)
            except ImportError:
                # Package not installed; downstream will fall back to mock
                print("uber_rides package not installed. Using mock Uber data if available.")
            except Exception as e:
                print(f"Error initializing Uber client: {e}")
    
    def get_price_estimates(
        self,
        start_latitude: float,
        start_longitude: float,
        end_latitude: float,
        end_longitude: float
    ) -> Dict:
        """
        Get Uber price estimates for a trip.
        
        Args:
            start_latitude: Starting location latitude
            start_longitude: Starting location longitude
            end_latitude: Destination latitude
            end_longitude: Destination longitude
            
        Returns:
            Dict containing price estimates for different Uber products
        """
        if not self.client:
            return {
                'success': False,
                'error': 'Uber API token not configured'
            }
        
        try:
            response = self.client.get_price_estimates(
                start_latitude=start_latitude,
                start_longitude=start_longitude,
                end_latitude=end_latitude,
                end_longitude=end_longitude
            )
            
            estimates = response.json.get('prices', [])
            
            if not estimates:
                return {
                    'success': False,
                    'error': 'No Uber estimates available'
                }
            
            formatted_estimates = []
            for estimate in estimates:
                formatted_estimates.append({
                    'product_name': estimate['display_name'],
                    'estimate': estimate.get('estimate', 'N/A'),
                    'low_estimate': estimate.get('low_estimate'),
                    'high_estimate': estimate.get('high_estimate'),
                    'currency_code': estimate.get('currency_code', 'USD'),
                    'duration': estimate['duration'],
                    'distance': estimate['distance'],
                    'surge_multiplier': estimate.get('surge_multiplier', 1.0)
                })
            
            return {
                'success': True,
                'estimates': formatted_estimates
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Error fetching Uber estimates: {str(e)}'
            }
    
    def get_time_estimates(
        self,
        start_latitude: float,
        start_longitude: float,
        product_id: Optional[str] = None
    ) -> Dict:
        """
        Get Uber pickup time estimates.
        
        Args:
            start_latitude: Starting location latitude
            start_longitude: Starting location longitude
            product_id: Specific Uber product ID (optional)
            
        Returns:
            Dict containing time estimates
        """
        if not self.client:
            return {
                'success': False,
                'error': 'Uber API token not configured'
            }
        
        try:
            response = self.client.get_pickup_time_estimates(
                start_latitude=start_latitude,
                start_longitude=start_longitude,
                product_id=product_id
            )
            
            times = response.json.get('times', [])
            
            formatted_times = []
            for time_est in times:
                formatted_times.append({
                    'product_name': time_est['display_name'],
                    'estimate_seconds': time_est['estimate'],
                    'estimate_minutes': time_est['estimate'] // 60
                })
            
            return {
                'success': True,
                'time_estimates': formatted_times
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Error fetching Uber time estimates: {str(e)}'
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
    return {
        'success': True,
        'estimates': [
            {
                'product_name': 'UberX',
                'estimate': '$8-11',
                'low_estimate': 8,
                'high_estimate': 11,
                'currency_code': 'USD',
                'duration': 780,  # 13 minutes
                'distance': 3.2,
                'surge_multiplier': 1.0
            },
            {
                'product_name': 'Uber Comfort',
                'estimate': '$10-14',
                'low_estimate': 10,
                'high_estimate': 14,
                'currency_code': 'USD',
                'duration': 780,
                'distance': 3.2,
                'surge_multiplier': 1.0
            },
            {
                'product_name': 'UberXL',
                'estimate': '$13-17',
                'low_estimate': 13,
                'high_estimate': 17,
                'currency_code': 'USD',
                'duration': 780,
                'distance': 3.2,
                'surge_multiplier': 1.0
            }
        ]
    }


if __name__ == "__main__":
    print("Uber API module")
    print("To use this module, set your UBER_ACCESS_TOKEN environment variable")
    print("\nExample mock data:")
    mock_data = get_mock_uber_estimates("CMU Campus", "Shadyside")
    print(f"Estimates found: {len(mock_data['estimates'])}")
    for est in mock_data['estimates']:
        print(f"  - {est['product_name']}: {est['estimate']} ({est['duration']//60} mins)")

