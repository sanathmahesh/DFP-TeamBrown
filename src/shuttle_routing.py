"""
Shuttle routing utilities: stops database, route sequences, and schedule-aware planning.

This module computes a shuttle plan between two coordinates by:
- Finding nearest origin/destination shuttle stops
- Determining a plausible route that connects them (same route sequence)
- Estimating wait time based on headways and operating windows by route/day
- Estimating in-vehicle travel time based on distance along the route
- Optionally estimating walking times to/from stops via Google Directions
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timedelta
from typing import Dict, List, Optional, Tuple
import importlib
import math


# ------------------------------
# Data models
# ------------------------------

@dataclass(frozen=True)
class Stop:
    name: str
    lat: float
    lon: float


@dataclass(frozen=True)
class RouteDefinition:
    name: str
    stops: List[Stop]  # ordered sequence (one canonical direction)
    weekday_headway_min: int
    weekend_headway_min: Optional[int]
    service_span_weekday: Tuple[time, time]
    service_span_weekend: Optional[Tuple[time, time]]


# ------------------------------
# Geometry helpers
# ------------------------------

def haversine_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 3958.8
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def walking_minutes_heuristic(miles: float) -> int:
    # 3 mph walking speed
    return max(1, int(round((miles / 3.0) * 60)))


# ------------------------------
# Core shuttle network (minimal but useful set of stops)
# Note: These are representative stops to make routing useful now. You can
# expand with full stop lists later.
# ------------------------------

MOREWOOD_FORBES = Stop("Morewood & Forbes (Main Campus)", 40.4449, -79.9429)
FIFTH_AIKEN = Stop("Fifth Ave & Aiken Ave (Shadyside)", 40.4520, -79.9392)
BAKERY_SQUARE = Stop("Bakery Square (Penn Ave)", 40.4633, -79.9214)
PTC_TECH_DR = Stop("PTC (Technology Dr)", 40.4542, -79.9196)
MILL_19 = Stop("Mill 19 (Hazelwood Green)", 40.4288, -79.9465)
MURRAY_FORBES = Stop("Forbes Ave & Murray Ave (Squirrel Hill)", 40.4347, -79.9234)


ROUTES: List[RouteDefinition] = [
    RouteDefinition(
        name="A/B/AB",
        stops=[MOREWOOD_FORBES, FIFTH_AIKEN],
        weekday_headway_min=10,
        weekend_headway_min=15,
        service_span_weekday=(time(7, 0), time(23, 30)),
        service_span_weekend=(time(10, 0), time(23, 30)),
    ),
    RouteDefinition(
        name="C Route",
        stops=[MOREWOOD_FORBES, MURRAY_FORBES],
        weekday_headway_min=20,
        weekend_headway_min=None,  # no weekend service
        service_span_weekday=(time(7, 0), time(19, 30)),
        service_span_weekend=None,
    ),
    RouteDefinition(
        name="PTC & Mill 19",
        stops=[MOREWOOD_FORBES, PTC_TECH_DR, MILL_19],
        weekday_headway_min=30,
        weekend_headway_min=45,
        service_span_weekday=(time(7, 0), time(20, 0)),
        service_span_weekend=(time(10, 0), time(18, 0)),
    ),
    RouteDefinition(
        name="Bakery Square",
        stops=[MOREWOOD_FORBES, BAKERY_SQUARE],
        weekday_headway_min=30,
        weekend_headway_min=None,  # weekday only per typical ops
        service_span_weekday=(time(7, 0), time(19, 30)),
        service_span_weekend=None,
    ),
]


# ------------------------------
# Google helpers (optional)
# ------------------------------

def get_walking_minutes_via_google(
    origin: Tuple[float, float],
    destination: Tuple[float, float],
    api_key: Optional[str],
) -> Optional[int]:
    if not api_key:
        return None
    try:
        googlemaps = importlib.import_module("googlemaps")
        client = googlemaps.Client(key=api_key)
        directions = client.directions(
            origin, destination, mode="walking", departure_time=datetime.now()
        )
        if not directions:
            return None
        leg = directions[0]["legs"][0]
        return int(round(leg["duration"]["value"] / 60))
    except Exception:
        return None


# ------------------------------
# Planning helpers
# ------------------------------

def is_weekend(dt: datetime) -> bool:
    return dt.weekday() >= 5


def minutes_since_midnight(dt: datetime) -> int:
    return dt.hour * 60 + dt.minute


def service_is_active(route: RouteDefinition, dt: datetime) -> bool:
    weekend = is_weekend(dt)
    m = minutes_since_midnight(dt)
    if weekend:
        if not route.service_span_weekend:
            return False
        start, end = route.service_span_weekend
    else:
        start, end = route.service_span_weekday
    start_m = start.hour * 60 + start.minute
    end_m = end.hour * 60 + end.minute
    return start_m <= m <= end_m


def headway_minutes(route: RouteDefinition, dt: datetime) -> Optional[int]:
    if is_weekend(dt):
        return route.weekend_headway_min
    return route.weekday_headway_min


def find_nearest_stop(lat: float, lon: float) -> Tuple[Stop, float]:
    all_stops: List[Stop] = []
    for r in ROUTES:
        all_stops.extend(r.stops)
    # De-duplicate by name while preserving earliest instance
    unique: Dict[str, Stop] = {}
    for s in all_stops:
        if s.name not in unique:
            unique[s.name] = s
    nearest = min(unique.values(), key=lambda s: haversine_miles(lat, lon, s.lat, s.lon))
    dist = haversine_miles(lat, lon, nearest.lat, nearest.lon)
    return nearest, dist


def find_route_connecting(origin_stop: Stop, dest_stop: Stop) -> Optional[RouteDefinition]:
    for route in ROUTES:
        names = [s.name for s in route.stops]
        if origin_stop.name in names and dest_stop.name in names:
            if names.index(origin_stop.name) != names.index(dest_stop.name):
                return route
    return None


def distance_along_route(route: RouteDefinition, a: Stop, b: Stop) -> float:
    names = [s.name for s in route.stops]
    ia, ib = names.index(a.name), names.index(b.name)
    if ia > ib:
        ia, ib = ib, ia
    miles = 0.0
    for i in range(ia, ib):
        s1, s2 = route.stops[i], route.stops[i + 1]
        miles += haversine_miles(s1.lat, s1.lon, s2.lat, s2.lon)
    return miles


def estimate_in_vehicle_minutes(route_miles: float) -> int:
    # Assume 12 mph average including signals; add 1 minute per intermediate stop
    base = (route_miles / 12.0) * 60.0
    return max(3, int(round(base)))


def plan_shuttle_trip(
    origin_coords: Tuple[float, float],
    dest_coords: Tuple[float, float],
    when: datetime,
    google_api_key: Optional[str] = None,
) -> Dict:
    """Return a shuttle plan with walking + shuttle segments.

    Returns a dict with keys: success, reason?, route_name, steps[], totals.
    """
    o_stop, o_stop_dist = find_nearest_stop(origin_coords[0], origin_coords[1])
    d_stop, d_stop_dist = find_nearest_stop(dest_coords[0], dest_coords[1])

    route = find_route_connecting(o_stop, d_stop)
    if not route:
        return {
            "success": False,
            "reason": "No single shuttle route connects the nearest stops",
            "origin_stop": o_stop.name,
            "dest_stop": d_stop.name,
        }

    if not service_is_active(route, when):
        return {
            "success": False,
            "reason": f"{route.name} not operating at selected time",
            "route_name": route.name,
            "origin_stop": o_stop.name,
            "dest_stop": d_stop.name,
        }

    hw = headway_minutes(route, when)
    if hw is None:
        return {
            "success": False,
            "reason": f"{route.name} has no service at this time/day",
            "route_name": route.name,
        }

    # Estimate walking minutes using Google if available, fallback to heuristic
    walk_to_stop_min = get_walking_minutes_via_google(
        origin_coords, (o_stop.lat, o_stop.lon), google_api_key
    )
    if walk_to_stop_min is None:
        walk_to_stop_min = walking_minutes_heuristic(o_stop_dist)

    walk_from_stop_min = get_walking_minutes_via_google(
        (d_stop.lat, d_stop.lon), dest_coords, google_api_key
    )
    if walk_from_stop_min is None:
        walk_from_stop_min = walking_minutes_heuristic(d_stop_dist)

    # Wait time approximation: half headway on average
    wait_min = max(1, hw // 2)

    in_vehicle_miles = distance_along_route(route, o_stop, d_stop)
    in_vehicle_min = estimate_in_vehicle_minutes(in_vehicle_miles)

    total_min = walk_to_stop_min + wait_min + in_vehicle_min + walk_from_stop_min

    # Timestamps (best-effort estimates)
    board_time = when.replace(second=0, microsecond=0) 
    board_time = board_time + (datetime.min - datetime.min)  # no-op to keep type hints happy
    board_time = when
    board_time = board_time + timedelta(minutes=walk_to_stop_min + wait_min)
    arrive_time = board_time + timedelta(minutes=in_vehicle_min + walk_from_stop_min)
    def fmt(dt: datetime) -> str:
        return dt.strftime("%I:%M %p").lstrip('0')

    steps = [
        {
            "type": "WALK",
            "from": "Origin",
            "to": o_stop.name,
            "minutes": walk_to_stop_min,
        },
        {
            "type": "WAIT",
            "at": o_stop.name,
            "route": route.name,
            "minutes": wait_min,
        },
        {
            "type": "SHUTTLE",
            "route": route.name,
            "from": o_stop.name,
            "to": d_stop.name,
            "minutes": in_vehicle_min,
            "miles": round(in_vehicle_miles, 2),
        },
        {
            "type": "WALK",
            "from": d_stop.name,
            "to": "Destination",
            "minutes": walk_from_stop_min,
        },
    ]

    return {
        "success": True,
        "route_name": route.name,
        "origin_stop": o_stop.name,
        "dest_stop": d_stop.name,
        "steps": steps,
        "totals": {
            "minutes": total_min,
            "walk_minutes": walk_to_stop_min + walk_from_stop_min,
            "wait_minutes": wait_min,
            "in_vehicle_minutes": in_vehicle_min,
        },
        "times": {
            "board_time": fmt(board_time),
            "arrival_time": fmt(arrive_time),
        },
    }


