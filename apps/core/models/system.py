import uuid
from django.db import models

class SystemSetting(models.Model):
    """
    Stores application-level preference toggles and AI configurations.
    """
    key = models.CharField(max_length=100, unique=True, db_index=True)
    value = models.TextField(blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['key']),
        ]

    def __str__(self):
        return f"{self.key} = {self.value}"

    @classmethod
    def get_val(cls, key, default=None):
        try:
            obj = cls.objects.get(key=key)
            return obj.value
        except cls.DoesNotExist:
            return default

    @classmethod
    def set_val(cls, key, val):
        cls.objects.update_or_create(key=key, defaults={'value': str(val)})


class BackgroundTask(models.Model):
    """
    Stores background task status for AI analysis and heavy calculations.
    """
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        RUNNING = 'RUNNING', 'Running'
        SUCCESS = 'SUCCESS', 'Success'
        FAILED = 'FAILED', 'Failed'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    progress = models.IntegerField(default=0, help_text="Progress percentage (0-100)")
    result = models.JSONField(null=True, blank=True, help_text="Success result payload")
    error = models.TextField(blank=True, help_text="Error message if failed")
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Task {self.id} ({self.status} - {self.progress}%)"
