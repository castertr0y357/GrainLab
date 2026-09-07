import datetime

from celery import shared_task
from django.utils import timezone

from apps.core.models.inventory import Equipment, WheatBerry
from apps.core.models.recipe import SavedRecipe
from apps.core.models.system import SystemSetting


@shared_task
def prune_soft_deleted_records():
    """
    Finds and permanently deletes records from SoftDeleteModels
    that have been soft-deleted longer than the retention period.
    """
    retention_days = int(SystemSetting.get_val("soft_delete_retention_days", "30"))
    if retention_days <= 0:
        return "Pruning disabled (retention set to 0 or less)."

    cutoff_date = timezone.now() - datetime.timedelta(days=retention_days)

    deleted_counts = {}

    models_to_check = [
        ("WheatBerry", WheatBerry),
        ("Equipment", Equipment),
        ("SavedRecipe", SavedRecipe),
    ]

    for model_name, model_class in models_to_check:
        # Get records that are 'dead' and deleted before the cutoff date
        expired_records = model_class.all_objects.filter(deleted_at__isnull=False, deleted_at__lte=cutoff_date)

        count = expired_records.count()
        if count > 0:
            # We call hard_delete() which is defined on SoftDeleteQuerySet
            expired_records.hard_delete()
            deleted_counts[model_name] = count

    return f"Pruned records: {deleted_counts}"
