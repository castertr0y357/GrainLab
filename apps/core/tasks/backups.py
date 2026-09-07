import datetime
import glob
import os
import subprocess

from celery import shared_task
from django.conf import settings
from django.core.cache import cache

from apps.core.models.system import SystemSetting

BACKUP_DIR = os.path.join(settings.BASE_DIR, "backups")


def get_db_env():
    """Returns environment variables dictionary for pg commands."""
    db = settings.DATABASES["default"]
    env = os.environ.copy()
    if db.get("PASSWORD"):
        env["PGPASSWORD"] = str(db["PASSWORD"])
    return env, db


@shared_task
def create_backup():
    """Creates a pg_dump backup and saves it to the backups directory."""
    os.makedirs(BACKUP_DIR, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"grainlab_backup_{timestamp}.sql.gz"
    filepath = os.path.join(BACKUP_DIR, filename)

    env, db = get_db_env()
    host = db.get("HOST", "localhost")
    port = db.get("PORT", "5432")
    user = db.get("USER", "postgres")
    name = db.get("NAME", "postgres")

    command = f"pg_dump -h {host} -p {port} -U {user} -d {name} --clean --if-exists --no-owner --no-privileges | gzip > '{filepath}'"
    result = subprocess.run(command, shell=True, capture_output=True, text=True, env=env)

    if result.returncode != 0:
        raise Exception(f"Backup failed: {result.stderr}")

    # Automatically prune old backups after creating a new one
    prune_backups()

    return f"Created backup: {filename}"


@shared_task
def restore_backup(filename: str):
    """Restores a backup and wipes the existing database."""
    filepath = os.path.join(BACKUP_DIR, filename)
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Backup file not found: {filename}")

    env, db = get_db_env()
    host = db.get("HOST", "localhost")
    port = db.get("PORT", "5432")
    user = db.get("USER", "postgres")
    name = db.get("NAME", "postgres")

    # Set maintenance mode flag
    cache.set("MAINTENANCE_MODE", True, timeout=None)

    try:
        # We can restore by piping zcat/gunzip to psql.
        command = f"zcat '{filepath}' | psql -h {host} -p {port} -U {user} -d {name}"
        result = subprocess.run(command, shell=True, capture_output=True, text=True, env=env)

        if result.returncode != 0:
            raise Exception(f"Restore failed: {result.stderr}")
    finally:
        # ALWAYS release the maintenance lock
        cache.delete("MAINTENANCE_MODE")

    return f"Restored backup: {filename}"


@shared_task
def prune_backups():
    """Deletes oldest backups if we exceed the retention limit."""
    retention_count = int(SystemSetting.get_val("backup_retention", default="14"))

    # If 0, we don't prune
    if retention_count == 0:
        return

    os.makedirs(BACKUP_DIR, exist_ok=True)
    backups = glob.glob(os.path.join(BACKUP_DIR, "grainlab_backup_*.sql.gz"))
    backups.sort(key=os.path.getctime)

    # If we have more backups than retention limit, delete the oldest
    while len(backups) > retention_count:
        oldest = backups.pop(0)
        os.remove(oldest)


@shared_task
def scheduled_backup_check():
    """
    Runs every hour (via Celery beat).
    Checks the SystemSetting 'backup_schedule' to see if we should run a backup.
    """
    schedule = SystemSetting.get_val("backup_schedule", default="disabled")

    if schedule == "disabled":
        return

    # Get last backup time
    os.makedirs(BACKUP_DIR, exist_ok=True)
    backups = glob.glob(os.path.join(BACKUP_DIR, "grainlab_backup_*.sql.gz"))
    backups.sort(key=os.path.getctime)

    now = datetime.datetime.now()

    if not backups:
        # No backups exist, trigger one immediately
        create_backup.delay()
        return

    latest_backup_time = datetime.datetime.fromtimestamp(os.path.getctime(backups[-1]))
    hours_since_last = (now - latest_backup_time).total_seconds() / 3600

    if schedule == "daily" and hours_since_last >= 24 or schedule == "weekly" and hours_since_last >= 168:
        create_backup.delay()
