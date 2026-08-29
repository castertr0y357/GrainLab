import logging
import uuid
from django.utils import timezone
from apps.core.models import BackgroundTask

logger = logging.getLogger("grainlab.background_tasks")

def run_async_task(task_id: uuid.UUID, task_func, *args, **kwargs) -> None:
    try:
        task = BackgroundTask.objects.get(id=task_id)
        task.status = 'RUNNING'
        task.progress = 15
        task.save()
        
        result_data = task_func(task, *args, **kwargs)
        
        task.status = 'SUCCESS'
        task.progress = 100
        task.result = result_data
        task.completed_at = timezone.now()
        task.save()
    except Exception as e:
        logger.error(f"[BackgroundTask] - Error - Task {task_id} failed: {e}")
        try:
            task = BackgroundTask.objects.get(id=task_id)
            task.status = 'FAILED'
            task.progress = 100
            task.error = str(e)
            task.completed_at = timezone.now()
            task.save()
        except Exception:
            pass
