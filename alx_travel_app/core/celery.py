import os
from alx_travel_app.alx_travel_app.alx_travel_app.celery import Celery

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'alx_travel_app.core.settings')

# Create the Celery app
app = Celery('alx_travel_app')

# Load settings from Django settings using namespace 'CELERY'
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks in all registered Django apps
app.autodiscover_tasks()
