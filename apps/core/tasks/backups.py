import logging
import threading
import time
from typing import Callable, Any
from celery import shared_task
from django.conf import settings
from django.db import connection, transaction
from apps.core.models.backup import BackupConfiguration, BackupRecord
from apps.core.models.system import BackgroundTask

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Background Task Progress Helpers
# ---------------------------------------------------------------------------

def update_progress_factory(task_id: Any) -> Callable[..., None]:
    """Generates a thread-safe helper to update task progress."""
    def update_progress(progress_val: int, status: str = 'RUNNING', error_msg: str = None, result_data: Any = None) -> None:
        try:
            with transaction.atomic():
                task = BackgroundTask.objects.get(id=task_id)
                task.progress = progress_val
                task.status = status
                if error_msg is not None:
                    task.error = error_msg
                if result_data is not None:
                    task.result = result_data
                task.save()
        except Exception as e:
            logger.error(f"TaskRegistry - Error - Failed to update task {task_id} progress: {e}")
    return update_progress


def run_task_in_thread(task_id: Any, func: Callable[..., None], *args: Any, **kwargs: Any) -> None:
    """Wrapper running the task and ensuring database connection cleanup."""
    update_progress = update_progress_factory(task_id)
    update_progress(0, status='RUNNING')
    
    try:
        func(update_progress, *args, **kwargs)
        task = BackgroundTask.objects.get(id=task_id)
        if task.status == 'RUNNING':
            update_progress(100, status='SUCCESS')
    except Exception as e:
        logger.error(f"TaskRegistry - Error - Task {task_id} execution failed: {e}", exc_info=True)
        update_progress(100, status='FAILED', error_msg=str(e))
    finally:
        import sys
        if 'test' not in sys.argv:
            connection.close()


def submit_backup_task(task_name: str, func: Callable[..., None], *args: Any, **kwargs: Any) -> BackgroundTask:
    """Submits a background task executed via a daemon thread."""
    task = BackgroundTask.objects.create(status=BackgroundTask.Status.RUNNING, progress=0)
    import sys
    if 'test' in sys.argv:
        run_task_in_thread(task.id, func, *args, **kwargs)
    else:
        thread = threading.Thread(
            target=run_task_in_thread,
            args=(task.id, func) + args,
            kwargs=kwargs,
            daemon=True
        )
        thread.start()
    return task


# ---------------------------------------------------------------------------
# Scheduler Daemon Loop
# ---------------------------------------------------------------------------

def backup_scheduler_loop():
    """Periodic daemon loop checking every 60s if a scheduled GFS backup is due."""
    logger.info("BackupScheduler - Started automated GFS backup daemon thread.")
    while True:
        try:
            from django.utils import timezone
            from apps.core.services.backup_service import determine_gfs_tier, execute_backup

            config = BackupConfiguration.get_config()
            if config.is_enabled:
                now = timezone.now()
                target_hour, target_min = map(int, config.backup_time.split(':'))
                is_due_time = (now.hour > target_hour) or (now.hour == target_hour and now.minute >= target_min)
                not_run_today = (config.last_run_at is None) or (config.last_run_at.date() < now.date())

                if is_due_time and not_run_today:
                    with connection.cursor() as cursor:
                        cursor.execute("SELECT pg_try_advisory_lock(987654321);")
                        locked = cursor.fetchone()[0]

                    if locked:
                        try:
                            config.refresh_from_db()
                            if (config.last_run_at is None) or (config.last_run_at.date() < now.date()):
                                tier = determine_gfs_tier(now, config)
                                logger.info(f"BackupScheduler - Executing scheduled {tier} database backup...")
                                execute_backup(tier=tier, config=config)
                                logger.info(f"BackupScheduler - Scheduled {tier} database backup succeeded.")
                        finally:
                            with connection.cursor() as cursor:
                                cursor.execute("SELECT pg_advisory_unlock(987654321);")
        except Exception as e:
            logger.error(f"BackupScheduler - Error in scheduler loop: {e}", exc_info=True)

        time.sleep(60)


def start_backup_scheduler_task():
    thread = threading.Thread(target=backup_scheduler_loop, daemon=True, name="GrainLabBackupSchedulerThread")
    thread.start()
    logger.info("BackupScheduler - Dispatched automated GFS backup daemon thread.")


# ---------------------------------------------------------------------------
# Celery compatibility bridges
# ---------------------------------------------------------------------------

@shared_task
def scheduled_backup_check():
    """Celery beat task hook running GFS check if Celery is used."""
    from django.utils import timezone
    from apps.core.services.backup_service import determine_gfs_tier, execute_backup

    config = BackupConfiguration.get_config()
    if not config.is_enabled:
        return

    now = timezone.now()
    target_hour, target_min = map(int, config.backup_time.split(':'))
    is_due_time = (now.hour > target_hour) or (now.hour == target_hour and now.minute >= target_min)
    not_run_today = (config.last_run_at is None) or (config.last_run_at.date() < now.date())

    if is_due_time and not_run_today:
        with connection.cursor() as cursor:
            cursor.execute("SELECT pg_try_advisory_lock(987654321);")
            locked = cursor.fetchone()[0]

        if locked:
            try:
                config.refresh_from_db()
                if (config.last_run_at is None) or (config.last_run_at.date() < now.date()):
                    tier = determine_gfs_tier(now, config)
                    execute_backup(tier=tier, config=config)
            finally:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT pg_advisory_unlock(987654321);")
