#!/usr/bin/env python
import os
import sys

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'alx_travel_app.alx_travel_app.settings')

try:
    # Try to import Django
    import django
    print("Django imported successfully")
    
    # Try Django setup
    django.setup()
    print("Django setup successful")
    
    # Try to import the listings app
    from alx_travel_app.alx_travel_app.listings import apps
    print("Listings app imported successfully")
    
    # Try Django management commands
    from django.core.management import execute_from_command_line
    print("Django management imported successfully")
    
    # Run the check command
    execute_from_command_line(['manage.py', 'check'])
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
