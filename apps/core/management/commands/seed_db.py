import os
from django.core.management.base import BaseCommand
from django.core.management import call_command

class Command(BaseCommand):
    help = "Seeds initial dough categories, form factors, presets, and default system settings using fixtures."

    def handle(self, *args, **options):
        self.stdout.write("Seeding database from fixtures...")
        
        # Determine the path to the fixture
        fixture_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "fixtures",
            "seed_data.json"
        )
        
        if not os.path.exists(fixture_path):
            self.stdout.write(self.style.ERROR(f"Fixture not found at {fixture_path}"))
            return

        # Load the fixture data
        call_command("loaddata", fixture_path)
        
        self.stdout.write(self.style.SUCCESS("Database seeded successfully!"))
