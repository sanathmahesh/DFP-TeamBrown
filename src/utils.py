"""
Utility functions for the CMU Transportation Comparison Tool.
"""

from datetime import datetime, time
from typing import Tuple, List, Dict
import re


def parse_time_string(time_str: str) -> Tuple[int, int, str]:
    """
    Parse a time string in format "H:MM AM/PM" into components.
    
    Args:
        time_str: Time string (e.g., "7:30 AM", "10:45 PM")
        
    Returns:
        Tuple of (hour, minute, period) where period is 'AM' or 'PM'
    """
    time_str = time_str.strip()
    pattern = r'(\d{1,2}):(\d{2})\s*(AM|PM)'
    match = re.match(pattern, time_str, re.IGNORECASE)
    
    if not match:
        raise ValueError(f"Invalid time format: {time_str}")
    
    hour = int(match.group(1))
    minute = int(match.group(2))
    period = match.group(3).upper()
    
    return hour, minute, period


def time_to_minutes(time_str: str) -> int:
    """
    Convert time string to minutes since midnight.
    
    Args:
        time_str: Time string (e.g., "7:30 AM")
        
    Returns:
        Minutes since midnight
    """
    hour, minute, period = parse_time_string(time_str)
    
    # Convert to 24-hour format
    if period == 'PM' and hour != 12:
        hour += 12
    elif period == 'AM' and hour == 12:
        hour = 0
    
    return hour * 60 + minute


def format_duration(seconds: int) -> str:
    """
    Format duration in seconds to human-readable string.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted string (e.g., "25 mins", "1 hour 30 mins")
    """
    if seconds < 60:
        return f"{seconds} secs"
    
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes} mins"
    
    hours = minutes // 60
    remaining_mins = minutes % 60
    
    if remaining_mins == 0:
        return f"{hours} hour{'s' if hours > 1 else ''}"
    
    return f"{hours} hour{'s' if hours > 1 else ''} {remaining_mins} mins"


def get_current_day_type() -> str:
    """
    Get current day type (weekday or weekend).
    
    Returns:
        'weekday' or 'weekend'
    """
    day = datetime.now().weekday()
    return 'weekend' if day >= 5 else 'weekday'


def get_day_of_week() -> str:
    """
    Get current day of week name.
    
    Returns:
        Day name (e.g., 'Monday', 'Tuesday')
    """
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    return days[datetime.now().weekday()]


def find_next_shuttle(current_time_str: str, schedule: List[str]) -> Tuple[str, int]:
    """
    Find the next available shuttle from a schedule.
    
    Args:
        current_time_str: Current time as string (e.g., "2:30 PM")
        schedule: List of shuttle times
        
    Returns:
        Tuple of (next_shuttle_time, minutes_until_shuttle)
    """
    current_minutes = time_to_minutes(current_time_str)
    
    for shuttle_time in schedule:
        try:
            shuttle_minutes = time_to_minutes(shuttle_time)
            if shuttle_minutes > current_minutes:
                wait_time = shuttle_minutes - current_minutes
                return shuttle_time, wait_time
        except ValueError:
            continue
    
    # If no shuttle found after current time, return first shuttle (next day)
    if schedule:
        first_shuttle = schedule[0]
        first_minutes = time_to_minutes(first_shuttle)
        wait_time = (24 * 60 - current_minutes) + first_minutes
        return first_shuttle, wait_time
    
    return "No service", 0


def calculate_cost_savings(
    uber_cost: float,
    transit_cost: float = 2.75,
    shuttle_cost: float = 0.0
) -> Dict[str, float]:
    """
    Calculate cost savings between different transportation options.
    
    Args:
        uber_cost: Uber ride cost
        transit_cost: Public transit cost (default $2.75 for Pittsburgh)
        shuttle_cost: Shuttle cost (default $0 - free for CMU)
        
    Returns:
        Dict with savings comparisons
    """
    return {
        'uber_vs_transit': uber_cost - transit_cost,
        'uber_vs_shuttle': uber_cost - shuttle_cost,
        'transit_vs_shuttle': transit_cost - shuttle_cost,
        'shuttle_savings_pct': ((uber_cost - shuttle_cost) / uber_cost * 100) if uber_cost > 0 else 0
    }


def format_currency(amount: float, currency: str = 'USD') -> str:
    """
    Format currency amount.
    
    Args:
        amount: Amount to format
        currency: Currency code (default USD)
        
    Returns:
        Formatted currency string
    """
    symbols = {
        'USD': '$',
        'EUR': '€',
        'GBP': '£'
    }
    
    symbol = symbols.get(currency, '$')
    return f"{symbol}{amount:.2f}"


def calculate_time_savings(
    time1_seconds: int,
    time2_seconds: int
) -> Dict[str, any]:
    """
    Calculate time savings between two options.
    
    Args:
        time1_seconds: First time option in seconds
        time2_seconds: Second time option in seconds
        
    Returns:
        Dict with time difference information
    """
    diff_seconds = time1_seconds - time2_seconds
    diff_minutes = abs(diff_seconds) // 60
    
    return {
        'difference_seconds': diff_seconds,
        'difference_minutes': diff_minutes,
        'difference_formatted': format_duration(abs(diff_seconds)),
        'first_is_faster': diff_seconds > 0,
        'percentage_difference': (diff_seconds / time2_seconds * 100) if time2_seconds > 0 else 0
    }


# CMU-specific location presets
CMU_LOCATIONS = {
    'Main Campus': {
        'address': '5000 Forbes Avenue, Pittsburgh, PA 15213',
        'lat': 40.4433,
        'lon': -79.9436
    },
    'Morewood Parking': {
        'address': 'Morewood Avenue, Pittsburgh, PA 15213',
        'lat': 40.4458,
        'lon': -79.9461
    },
    'PTC': {
        'address': '700 Technology Drive, Pittsburgh, PA 15219',
        'lat': 40.4542,
        'lon': -79.9196
    },
    'Shadyside': {
        'address': '5500 Centre Avenue, Pittsburgh, PA 15232',
        'lat': 40.4529,
        'lon': -79.9325
    },
    'Squirrel Hill': {
        'address': 'Forbes Avenue & Murray Avenue, Pittsburgh, PA 15217',
        'lat': 40.4347,
        'lon': -79.9234
    },
    'Bakery Square': {
        'address': '6425 Penn Avenue, Pittsburgh, PA 15206',
        'lat': 40.4633,
        'lon': -79.9214
    }
}


def get_location_coordinates(location_name: str) -> Tuple[float, float]:
    """
    Get coordinates for a CMU location preset.
    
    Args:
        location_name: Name of the location
        
    Returns:
        Tuple of (latitude, longitude)
    """
    if location_name in CMU_LOCATIONS:
        loc = CMU_LOCATIONS[location_name]
        return loc['lat'], loc['lon']
    
    raise ValueError(f"Unknown location: {location_name}")


if __name__ == "__main__":
    print("Utility functions module")
    print("\nTesting time parsing:")
    print(f"  '7:30 AM' = {time_to_minutes('7:30 AM')} minutes since midnight")
    print(f"  '2:45 PM' = {time_to_minutes('2:45 PM')} minutes since midnight")
    
    print("\nTesting duration formatting:")
    print(f"  900 seconds = {format_duration(900)}")
    print(f"  5400 seconds = {format_duration(5400)}")
    
    print("\nCMU Locations:")
    for loc_name in CMU_LOCATIONS:
        print(f"  - {loc_name}")

