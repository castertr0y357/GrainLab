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
from apps.core import gemma


logger = logging.getLogger("grainlab.views")
executor = ThreadPoolExecutor(max_workers=2)

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


def ai_analyze_wheat_berry_task(task: BackgroundTask, wb_id: uuid.UUID) -> dict:
    wb = WheatBerry.objects.get(id=wb_id)
    task.progress = 30
    task.save()
    
    analysis = gemma.analyze_wheat_berry_ai(wb.name)
    task.progress = 80
    task.save()
    
    if analysis:
        wb.protein_content = analysis.get("protein_content", wb.protein_content)
        wb.moisture_absorption_coef = analysis.get("moisture_absorption_coef", wb.moisture_absorption_coef)
        wb.hardness = analysis.get("hardness", wb.hardness)
        wb.notes = analysis.get("notes", wb.notes)
        wb.ai_analyzed = True
        wb.save()
        return {"status": "success", "item_name": wb.name}
    else:
        raise Exception("Gemma AI response was empty or failed.")


def ai_analyze_equipment_task(task: BackgroundTask, eq_id: uuid.UUID) -> dict:
    eq = Equipment.objects.get(id=eq_id)
    task.progress = 30
    task.save()
    
    analysis = gemma.analyze_equipment_ai(eq.name, eq.equipment_type)
    task.progress = 80
    task.save()
    
    if analysis:
        eq.friction_heat_factor = analysis.get("friction_heat_factor", eq.friction_heat_factor)
        eq.notes = analysis.get("notes", eq.notes)
        eq.details = analysis.get("details", eq.details)
        eq.ai_analyzed = True
        eq.save()
        return {"status": "success", "item_name": eq.name}
    else:
        raise Exception("Gemma AI response was empty or failed.")


def bulk_ai_analyze_task(task: BackgroundTask) -> dict:
    unanalyzed_berries = list(WheatBerry.objects.filter(ai_analyzed=False))
    unanalyzed_eq = list(Equipment.objects.filter(ai_analyzed=False))
    
    total_items = len(unanalyzed_berries) + len(unanalyzed_eq)
    if total_items == 0:
        return {"status": "success", "processed_count": 0}
        
    processed = 0
    for wb in unanalyzed_berries:
        progress_pct = int(10 + (processed / total_items) * 80)
        task.progress = progress_pct
        task.save()
        
        analysis = gemma.analyze_wheat_berry_ai(wb.name)
        if analysis:
            wb.protein_content = analysis.get("protein_content", wb.protein_content)
            wb.moisture_absorption_coef = analysis.get("moisture_absorption_coef", wb.moisture_absorption_coef)
            wb.hardness = analysis.get("hardness", wb.hardness)
            wb.notes = analysis.get("notes", wb.notes)
            wb.ai_analyzed = True
            wb.save()
        processed += 1
        
    for eq in unanalyzed_eq:
        progress_pct = int(10 + (processed / total_items) * 80)
        task.progress = progress_pct
        task.save()
        
        analysis = gemma.analyze_equipment_ai(eq.name, eq.equipment_type)
        if analysis:
            eq.friction_heat_factor = analysis.get("friction_heat_factor", eq.friction_heat_factor)
            eq.notes = analysis.get("notes", eq.notes)
            eq.details = analysis.get("details", eq.details)
            eq.ai_analyzed = True
            eq.save()
        processed += 1
        
    return {"status": "success", "processed_count": processed}


def redo_ai_analysis_task(task: BackgroundTask, item_type: str, item_id: uuid.UUID) -> dict:
    if item_type == "wheat_berry":
        return ai_analyze_wheat_berry_task(task, item_id)
    elif item_type == "equipment":
        return ai_analyze_equipment_task(task, item_id)
    else:
        raise Exception(f"Unknown item type: {item_type}")


class TaskStatusView(View):
    def get(self, request: HttpRequest, task_id: uuid.UUID) -> HttpResponse:
        task = get_object_or_404(BackgroundTask, id=task_id)
        is_bulk = request.GET.get("bulk") == "true"
        
        if task.status in ('PENDING', 'RUNNING'):
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
                
        elif task.status == 'SUCCESS':
            response = HttpResponse(status=200)
            response['HX-Redirect'] = reverse('inventory_page')
            return response
            
        else:  # FAILED
            return HttpResponse(
                f'<div class="warning-box" style="margin: 0; padding: 0.5rem 1rem; border-radius: var(--radius-sm); font-size: 0.85rem; display: flex; flex-direction: column; gap: 0.25rem;">'
                f'  <h4 style="margin:0; font-size:0.9rem; color: var(--text-primary);">🤖 AI Analysis Failed</h4>'
                f'  <p style="margin:0; color: var(--text-secondary);">{task.error or "Unknown Ollama/Gemma error."}</p>'
                f'</div>'
            )


