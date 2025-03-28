"""
URL configuration for trucking_app project.
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.shortcuts import redirect
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse
import os

# View to serve frontend files
def serve_frontend_file(request, path):
    # Map the path to the actual frontend directory
    frontend_dir = os.path.join(settings.BASE_DIR.parent, 'frontend')
    file_path = os.path.join(frontend_dir, path)
    
    # If the path doesn't exist, default to index.html
    if not os.path.exists(file_path) or os.path.isdir(file_path):
        file_path = os.path.join(frontend_dir, 'index.html')
    
    # Determine content type based on file extension
    content_type = 'text/html'
    if file_path.endswith('.js'):
        content_type = 'application/javascript'
    elif file_path.endswith('.css'):
        content_type = 'text/css'
    elif file_path.endswith('.png'):
        content_type = 'image/png'
    elif file_path.endswith('.jpg') or file_path.endswith('.jpeg'):
        content_type = 'image/jpeg'
    
    # Read the file and return its contents
    with open(file_path, 'rb') as f:
        file_content = f.read()
    
    return HttpResponse(file_content, content_type=content_type)

# Redirect the root path to the frontend
def redirect_to_frontend(request):
    return redirect('/app/')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('route_planner.urls')),
    
    # Serve frontend files
    path('app/<path:path>', serve_frontend_file),
    path('app/', serve_frontend_file, {'path': 'index.html'}),
    
    # Redirect root to frontend
    path('', redirect_to_frontend),
]
