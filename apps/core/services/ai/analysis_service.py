import sys
import uuid
from apps.core.models import BackgroundTask
from apps.core.background_tasks import (
    executor, run_async_task, ai_analyze_wheat_berry_task, 
    ai_analyze_equipment_task, bulk_ai_analyze_task, redo_ai_analysis_task
)

def queue_analyze_wheat_berry(item_id: uuid.UUID) -> uuid.UUID:
    task = BackgroundTask.objects.create()
    if 'test' in sys.argv:
        run_async_task(task.id, ai_analyze_wheat_berry_task, item_id)
    else:
        executor.submit(run_async_task, task.id, ai_analyze_wheat_berry_task, item_id)
    return task.id

def queue_analyze_equipment(item_id: uuid.UUID) -> uuid.UUID:
    task = BackgroundTask.objects.create()
    if 'test' in sys.argv:
        run_async_task(task.id, ai_analyze_equipment_task, item_id)
    else:
        executor.submit(run_async_task, task.id, ai_analyze_equipment_task, item_id)
    return task.id

def queue_bulk_analyze() -> uuid.UUID:
    task = BackgroundTask.objects.create()
    if 'test' in sys.argv:
        run_async_task(task.id, bulk_ai_analyze_task)
    else:
        executor.submit(run_async_task, task.id, bulk_ai_analyze_task)
    return task.id

def queue_redo_analysis(item_type: str, item_id: uuid.UUID) -> uuid.UUID:
    task = BackgroundTask.objects.create()
    if 'test' in sys.argv:
        run_async_task(task.id, redo_ai_analysis_task, item_type, item_id)
    else:
        executor.submit(run_async_task, task.id, redo_ai_analysis_task, item_type, item_id)
    return task.id
