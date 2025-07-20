# listings/management/commands/seed.py

from django.core.management.base import BaseCommand
from alx_travel_app.alx_travel_app.listings.models import Listing
import random

class Command(BaseCommand):
    help = 'Seed database with sample listings'

    def handle(self, *args, **kwargs):
        for i in range(10):
            Listing.objects.create(
                title=f"Sample Listing {i+1}",
                description="A beautiful place to stay.",
                price_per_night=random.randint(50, 500),
                location="Sample Location"
            )
        self.stdout.write(self.style.SUCCESS('Successfully seeded database with sample listings.'))
