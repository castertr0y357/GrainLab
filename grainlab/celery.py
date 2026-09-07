import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "grainlab.settings")

app = Celery("grainlab")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

app.conf.beat_schedule = {
    "check-backups-hourly": {
        "task": "apps.core.tasks.backups.scheduled_backup_check",
        "schedule": crontab(minute=0),  # Top of every hour
    },
    "prune-soft-deleted-records-daily": {
        "task": "apps.core.tasks.maintenance.prune_soft_deleted_records",
        "schedule": crontab(hour=3, minute=0),  # Run daily at 3:00 AM
    },
}
