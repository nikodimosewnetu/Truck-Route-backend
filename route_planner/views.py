from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import datetime
import requests
import json

from .serializers import TripRequestSerializer, RouteResponseSerializer
from .route_calculator import calculate_route
from .hos_calculator import calculate_hos_compliant_schedule
from .log_generator import generate_log_sheets


class RouteCalculatorView(APIView):
    """API view for calculating routes with HOS compliance"""

    def post(self, request):
        """Process route calculation request"""
        serializer = TripRequestSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Extract validated data
        current_location = serializer.validated_data['current_location']
        pickup_location = serializer.validated_data['pickup_location']
        dropoff_location = serializer.validated_data['dropoff_location']
        current_cycle_hours = serializer.validated_data['current_cycle_hours']
        
        try:
            # Step 1: Calculate basic route information
            route_data = calculate_route(
                current_location, 
                pickup_location,
                dropoff_location
            )
            
            # Step 2: Calculate HOS-compliant schedule with rest stops
            schedule_data = calculate_hos_compliant_schedule(
                route_data,
                current_cycle_hours
            )
            
            # Step 3: Generate log sheets based on the schedule
            log_sheets = generate_log_sheets(schedule_data)
            
            # Combine all data for response
            response_data = {
                'total_distance': schedule_data['total_distance'],
                'total_duration': schedule_data['total_duration'],
                'estimated_start_time': schedule_data['start_time'],
                'estimated_delivery_time': schedule_data['end_time'],
                'stops': schedule_data['stops'],
                'segments': schedule_data['segments'],
                'logs': log_sheets,
                'polyline': route_data['polyline']
            }
            
            # Validate response data
            response_serializer = RouteResponseSerializer(data=response_data)
            if response_serializer.is_valid():
                return Response(response_serializer.validated_data)
            else:
                return Response(response_serializer.errors, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GeocodeView(APIView):
    """API view for geocoding addresses"""
    
    def get(self, request):
        """Geocode an address to coordinates"""
        address = request.query_params.get('address')
        
        if not address:
            return Response(
                {'error': 'Address parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
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
                return Response(
                    {'error': 'Location not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
                
            result = {
                'address': address,
                'lat': float(data[0]['lat']),
                'lng': float(data[0]['lon']),
                'display_name': data[0]['display_name']
            }
            
            return Response(result)
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class LocationSuggestionsView(APIView):
    """API view for getting location suggestions"""
    
    def get(self, request):
        """Get suggestions for location input"""
        query = request.query_params.get('query')
        
        if not query or len(query) < 3:
            return Response([])
        
        try:
            # Use OpenStreetMap Nominatim API for location suggestions
            response = requests.get(
                'https://nominatim.openstreetmap.org/search',
                params={
                    'q': query,
                    'format': 'json',
                    'limit': 5  # Return top 5 suggestions
                },
                headers={'User-Agent': 'TruckingRouteApp/1.0'}
            )
            
            data = response.json()
            
            # Format suggestions for frontend
            suggestions = []
            for item in data:
                suggestions.append({
                    'display_name': item['display_name'],
                    'lat': float(item['lat']),
                    'lng': float(item['lon'])
                })
                
            return Response(suggestions)
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
