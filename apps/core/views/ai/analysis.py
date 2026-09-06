import uuid

from django.http import HttpRequest, HttpResponse
from django.urls import reverse
from django.views import View

from apps.core.services.ai.analysis_service import (
    queue_analyze_equipment,
    queue_analyze_wheat_berry,
    queue_bulk_analyze,
    queue_redo_analysis,
)


class AiAnalyzeWheatBerryView(View):
    def get(self, request: HttpRequest, id: uuid.UUID):
        """
        Runs AI analysis for a specific wheat berry.
        """
        task_id = queue_analyze_wheat_berry(id)

        # Return loading indicator to trigger polling
        return HttpResponse(
            f'<div hx-get="{reverse("task_status", args=[task_id])}" hx-trigger="every 1s" hx-swap="outerHTML" style="display: flex; align-items: center; gap: 0.25rem;">'
            f'  <span class="spinner" style="width: 12px; height: 12px;"></span>'
            f'  <span style="font-size: 0.8rem; color: var(--text-muted);">AI Running...</span>'
            f'</div>'
        )


class AiAnalyzeEquipmentView(View):
    def get(self, request: HttpRequest, id: uuid.UUID):
        """
        Runs AI analysis for a specific equipment item.
        """
        task_id = queue_analyze_equipment(id)

        return HttpResponse(
            f'<div hx-get="{reverse("task_status", args=[task_id])}" hx-trigger="every 1s" hx-swap="outerHTML" style="display: flex; align-items: center; gap: 0.25rem;">'
            f'  <span class="spinner" style="width: 12px; height: 12px;"></span>'
            f'  <span style="font-size: 0.8rem; color: var(--text-muted);">AI Running...</span>'
            f'</div>'
        )


class BulkAiAnalyzeView(View):
    def get(self, request: HttpRequest):
        """
        Analyzes all unanalyzed inventory items.
        """
        task_id = queue_bulk_analyze()

        return HttpResponse(
            f'<div hx-get="{reverse("task_status", args=[task_id])}?bulk=true" hx-trigger="every 1s" hx-swap="outerHTML" '
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
        task_id = queue_redo_analysis(item_type, id)

        return HttpResponse(
            f'<div hx-get="{reverse("task_status", args=[task_id])}" hx-trigger="every 1s" hx-swap="outerHTML" style="display: flex; align-items: center; gap: 0.25rem;">'
            f'  <span class="spinner" style="width: 12px; height: 12px;"></span>'
            f'  <span style="font-size: 0.8rem; color: var(--text-muted);">AI Running...</span>'
            f'</div>'
        )
