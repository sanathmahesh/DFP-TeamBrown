"""
POGOH (Pittsburgh's bike-share system) integration module.
Handles POGOH station data and bike availability information.
Integrates with Google Directions API for dynamic travel time estimation.
"""

import csv
import math
import os
import importlib
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class POGOHStation:
    """Represents a POGOH bike station."""
    id: int
    name: str
    total_docks: int
    latitude: float
    longitude: float
    available_bikes: int = 0  # This would be updated from real-time API


class POGOHBikesAPI:
    """API for POGOH bike-share system with Google Directions API integration."""
    
    def __init__(self, csv_file_path: str = "POGOH Dataset.csv", google_api_key: Optional[str] = None):
        """
        Initialize POGOH API with station data.
        
        Args:
            csv_file_path: Path to the POGOH Dataset CSV file
            google_api_key: Google Maps API key for dynamic routing
        """
        self.csv_file_path = csv_file_path
        self.stations = self._load_stations()
        self.google_api_key = google_api_key or os.getenv('GOOGLE_MAPS_API_KEY')
        self.google_client = None
        self.init_error: Optional[str] = None
        
        if self.google_api_key:
            try:
                googlemaps = importlib.import_module('googlemaps')
                self.google_client = googlemaps.Client(key=self.google_api_key)
            except ImportError:
                self.init_error = "googlemaps package not installed"
                print("googlemaps package not installed. Using static estimates for bike routes.")
            except Exception as e:
                self.init_error = f"Error initializing Google Maps client: {e}"
                print(f"Error initializing Google Maps client: {e}")
    
    def _load_stations(self) -> List[POGOHStation]:
        """Load POGOH stations from CSV file."""
        try:
            stations = []
            
            with open(self.csv_file_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    station = POGOHStation(
                        id=int(row['Id']),
                        name=str(row['Name']),
                        total_docks=int(row['Total Docks']),
                        latitude=float(row['Latitude']),
                        longitude=float(row['Longitude'])
                    )
                    stations.append(station)
            
            return stations
        except Exception as e:
            print(f"Error loading POGOH stations: {e}")
            return []
    
    def get_all_stations(self) -> List[POGOHStation]:
        """Get all POGOH stations."""
        return self.stations
    
    def get_stations_near_location(self, lat: float, lon: float, radius_miles: float = 1.0) -> List[Tuple[POGOHStation, float]]:
        """
        Get POGOH stations within a specified radius of a location.
        
        Args:
            lat: Latitude of the location
            lon: Longitude of the location
            radius_miles: Search radius in miles
            
        Returns:
            List of tuples containing (station, distance_in_miles)
        """
        nearby_stations = []
        
        for station in self.stations:
            distance = self._haversine_miles(lat, lon, station.latitude, station.longitude)
            if distance <= radius_miles:
                nearby_stations.append((station, distance))
        
        # Sort by distance
        nearby_stations.sort(key=lambda x: x[1])
        return nearby_stations
    
    def get_nearest_station(self, lat: float, lon: float) -> Tuple[Optional[POGOHStation], float]:
        """
        Get the nearest POGOH station to a location.
        
        Args:
            lat: Latitude of the location
            lon: Longitude of the location
            
        Returns:
            Tuple of (nearest_station, distance_in_miles)
        """
        if not self.stations:
            return None, float('inf')
        
        nearest_station = None
        min_distance = float('inf')
        
        for station in self.stations:
            distance = self._haversine_miles(lat, lon, station.latitude, station.longitude)
            if distance < min_distance:
                min_distance = distance
                nearest_station = station
        
        return nearest_station, min_distance
    
    def _get_google_bike_directions(self, origin_lat: float, origin_lon: float, 
                                   dest_lat: float, dest_lon: float) -> Optional[Dict]:
        """
        Get bike directions from Google Directions API.
        
        Args:
            origin_lat: Origin latitude
            origin_lon: Origin longitude
            dest_lat: Destination latitude
            dest_lon: Destination longitude
            
        Returns:
            Dictionary with Google bike directions or None if unavailable
        """
        if not self.google_client:
            return None
        
        try:
            origin = f"{origin_lat},{origin_lon}"
            destination = f"{dest_lat},{dest_lon}"
            
            directions = self.google_client.directions(
                origin,
                destination,
                mode="bicycling",
                departure_time=datetime.now()
            )
            
            if not directions:
                return None
            
            leg = directions[0]['legs'][0]
            return {
                'duration_seconds': leg['duration']['value'],
                'distance_meters': leg['distance']['value'],
                'duration_text': leg['duration']['text'],
                'distance_text': leg['distance']['text']
            }
            
        except Exception as e:
            print(f"Error getting Google bike directions: {e}")
            return None
    
    def _get_google_walking_directions(self, origin_lat: float, origin_lon: float, 
                                      dest_lat: float, dest_lon: float) -> Optional[Dict]:
        """
        Get walking directions from Google Directions API.
        
        Args:
            origin_lat: Origin latitude
            origin_lon: Origin longitude
            dest_lat: Destination latitude
            dest_lon: Destination longitude
            
        Returns:
            Dictionary with Google walking directions or None if unavailable
        """
        if not self.google_client:
            return None
        
        try:
            origin = f"{origin_lat},{origin_lon}"
            destination = f"{dest_lat},{dest_lon}"
            
            directions = self.google_client.directions(
                origin,
                destination,
                mode="walking",
                departure_time=datetime.now()
            )
            
            if not directions:
                return None
            
            leg = directions[0]['legs'][0]
            return {
                'duration_seconds': leg['duration']['value'],
                'distance_meters': leg['distance']['value'],
                'duration_text': leg['duration']['text'],
                'distance_text': leg['distance']['text']
            }
            
        except Exception as e:
            print(f"Error getting Google walking directions: {e}")
            return None

    def find_route_between_stations(self, origin_lat: float, origin_lon: float, 
                                  dest_lat: float, dest_lon: float, max_walk_distance_miles: float = 1.0) -> Optional[Dict]:
        """
        Find a bike route between two locations using POGOH stations with Google API integration.
        
        Args:
            origin_lat: Origin latitude
            origin_lon: Origin longitude
            dest_lat: Destination latitude
            dest_lon: Destination longitude
            max_walk_distance_miles: Maximum walking distance to consider a station accessible
            
        Returns:
            Dictionary with route information or None if no suitable route found
        """
        # Find nearest stations to origin and destination
        origin_station, origin_dist = self.get_nearest_station(origin_lat, origin_lon)
        dest_station, dest_dist = self.get_nearest_station(dest_lat, dest_lon)
        
        # Check if stations are within reasonable walking distance
        if not origin_station or origin_dist > max_walk_distance_miles:
            return {
                'success': False,
                'error': 'no_origin_station',
                'message': f'No POGOH stations within {max_walk_distance_miles} miles of origin',
                'nearest_origin_distance': round(origin_dist, 2) if origin_station else None,
                'nearest_origin_station': origin_station.name if origin_station else None
            }
        
        if not dest_station or dest_dist > max_walk_distance_miles:
            return {
                'success': False,
                'error': 'no_destination_station',
                'message': f'No POGOH stations within {max_walk_distance_miles} miles of destination',
                'nearest_dest_distance': round(dest_dist, 2) if dest_station else None,
                'nearest_dest_station': dest_station.name if dest_station else None
            }
        
        # Try to get Google API data for more accurate estimates
        bike_google_data = None
        walk_to_origin_data = None
        walk_from_dest_data = None
        
        if self.google_client:
            # Get bike directions between stations
            bike_google_data = self._get_google_bike_directions(
                origin_station.latitude, origin_station.longitude,
                dest_station.latitude, dest_station.longitude
            )
            
            # Get walking directions to origin station
            walk_to_origin_data = self._get_google_walking_directions(
                origin_lat, origin_lon,
                origin_station.latitude, origin_station.longitude
            )
            
            # Get walking directions from destination station
            walk_from_dest_data = self._get_google_walking_directions(
                dest_station.latitude, dest_station.longitude,
                dest_lat, dest_lon
            )
        
        # Use Google data if available, otherwise fall back to static estimates
        if bike_google_data:
            bike_time_minutes = bike_google_data['duration_seconds'] // 60
            bike_distance_miles = bike_google_data['distance_meters'] * 0.000621371  # Convert meters to miles
        else:
            # Fallback to static calculation
            bike_distance = self._haversine_miles(
                origin_station.latitude, origin_station.longitude,
                dest_station.latitude, dest_station.longitude
            )
            bike_time_minutes = int((bike_distance / 10.0) * 60)  # 10 mph average
            bike_distance_miles = bike_distance
        
        if walk_to_origin_data:
            walk_to_station_minutes = walk_to_origin_data['duration_seconds'] // 60
        else:
            # Fallback to static calculation (3 mph walking speed)
            walk_to_station_minutes = int((origin_dist / 3.0) * 60)
        
        if walk_from_dest_data:
            walk_from_station_minutes = walk_from_dest_data['duration_seconds'] // 60
        else:
            # Fallback to static calculation (3 mph walking speed)
            walk_from_station_minutes = int((dest_dist / 3.0) * 60)
        
        total_time_minutes = walk_to_station_minutes + bike_time_minutes + walk_from_station_minutes
        
        return {
            'success': True,
            'origin_station': {
                'name': origin_station.name,
                'distance_miles': round(origin_dist, 2),
                'walk_time_minutes': walk_to_station_minutes
            },
            'destination_station': {
                'name': dest_station.name,
                'distance_miles': round(dest_dist, 2),
                'walk_time_minutes': walk_from_station_minutes
            },
            'bike_ride': {
                'distance_miles': round(bike_distance_miles, 2),
                'time_minutes': bike_time_minutes
            },
            'total_time_minutes': total_time_minutes,
            'cost': '$2.00',  # POGOH typical fare
            'uses_google_api': self.google_client is not None
        }
    
    def get_station_info(self, station_id: int) -> Optional[POGOHStation]:
        """Get information about a specific station by ID."""
        for station in self.stations:
            if station.id == station_id:
                return station
        return None
    
    def check_station_availability(self, lat: float, lon: float, radius_miles: float = 1.0) -> Dict:
        """
        Check if there are POGOH stations available near a location.
        
        Args:
            lat: Latitude of the location
            lon: Longitude of the location
            radius_miles: Search radius in miles
            
        Returns:
            Dictionary with station availability information
        """
        nearby_stations = self.get_stations_near_location(lat, lon, radius_miles)
        
        if not nearby_stations:
            return {
                'available': False,
                'message': f'No POGOH stations within {radius_miles} miles',
                'nearest_station': None,
                'nearest_distance': None,
                'stations_in_radius': []
            }
        
        nearest_station, nearest_distance = nearby_stations[0]
        
        return {
            'available': True,
            'message': f'Found {len(nearby_stations)} POGOH station(s) within {radius_miles} miles',
            'nearest_station': nearest_station.name,
            'nearest_distance': round(nearest_distance, 2),
            'stations_in_radius': [
                {
                    'name': station.name,
                    'distance': round(distance, 2),
                    'total_docks': station.total_docks
                }
                for station, distance in nearby_stations
            ]
        }
    
    def _haversine_miles(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate great-circle distance between two points in miles."""
        R = 3958.8  # Earth's radius in miles
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)
        
        a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c


def get_mock_pogoh_data(origin: str, destination: str) -> Dict:
    """
    Generate mock POGOH bike data for demonstration purposes.
    
    Args:
        origin: Origin location name
        destination: Destination location name
        
    Returns:
        Dictionary with mock POGOH route information
    """
    # Mock data for demonstration
    mock_routes = {
        ('Main Campus', 'Shadyside'): {
            'success': True,
            'origin_station': {
                'name': 'Forbes Ave at TCS Hall (CMU Campus)',
                'distance_miles': 0.1,
                'walk_time_minutes': 2
            },
            'destination_station': {
                'name': 'Centre Ave & Addison St',
                'distance_miles': 0.3,
                'walk_time_minutes': 6
            },
            'bike_ride': {
                'distance_miles': 1.2,
                'time_minutes': 8
            },
            'total_time_minutes': 16,
            'cost': '$2.00'
        },
        ('Shadyside', 'Bakery Square'): {
            'success': True,
            'origin_station': {
                'name': 'Centre Ave & Addison St',
                'distance_miles': 0.2,
                'walk_time_minutes': 4
            },
            'destination_station': {
                'name': 'Penn Ave & Putnam St (Bakery Square)',
                'distance_miles': 0.1,
                'walk_time_minutes': 2
            },
            'bike_ride': {
                'distance_miles': 0.8,
                'time_minutes': 5
            },
            'total_time_minutes': 11,
            'cost': '$2.00'
        }
    }
    
    # Try to find a matching route
    for (o, d), route_data in mock_routes.items():
        if o.lower() in origin.lower() and d.lower() in destination.lower():
            return route_data
        if o.lower() in destination.lower() and d.lower() in origin.lower():
            # Reverse the route
            reversed_route = route_data.copy()
            reversed_route['origin_station'] = route_data['destination_station']
            reversed_route['destination_station'] = route_data['origin_station']
            return reversed_route
    
    # Default mock route
    return {
        'success': True,
        'origin_station': {
            'name': 'Nearest POGOH Station',
            'distance_miles': 0.2,
            'walk_time_minutes': 4
        },
        'destination_station': {
            'name': 'Nearest POGOH Station',
            'distance_miles': 0.3,
            'walk_time_minutes': 6
        },
        'bike_ride': {
            'distance_miles': 1.5,
            'time_minutes': 10
        },
        'total_time_minutes': 20,
        'cost': '$2.00'
    }


# Test function
def test_pogoh_api():
    """Test the POGOH API functionality."""
    try:
        api = POGOHBikesAPI()
        stations = api.get_all_stations()
        
        print(f"✓ Loaded {len(stations)} POGOH stations")
        
        # Test finding stations near CMU
        cmu_lat, cmu_lon = 40.4449, -79.9429
        nearby = api.get_stations_near_location(cmu_lat, cmu_lon, radius_miles=0.5)
        
        print(f"Found {len(nearby)} stations within 0.5 miles of CMU:")
        for station, distance in nearby[:3]:  # Show first 3
            print(f"  - {station.name}: {distance:.2f} miles")
        
        # Test route finding
        route = api.find_route_between_stations(
            cmu_lat, cmu_lon, 40.4520, -79.9392  # CMU to Shadyside
        )
        
        if route:
            print(f"✓ Found bike route: {route['total_time_minutes']} minutes, {route['cost']}")
        else:
            print("✗ No bike route found")
            
    except Exception as e:
        print(f"✗ Error testing POGOH API: {e}")


if __name__ == "__main__":
    test_pogoh_api()
