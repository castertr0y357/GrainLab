import sys
import uuid
from apps.core.models import BackgroundTask
from apps.core.background_tasks.base import run_async_task

def queue_analyze_wheat_berry(item_id: uuid.UUID) -> uuid.UUID:
    task = BackgroundTask.objects.create()
    run_async_task.delay(task.id, 'ai_analyze_wheat_berry_task', item_id)
    return task.id

def queue_analyze_equipment(item_id: uuid.UUID) -> uuid.UUID:
    task = BackgroundTask.objects.create()
    run_async_task.delay(task.id, 'ai_analyze_equipment_task', item_id)
    return task.id

def queue_bulk_analyze() -> uuid.UUID:
    task = BackgroundTask.objects.create()
    run_async_task.delay(task.id, 'bulk_ai_analyze_task')
    return task.id

def queue_redo_analysis(item_type: str, item_id: uuid.UUID) -> uuid.UUID:
    task = BackgroundTask.objects.create()
    run_async_task.delay(task.id, 'redo_ai_analysis_task', item_type, item_id)
    return task.id
