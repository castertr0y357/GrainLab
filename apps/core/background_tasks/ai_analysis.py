import uuid

from apps.core import gemma
from apps.core.models import BackgroundTask, Equipment, WheatBerry


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
