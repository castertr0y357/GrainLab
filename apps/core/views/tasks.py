import logging
import uuid

from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views import View

from apps.core.models import BackgroundTask

logger = logging.getLogger("grainlab.views")


class TaskStatusView(View):
    def get(self, request: HttpRequest, task_id: uuid.UUID) -> HttpResponse:
        task = get_object_or_404(BackgroundTask, id=task_id)
        is_bulk = request.GET.get("bulk") == "true"

        if task.status in ("PENDING", "RUNNING"):
            if is_bulk:
                return HttpResponse(
                    f'<div hx-get="{reverse("task_status", args=[task.id])}?bulk=true" '
                    f'hx-trigger="every 1s" hx-swap="outerHTML" '
                    f'style="display: flex; align-items: center; gap: 0.5rem; background: var(--bg-card); padding: 0.75rem 1.5rem; border-radius: var(--radius-sm); border: 1px solid var(--border);">'
                    f'  <span>🤖 Bulk Analyzing...</span>'
                    f'  <div style="flex: 1; height: 6px; background: var(--bg-input); border-radius: 3px; overflow: hidden; min-width: 100px;">'
                    f'    <div style="width: {task.progress}%; height: 100%; background: var(--accent); transition: width 0.3s;"></div>'
                    f'  </div>'
                    f'  <span style="font-size: 0.85rem; font-weight: bold;">{task.progress}%</span>'
                    f'</div>'
                )
            else:
                return HttpResponse(
                    f'<div hx-get="{reverse("task_status", args=[task.id])}" '
                    f'hx-trigger="every 1s" hx-swap="outerHTML" style="display: flex; align-items: center; gap: 0.25rem;">'
                    f'  <span class="spinner" style="width: 12px; height: 12px;"></span>'
                    f'  <span style="font-size: 0.8rem; color: var(--text-muted);">AI Running ({task.progress}%)...</span>'
                    f'</div>'
                )

        elif task.status == "SUCCESS":
            response = HttpResponse(status=200)
            redirect_url = reverse("inventory_page")
            tab = request.GET.get("tab")
            if tab:
                redirect_url += f"?tab={tab}"
            response["HX-Redirect"] = redirect_url
            return response

        else:  # FAILED
            return HttpResponse(
                f'<div class="warning-box" style="margin: 0; padding: 0.5rem 1rem; border-radius: var(--radius-sm); font-size: 0.85rem; display: flex; flex-direction: column; gap: 0.25rem;">'
                f'  <h4 style="margin:0; font-size:0.9rem; color: var(--text-primary);">🤖 AI Analysis Failed</h4>'
                f'  <p style="margin:0; color: var(--text-secondary);">{task.error or "Unknown Ollama/Gemma error."}</p>'
                f'</div>'
            )
