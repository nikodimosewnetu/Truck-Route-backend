from django.urls import path
from . import views

urlpatterns = [
    path('calculate-route', views.RouteCalculatorView.as_view(), name='calculate_route'),
    path('geocode', views.GeocodeView.as_view(), name='geocode'),
    path('location-suggestions', views.LocationSuggestionsView.as_view(), name='location_suggestions'),
]
