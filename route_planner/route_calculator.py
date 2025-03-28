"""
Route Calculator module

This module is responsible for calculating routes between locations
using external mapping APIs.
"""

import requests
import polyline
import datetime
from urllib.parse import quote


def geocode_address(address):
    """
    Convert address to coordinates using Nominatim
    
    Args:
        address: String address to geocode
        
    Returns:
        Dictionary with lat and lng
    """
    # Use OpenStreetMap Nominatim API for geocoding (free)
    response = requests.get(
        'https://nominatim.openstreetmap.org/search',
        params={
            'q': address,
            'format': 'json',
            'limit': 1
        },
        headers={'User-Agent': 'TruckingRouteApp/1.0'}
    )
    
    data = response.json()
    
    if not data:
        raise ValueError(f"Location not found: {address}")
        
    return {
        'address': address,
        'lat': float(data[0]['lat']),
        'lng': float(data[0]['lon']),
        'display_name': data[0]['display_name']
    }


def calculate_route(current_location, pickup_location, dropoff_location):
    """
    Calculate route between locations
    
    Args:
        current_location: String address of starting point
        pickup_location: String address of pickup location
        dropoff_location: String address of dropoff location
        
    Returns:
        Dictionary with route information
    """
    # Step 1: Geocode all locations
    try:
        current_loc = geocode_address(current_location)
        pickup_loc = geocode_address(pickup_location)
        dropoff_loc = geocode_address(dropoff_location)
    except Exception as e:
        raise ValueError(f"Failed to geocode one or more locations: {str(e)}")
    
    # Step 2: Calculate route from current to pickup
    first_leg = calculate_route_segment(current_loc, pickup_loc)
    
    # Step 3: Calculate route from pickup to dropoff
    second_leg = calculate_route_segment(pickup_loc, dropoff_loc)
    
    # Combine results
    result = {
        'locations': [current_loc, pickup_loc, dropoff_loc],
        'segments': [first_leg, second_leg],
        'total_distance': first_leg['distance'] + second_leg['distance'],
        'total_duration': first_leg['duration'] + second_leg['duration'],
        'polyline': first_leg['polyline'] + second_leg['polyline']
    }
    
    return result


def calculate_route_segment(origin, destination):
    """
    Calculate route between two points
    
    Args:
        origin: Dictionary with lat and lng of starting point
        destination: Dictionary with lat and lng of ending point
        
    Returns:
        Dictionary with segment information
    """
    # Use OSRM API (Open Source Routing Machine) - free and open source
    # This is a public instance - for production, consider hosting your own
    url = (
        f"http://router.project-osrm.org/route/v1/driving/"
        f"{origin['lng']},{origin['lat']};"
        f"{destination['lng']},{destination['lat']}"
        f"?overview=full&alternatives=false&steps=true"
    )
    
    response = requests.get(url)
    
    if response.status_code != 200:
        raise ValueError(f"Route calculation failed: {response.text}")
    
    data = response.json()
    
    if data['code'] != 'Ok':
        raise ValueError(f"Route calculation failed: {data['message']}")
    
    route = data['routes'][0]
    
    # Convert distance to miles and duration to hours
    distance_miles = route['distance'] * 0.000621371  # meters to miles
    duration_hours = route['duration'] / 3600  # seconds to hours
    
    # Get encoded polyline
    encoded_polyline = route['geometry']
    
    # Create segment
    segment = {
        'start_location': origin,
        'end_location': destination,
        'distance': distance_miles,
        'duration': duration_hours,
        'polyline': encoded_polyline
    }
    
    return segment
