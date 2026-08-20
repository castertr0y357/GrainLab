import json
import logging
from apps.core.gemma.core_client import stream_gemma_api, assemble_system_prompt
from grainlab.engines.router import ENGINES

logger = logging.getLogger("grainlab.gemma")

def stream_creative_ideas(user_prompt: str):
    """
    Given a free-form user prompt, generates creative recipe ideas mapping to our internal engines.
    """
    
    # Compile a dictionary of valid categories and archetypes
    frontend_slugs = [
        'lean-crusty', 'enriched-soft', 'alkaline-bath', 'flatbreads-griddles',
        'quick-breads-scones', 'cakes-batters', 'pastry-lamination', 'choux-paste',
        'cookies-shortbread', 'fried-doughs', 'fresh-pasta-noodles'
    ]
    valid_targets = []
    for category_slug in frontend_slugs:
        engine = ENGINES.get(category_slug)
        if not engine: continue
        for archetype_id, details in engine.archetypes.items():
            valid_targets.append({
                "category_slug": category_slug,
                "archetype_id": archetype_id,
                "archetype_name": details.get("name", archetype_id),
                "description": details.get("description", "")
            })
            
    context_str = json.dumps(valid_targets, indent=2)

    system_prompt = (
        "You are an expert artisan baker and culinary ideation engine.\n"
        "The user will give you a free-form idea of what they want to bake (e.g. 'I want bread for a PB&J' or 'Dutch Baby').\n"
        "Your task is to generate 3 to 5 distinct recipe ideas that fulfill their craving.\n\n"
        "CRITICAL RULE: You MUST map each of your ideas to one of the strictly valid 'category_slug' and 'archetype_id' pairs provided below.\n"
        "Do NOT invent new categories or archetypes.\n\n"
        f"Valid Targets Manifest:\n{context_str}\n\n"
    )

    task_instructions = (
        "Return a JSON stream of objects matching this schema:\n"
        "{\n"
        "  \"generated_ideas\": [\n"
        "    {\n"
        "      \"recipe_name\": \"string (A creative, appetizing name)\",\n"
        "      \"menu_description\": \"string (A 2-sentence description of the flavor and texture)\",\n"
        "      \"category_slug\": \"string (Must exactly match a category_slug from the manifest)\",\n"
        "      \"archetype_id\": \"string (Must exactly match an archetype_id from the manifest)\"\n"
        "    }\n"
        "  ]\n"
        "}"
    )

    full_system = assemble_system_prompt(None, "", task_instructions, "")
    # Prepend the unique instructions to the default assembled prompt
    full_system = system_prompt + full_system

    logger.info(f"[AI] - Phase 1 Creative Prompt execution for: {user_prompt}")
    
    # Stream the results
    yield from stream_gemma_api(full_system, user_prompt)
