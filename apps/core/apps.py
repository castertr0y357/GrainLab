import logging
import sys
import time

from django.apps import AppConfig
from django.db import connections
from django.db.utils import OperationalError, ProgrammingError

logger = logging.getLogger("grainlab.startup")


def auto_seed_db(sender, **kwargs):
    import os
    import sys

    if "test" in sys.argv:
        return
        
    if os.environ.get("AUTO_SEED_DB", "False").lower() not in ("true", "1", "t"):
        return

    from django.core.management import call_command

    from apps.core.models import DoughCategory

    try:
        if not DoughCategory.objects.exists():
            logger.info("[Startup] - Database - No dough categories found. Seeding database...")
            call_command("seed_db")
    except (OperationalError, ProgrammingError) as e:
        logger.info(f"[Startup] - Database - Seeding skipped (tables not created yet): {e}")
    except Exception as e:
        logger.error(f"[Startup] - Database - Seeding failed: {e}")


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.core"

    def ready(self):
        # Register post-migrate signal for automatic database seeding
        from django.db.models.signals import post_migrate

        post_migrate.connect(auto_seed_db, sender=self)

        # Skip commands that don't need runtime DB connection checks
        skip_commands = {"makemigrations", "migrate", "collectstatic", "showmigrations", "clean", "doctor"}
        if any(arg in skip_commands for arg in sys.argv):
            return

        # 1. Startup Config Validation
        from django.conf import settings

        secret_key = getattr(settings, "SECRET_KEY", None)
        if not secret_key or secret_key.startswith("django-insecure-placeholder"):
            logger.error("[Startup] - Config - SECRET_KEY is missing or set to placeholder.")
            if not secret_key:
                sys.exit("[Startup] - Config - Critical Error: SECRET_KEY is not set.")

        # 2. Pre-flight connection check & Self-healing connection
        db_conn = connections["default"]
        max_retries = 5
        retry_delay = 1.0
        connected = False
        for attempt in range(1, max_retries + 1):
            try:
                db_conn.ensure_connection()
                connected = True
                break
            except Exception as e:
                logger.warning(
                    f"[Startup] - Database - Connection failed, retrying in {retry_delay}s (Attempt {attempt}/{max_retries}): {e}"
                )
                time.sleep(retry_delay)
                retry_delay *= 2.0  # Exponential backoff

        if not connected:
            logger.critical("[Startup] - Database - Max retries exceeded. Database connection failed.")
            sys.exit("[Startup] - Database - Critical Error: Database connection failed.")
