import logging
import uuid
from django.utils import timezone
from celery import shared_task
from apps.core.models import BackgroundTask
from apps.core.background_tasks.ai_analysis import (
    ai_analyze_wheat_berry_task, ai_analyze_equipment_task,
    bulk_ai_analyze_task, redo_ai_analysis_task
)

logger = logging.getLogger("grainlab.background_tasks")

TASK_MAPPING = {
    'ai_analyze_wheat_berry_task': ai_analyze_wheat_berry_task,
    'ai_analyze_equipment_task': ai_analyze_equipment_task,
    'bulk_ai_analyze_task': bulk_ai_analyze_task,
    'redo_ai_analysis_task': redo_ai_analysis_task,
}

@shared_task
def run_async_task(task_id: uuid.UUID, task_func_name: str, *args, **kwargs) -> None:
    task_func = TASK_MAPPING.get(task_func_name)
    if not task_func:
        logger.error(f"[BackgroundTask] - Error - Task function {task_func_name} not found")
        return
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
