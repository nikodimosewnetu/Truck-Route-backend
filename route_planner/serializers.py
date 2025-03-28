from rest_framework import serializers


class LocationSerializer(serializers.Serializer):
    """Serializer for location data"""
    address = serializers.CharField(max_length=255)
    lat = serializers.FloatField(required=False)
    lng = serializers.FloatField(required=False)


class TripRequestSerializer(serializers.Serializer):
    """Serializer for trip request data"""
    current_location = serializers.CharField(max_length=255)
    pickup_location = serializers.CharField(max_length=255)
    dropoff_location = serializers.CharField(max_length=255)
    current_cycle_hours = serializers.FloatField(min_value=0, max_value=70)


class RouteStopSerializer(serializers.Serializer):
    """Serializer for individual stops along the route"""
    location = LocationSerializer()
    arrival_time = serializers.DateTimeField()
    departure_time = serializers.DateTimeField()
    stop_type = serializers.CharField(max_length=50)  # e.g., 'rest', 'pickup', 'dropoff', 'fuel'
    duration = serializers.FloatField()  # in hours


class RouteSegmentSerializer(serializers.Serializer):
    """Serializer for route segments between stops"""
    start_location = LocationSerializer()
    end_location = LocationSerializer()
    distance = serializers.FloatField()  # in miles
    duration = serializers.FloatField()  # in hours
    start_time = serializers.DateTimeField()
    end_time = serializers.DateTimeField()


class LogEntrySerializer(serializers.Serializer):
    """Serializer for log entries (for drawing ELD logs)"""
    date = serializers.DateField()
    off_duty = serializers.ListField(child=serializers.ListField(child=serializers.FloatField()))
    sleeper_berth = serializers.ListField(child=serializers.ListField(child=serializers.FloatField()))
    driving = serializers.ListField(child=serializers.ListField(child=serializers.FloatField()))
    on_duty = serializers.ListField(child=serializers.ListField(child=serializers.FloatField()))
    total_miles = serializers.FloatField()
    carrier = serializers.CharField(max_length=255, required=False)
    main_office = serializers.CharField(max_length=255, required=False)
    home_terminal = serializers.CharField(max_length=255, required=False)
    shipping_docs = serializers.CharField(max_length=255, required=False)
    remarks = serializers.CharField(max_length=1000, required=False)


class RouteResponseSerializer(serializers.Serializer):
    """Serializer for the complete route response"""
    total_distance = serializers.FloatField()
    total_duration = serializers.FloatField()
    estimated_start_time = serializers.DateTimeField()
    estimated_delivery_time = serializers.DateTimeField()
    stops = RouteStopSerializer(many=True)
    segments = RouteSegmentSerializer(many=True)
    logs = LogEntrySerializer(many=True)
    polyline = serializers.CharField()  # encoded polyline for map display
