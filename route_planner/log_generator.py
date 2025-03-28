"""
Log Generator module

This module is responsible for generating ELD log sheets based on
the calculated HOS-compliant schedule.
"""

import datetime
from copy import deepcopy


def generate_log_sheets(schedule_data):
    """
    Generate ELD log sheets based on the schedule
    
    Args:
        schedule_data: Dictionary with schedule information
        
    Returns:
        List of log sheet entries
    """
    logs = []
    
    # Process each day of the trip
    current_date = schedule_data['start_time'].date()
    end_date = schedule_data['end_time'].date()
    
    # Add a day to end_date if there is activity in the current day
    if schedule_data['end_time'].time() > datetime.time(0, 0):
        end_date += datetime.timedelta(days=1)
    
    while current_date <= end_date:
        # Initialize log entry for this day
        log_entry = {
            'date': current_date,
            'off_duty': [],
            'sleeper_berth': [],
            'driving': [],
            'on_duty': [],
            'total_miles': 0,
            'carrier': 'Sample Carrier',  # Default values
            'main_office': 'Main Office Address',
            'home_terminal': 'Home Terminal Address',
            'shipping_docs': 'N/A',  # Default value for empty shipping docs
            'remarks': 'No remarks'  # Default value for empty remarks
        }
        
        # Filter schedule items for this day
        day_start = datetime.datetime.combine(current_date, datetime.time(0, 0))
        day_end = day_start + datetime.timedelta(days=1)
        
        # Process stops for this day
        for stop in schedule_data['stops']:
            # Skip stops outside of this day
            if stop['arrival_time'] >= day_end or stop['departure_time'] < day_start:
                continue
            
            # Add stop activities to log
            if stop['stop_type'] == 'rest':
                add_activity_to_log(log_entry, 'off_duty', stop['arrival_time'], stop['departure_time'], day_start)
            elif stop['stop_type'] == 'break':
                add_activity_to_log(log_entry, 'off_duty', stop['arrival_time'], stop['departure_time'], day_start)
            elif stop['stop_type'] in ['pickup', 'dropoff', 'fuel']:
                add_activity_to_log(log_entry, 'on_duty', stop['arrival_time'], stop['departure_time'], day_start)
        
        # Process segments for this day
        for segment in schedule_data['segments']:
            # Skip segments outside of this day
            if segment['start_time'] >= day_end or segment['end_time'] < day_start:
                continue
            
            # Add driving activity to log
            add_activity_to_log(log_entry, 'driving', segment['start_time'], segment['end_time'], day_start)
            
            # Calculate miles driven on this day
            segment_start = max(segment['start_time'], day_start)
            segment_end = min(segment['end_time'], day_end)
            
            # Calculate proportion of segment that falls on this day
            if segment['end_time'] > segment['start_time']:
                segment_day_proportion = (segment_end - segment_start).total_seconds() / (segment['end_time'] - segment['start_time']).total_seconds()
                log_entry['total_miles'] += segment['distance'] * segment_day_proportion
        
        # Add remarks about the day's activities
        remarks = []
        for stop in schedule_data['stops']:
            if stop['arrival_time'].date() == current_date:
                if stop['stop_type'] == 'pickup':
                    remarks.append(f"Pickup at {stop['location']['address']} at {stop['arrival_time'].strftime('%H:%M')}")
                elif stop['stop_type'] == 'dropoff':
                    remarks.append(f"Dropoff at {stop['location']['address']} at {stop['arrival_time'].strftime('%H:%M')}")
                elif stop['stop_type'] == 'fuel':
                    remarks.append(f"Fueling at {stop['arrival_time'].strftime('%H:%M')}")
        
        if remarks:
            log_entry['remarks'] = '. '.join(remarks)
        
        # Add shipping document numbers
        shipping_docs = []
        for stop in schedule_data['stops']:
            if stop['stop_type'] == 'pickup' and stop['arrival_time'].date() <= current_date <= stop['departure_time'].date():
                shipping_docs.append(f"PU{current_date.strftime('%Y%m%d')}")
            elif stop['stop_type'] == 'dropoff' and stop['arrival_time'].date() <= current_date <= stop['departure_time'].date():
                shipping_docs.append(f"DO{current_date.strftime('%Y%m%d')}")
        
        if shipping_docs:
            log_entry['shipping_docs'] = ', '.join(shipping_docs)
        
        # Round total miles to nearest mile
        log_entry['total_miles'] = round(log_entry['total_miles'])
        
        # Add log entry for this day
        logs.append(log_entry)
        
        # Move to next day
        current_date += datetime.timedelta(days=1)
    
    return logs


def add_activity_to_log(log_entry, activity_type, start_time, end_time, day_start):
    """
    Add an activity period to the log entry
    
    Args:
        log_entry: Dictionary with log entry data
        activity_type: String type of activity ('off_duty', 'sleeper_berth', 'driving', 'on_duty')
        start_time: Datetime of activity start
        end_time: Datetime of activity end
        day_start: Datetime representing start of the day
        
    Returns:
        None (modifies log_entry in place)
    """
    # Adjust times to be within the current day
    day_end = day_start + datetime.timedelta(days=1)
    activity_start = max(start_time, day_start)
    activity_end = min(end_time, day_end)
    
    # Skip if activity doesn't fall in this day
    if activity_start >= day_end or activity_end <= day_start:
        return
    
    # Convert to hour fractions (0-24)
    start_hour = (activity_start - day_start).total_seconds() / 3600
    end_hour = (activity_end - day_start).total_seconds() / 3600
    
    # Add to appropriate activity list
    log_entry[activity_type].append([start_hour, end_hour])
