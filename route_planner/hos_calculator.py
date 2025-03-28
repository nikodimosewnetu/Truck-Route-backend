"""
HOS (Hours of Service) Calculator module

This module implements the HOS regulations for property-carrying drivers:
- 11-hour driving limit after 10 consecutive hours off duty
- 14-hour "driving window" limit
- 30-minute break after 8 hours of driving
- 70-hour/8-day limit
"""

import datetime
import math
from copy import deepcopy


class HOSCalculator:
    """Calculator for HOS-compliant schedules"""
    
    # HOS constants for property-carrying drivers
    MAX_DRIVING_HOURS = 11  # Maximum driving hours after 10-hour break
    MAX_DUTY_WINDOW = 14    # Maximum duty window after 10-hour break
    MAX_DRIVING_WITHOUT_BREAK = 8  # Maximum driving before 30-min break
    MIN_BREAK_DURATION = 0.5  # 30-minute break duration in hours
    MIN_REST_DURATION = 10  # Minimum off-duty period to reset duty window
    PICKUP_DROPOFF_DURATION = 1  # 1 hour for pickup/dropoff activities
    
    # 70-hour/8-day rule constants
    MAX_CYCLE_HOURS = 70  # Maximum on-duty hours in 8-day period
    
    # Average truck speed in mph for estimation
    AVG_TRUCK_SPEED = 55
    
    # Fueling constants
    FUELING_INTERVAL_MILES = 1000  # Fuel every 1000 miles
    FUELING_DURATION = 0.5  # 30 minutes for fueling
    
    def __init__(self, current_cycle_hours=0):
        """Initialize calculator with current cycle hours used"""
        self.current_cycle_hours = current_cycle_hours
        self.current_driving_hours = 0
        self.current_window_hours = 0
        self.current_driving_without_break = 0
    
    def calculate_schedule(self, route_data):
        """
        Calculate an HOS-compliant schedule for the given route
        
        Args:
            route_data: Dictionary containing route information
                - segments: List of route segments with distance and duration
                - total_distance: Total route distance in miles
                - total_duration: Total route duration in hours
                
        Returns:
            Dictionary with schedule information including stops and segments
        """
        # Deep copy to avoid modifying original
        result = deepcopy(route_data)
        
        # Initialize schedule
        start_time = datetime.datetime.now().replace(
            minute=0, second=0, microsecond=0
        )
        current_time = start_time
        available_driving_hours = self.MAX_DRIVING_HOURS
        available_window_hours = self.MAX_DUTY_WINDOW
        hours_since_break = 0
        
        stops = []
        modified_segments = []
        remaining_cycle_hours = self.MAX_CYCLE_HOURS - self.current_cycle_hours
        
        # Add starting point
        stops.append({
            'location': route_data['locations'][0],
            'arrival_time': current_time,
            'departure_time': current_time,
            'stop_type': 'start',
            'duration': 0
        })
        
        # Process each segment
        accumulated_distance = 0
        last_fuel_distance = 0
        segment_index = 0
        total_segments = len(route_data['segments'])
        
        while segment_index < total_segments:
            segment = route_data['segments'][segment_index]
            remaining_segment = deepcopy(segment)
            segment_processed = False
            
            # Check if this is a pickup or dropoff point
            if segment_index == 0:  # First segment ends at pickup
                current_location = route_data['locations'][0]
                next_location = route_data['locations'][1]
                is_pickup = True
                is_dropoff = False
            elif segment_index == total_segments - 1:  # Last segment ends at dropoff
                current_location = route_data['locations'][1]
                next_location = route_data['locations'][2]
                is_pickup = False
                is_dropoff = True
            else:
                is_pickup = False
                is_dropoff = False
                current_location = segment['start_location']
                next_location = segment['end_location']
            
            # Process segment with HOS compliance
            while not segment_processed:
                # Check if we need a mandatory break due to 8-hour rule
                if hours_since_break >= self.MAX_DRIVING_WITHOUT_BREAK:
                    # Add a 30-minute break
                    stops.append({
                        'location': current_location,
                        'arrival_time': current_time,
                        'departure_time': current_time + datetime.timedelta(hours=self.MIN_BREAK_DURATION),
                        'stop_type': 'break',
                        'duration': self.MIN_BREAK_DURATION
                    })
                    
                    current_time += datetime.timedelta(hours=self.MIN_BREAK_DURATION)
                    hours_since_break = 0
                    available_window_hours -= self.MIN_BREAK_DURATION
                
                # Check if we need a fueling stop
                distance_since_last_fuel = accumulated_distance - last_fuel_distance
                if distance_since_last_fuel >= self.FUELING_INTERVAL_MILES:
                    stops.append({
                        'location': current_location,
                        'arrival_time': current_time,
                        'departure_time': current_time + datetime.timedelta(hours=self.FUELING_DURATION),
                        'stop_type': 'fuel',
                        'duration': self.FUELING_DURATION
                    })
                    
                    current_time += datetime.timedelta(hours=self.FUELING_DURATION)
                    available_window_hours -= self.FUELING_DURATION
                    last_fuel_distance = accumulated_distance
                
                # Handle pickup/dropoff activities
                if is_pickup:
                    stops.append({
                        'location': next_location,
                        'arrival_time': current_time,
                        'departure_time': current_time + datetime.timedelta(hours=self.PICKUP_DROPOFF_DURATION),
                        'stop_type': 'pickup',
                        'duration': self.PICKUP_DROPOFF_DURATION
                    })
                    
                    current_time += datetime.timedelta(hours=self.PICKUP_DROPOFF_DURATION)
                    available_window_hours -= self.PICKUP_DROPOFF_DURATION
                    remaining_cycle_hours -= self.PICKUP_DROPOFF_DURATION
                    is_pickup = False
                
                if is_dropoff:
                    stops.append({
                        'location': next_location,
                        'arrival_time': current_time,
                        'departure_time': current_time + datetime.timedelta(hours=self.PICKUP_DROPOFF_DURATION),
                        'stop_type': 'dropoff',
                        'duration': self.PICKUP_DROPOFF_DURATION
                    })
                    
                    current_time += datetime.timedelta(hours=self.PICKUP_DROPOFF_DURATION)
                    available_window_hours -= self.PICKUP_DROPOFF_DURATION
                    remaining_cycle_hours -= self.PICKUP_DROPOFF_DURATION
                    is_dropoff = False
                
                # Determine how much of the segment we can drive
                max_driving_time = min(
                    available_driving_hours,
                    available_window_hours,
                    remaining_segment['duration'],
                    self.MAX_DRIVING_WITHOUT_BREAK - hours_since_break,
                    remaining_cycle_hours
                )
                
                if max_driving_time <= 0:
                    # Need to take a rest period
                    stops.append({
                        'location': current_location,
                        'arrival_time': current_time,
                        'departure_time': current_time + datetime.timedelta(hours=self.MIN_REST_DURATION),
                        'stop_type': 'rest',
                        'duration': self.MIN_REST_DURATION
                    })
                    
                    current_time += datetime.timedelta(hours=self.MIN_REST_DURATION)
                    available_driving_hours = self.MAX_DRIVING_HOURS
                    available_window_hours = self.MAX_DUTY_WINDOW
                    hours_since_break = 0
                    
                    # No segment processed in this iteration
                    continue
                
                # Calculate how much distance we can cover
                segment_progress = max_driving_time / remaining_segment['duration']
                distance_covered = remaining_segment['distance'] * segment_progress
                
                # Update our position
                accumulated_distance += distance_covered
                
                # Create a partial segment if needed
                if segment_progress < 1:
                    # We're splitting the segment
                    partial_segment = {
                        'start_location': current_location,
                        'end_location': {
                            'address': f"Intermediate point {segment_index}",
                            'lat': (current_location['lat'] + next_location['lat']) / 2,
                            'lng': (current_location['lng'] + next_location['lng']) / 2
                        },
                        'distance': distance_covered,
                        'duration': max_driving_time,
                        'start_time': current_time,
                        'end_time': current_time + datetime.timedelta(hours=max_driving_time)
                    }
                    
                    modified_segments.append(partial_segment)
                    
                    # Update current location
                    current_location = partial_segment['end_location']
                    
                    # Update remaining segment
                    remaining_segment['distance'] -= distance_covered
                    remaining_segment['duration'] -= max_driving_time
                    
                    # Update times
                    current_time += datetime.timedelta(hours=max_driving_time)
                    available_driving_hours -= max_driving_time
                    available_window_hours -= max_driving_time
                    hours_since_break += max_driving_time
                    remaining_cycle_hours -= max_driving_time
                else:
                    # We completed the segment
                    complete_segment = {
                        'start_location': current_location,
                        'end_location': next_location,
                        'distance': remaining_segment['distance'],
                        'duration': remaining_segment['duration'],
                        'start_time': current_time,
                        'end_time': current_time + datetime.timedelta(hours=remaining_segment['duration'])
                    }
                    
                    modified_segments.append(complete_segment)
                    
                    # Update times
                    current_time += datetime.timedelta(hours=remaining_segment['duration'])
                    available_driving_hours -= remaining_segment['duration']
                    available_window_hours -= remaining_segment['duration']
                    hours_since_break += remaining_segment['duration']
                    remaining_cycle_hours -= remaining_segment['duration']
                    
                    # Mark segment as processed
                    segment_processed = True
                    segment_index += 1
            
        # Add final stop
        final_location = route_data['locations'][-1]
        stops.append({
            'location': final_location,
            'arrival_time': current_time,
            'departure_time': current_time,
            'stop_type': 'end',
            'duration': 0
        })
        
        # Update result
        result['stops'] = stops
        result['segments'] = modified_segments
        result['start_time'] = start_time
        result['end_time'] = current_time
        
        return result


def calculate_hos_compliant_schedule(route_data, current_cycle_hours=0):
    """
    Calculate an HOS-compliant schedule for the given route
    
    Args:
        route_data: Dictionary containing route information
        current_cycle_hours: Current hours used in the 70-hour/8-day cycle
        
    Returns:
        Dictionary with schedule information
    """
    calculator = HOSCalculator(current_cycle_hours)
    return calculator.calculate_schedule(route_data)
