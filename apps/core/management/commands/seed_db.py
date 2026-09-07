import os

from django.core.management import call_command
from django.core.management.base import BaseCommand

from apps.core.models import DoughCategory


class Command(BaseCommand):
    help = "Seeds initial dough categories, form factors, presets, and default system settings using fixtures. Also ensures superuser exists."

    def handle(self, *args, **options):
        # Always ensure superuser exists
        from django.contrib.auth import get_user_model

        User = get_user_model()

        su_username = os.getenv("SUPERUSER_USERNAME")
        su_email = os.getenv("SUPERUSER_EMAIL", "")
        su_password = os.getenv("SUPERUSER_PASSWORD")

        if su_username and su_password:
            user, created = User.objects.get_or_create(
                username=su_username, defaults={"email": su_email, "is_superuser": True, "is_staff": True}
            )
            if created:
                user.set_password(su_password)
                user.save()
                self.stdout.write(self.style.SUCCESS(f"Created superuser: {su_username}"))
            else:
                user.set_password(su_password)
                user.is_superuser = True
                user.is_staff = True
                user.save()
                self.stdout.write(self.style.SUCCESS(f"Updated superuser password for: {su_username}"))
        else:
            self.stdout.write(
                self.style.WARNING(
                    "SUPERUSER_USERNAME or SUPERUSER_PASSWORD not set in environment. Skipping superuser creation."
                )
            )

        if DoughCategory.objects.exists():
            self.stdout.write(self.style.SUCCESS("Database already contains data, skipping seed."))
            return

        self.stdout.write("Seeding database from fixtures...")

        # Determine the path to the fixture
        fixture_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "fixtures", "seed_data.json"
        )

        if not os.path.exists(fixture_path):
            self.stdout.write(self.style.ERROR(f"Fixture not found at {fixture_path}"))
            return

        # Load the fixture data
        try:
            call_command("loaddata", fixture_path)
            self.stdout.write(self.style.SUCCESS("Database seeded successfully!"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error seeding database: {e}"))
