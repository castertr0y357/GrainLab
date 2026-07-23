import logging
import math
import uuid
import json
from concurrent.futures import ThreadPoolExecutor
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views import View

from apps.core.models import DoughCategory, FormFactor, BreadPreset, SystemSetting, WheatBerry, Equipment, BackgroundTask
from apps.core import bakers_math
from apps.core import gemma_client
from apps.core.views.tasks import run_async_task, ai_analyze_wheat_berry_task, ai_analyze_equipment_task, bulk_ai_analyze_task, redo_ai_analysis_task

logger = logging.getLogger("grainlab.views")
executor = ThreadPoolExecutor(max_workers=2)


class AiAnalyzeWheatBerryView(View):
    def get(self, request: HttpRequest, id: uuid.UUID):
        """
        Runs AI analysis for a specific wheat berry.
        """
        task = BackgroundTask.objects.create()
        import sys
        if 'test' in sys.argv:
            run_async_task(task.id, ai_analyze_wheat_berry_task, id)
        else:
            executor.submit(run_async_task, task.id, ai_analyze_wheat_berry_task, id)
    
        # Return loading indicator to trigger polling
        return HttpResponse(
            f'<div hx-get="{reverse("task_status", args=[task.id])}" hx-trigger="every 1s" hx-swap="outerHTML" style="display: flex; align-items: center; gap: 0.25rem;">'
            f'  <span class="spinner" style="width: 12px; height: 12px;"></span>'
            f'  <span style="font-size: 0.8rem; color: var(--text-muted);">AI Running...</span>'
            f'</div>'
        )


class AiAnalyzeEquipmentView(View):
    def get(self, request: HttpRequest, id: uuid.UUID):
        """
        Runs AI analysis for a specific equipment item.
        """
        task = BackgroundTask.objects.create()
        import sys
        if 'test' in sys.argv:
            run_async_task(task.id, ai_analyze_equipment_task, id)
        else:
            executor.submit(run_async_task, task.id, ai_analyze_equipment_task, id)
    
        return HttpResponse(
            f'<div hx-get="{reverse("task_status", args=[task.id])}" hx-trigger="every 1s" hx-swap="outerHTML" style="display: flex; align-items: center; gap: 0.25rem;">'
            f'  <span class="spinner" style="width: 12px; height: 12px;"></span>'
            f'  <span style="font-size: 0.8rem; color: var(--text-muted);">AI Running...</span>'
            f'</div>'
        )


class BulkAiAnalyzeView(View):
    def get(self, request: HttpRequest):
        """
        Analyzes all unanalyzed inventory items.
        """
        task = BackgroundTask.objects.create()
        import sys
        if 'test' in sys.argv:
            run_async_task(task.id, bulk_ai_analyze_task)
        else:
            executor.submit(run_async_task, task.id, bulk_ai_analyze_task)
    
        return HttpResponse(
            f'<div hx-get="{reverse("task_status", args=[task.id])}?bulk=true" hx-trigger="every 1s" hx-swap="outerHTML" '
            f'style="display: flex; align-items: center; gap: 0.5rem; background: var(--bg-card); padding: 0.75rem 1.5rem; border-radius: var(--radius-sm); border: 1px solid var(--border);">'
            f'  <span>🤖 Bulk Analyzing...</span>'
            f'  <div style="flex: 1; height: 6px; background: var(--bg-input); border-radius: 3px; overflow: hidden; min-width: 100px;">'
            f'    <div style="width: 15%; height: 100%; background: var(--accent); transition: width 0.3s;"></div>'
            f'  </div>'
            f'  <span style="font-size: 0.85rem; font-weight: bold;">15%</span>'
            f'</div>'
        )


class RedoAiAnalysisView(View):
    def get(self, request: HttpRequest, item_type: str, id: uuid.UUID):
        """
        Re-analyzes an item (overriding manual tweaks).
        """
        task = BackgroundTask.objects.create()
        import sys
        if 'test' in sys.argv:
            run_async_task(task.id, redo_ai_analysis_task, item_type, id)
        else:
            executor.submit(run_async_task, task.id, redo_ai_analysis_task, item_type, id)
    
        return HttpResponse(
            f'<div hx-get="{reverse("task_status", args=[task.id])}" hx-trigger="every 1s" hx-swap="outerHTML" style="display: flex; align-items: center; gap: 0.25rem;">'
            f'  <span class="spinner" style="width: 12px; height: 12px;"></span>'
            f'  <span style="font-size: 0.8rem; color: var(--text-muted);">AI Running...</span>'
            f'</div>'
        )


