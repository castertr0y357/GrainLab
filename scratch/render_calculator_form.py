import os
import sys
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
import django

# Setup django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "grainlab.settings")
django.setup()

from django.template.loader import render_to_string
from apps.core.models import WheatBerry, DoughCategory, FormFactor, BreadPreset, Equipment
from apps.core.views import get_engines_ff_json, get_engines_archetypes_json

# Fetch context data from DB
active_berries = list(WheatBerry.objects.filter(is_active=True))
categories = DoughCategory.objects.all().order_by('name')
form_factors = FormFactor.objects.all().order_by('name')
presets = BreadPreset.objects.all().order_by('name')

context = {
    "active_berries": active_berries,
    "categories": categories,
    "form_factors": form_factors,
    "presets": presets,
    "ai_enabled": False,
    "engines_ff_json": get_engines_ff_json(),
    "engines_archetypes_json": get_engines_archetypes_json(),
    "default_texture_score": 50,
    "default_crumb_score": 50,
    "default_starter": 0,
    "default_flour_type": "all_purpose",
    "default_flour_maturity": "matured",
    "selected_category": categories.first(),
    "selected_form_factor": form_factors.first(),
}

# Render partials/calculator_form.html to string
rendered_html = render_to_string("partials/calculator_form.html", context)

with open("scratch/rendered_calculator_form.html", "w", encoding="utf-8") as f:
    f.write(rendered_html)

print("Rendered calculator_form.html successfully saved to scratch/rendered_calculator_form.html")

# Extract the exact x-data attribute string from the rendered HTML
import re
match = re.search(r'x-data="(\{.*?\})"', rendered_html, re.DOTALL)
if match:
    import html
    js_object_str = html.unescape(match.group(1))
    
    js_code = f"const xData = {js_object_str};\nmodule.exports = xData;"
    with open("scratch/rendered_form_xdata.js", "w", encoding="utf-8") as f:
        f.write(js_code)
        
    import subprocess
    print("Running Node.js validation on the actual RENDERED form x-data Javascript...")
    result = subprocess.run(["node", "--check", "scratch/rendered_form_xdata.js"], capture_output=True, text=True)
    if result.returncode == 0:
        print("Success: Node.js verified that the rendered form JS is 100% syntactically correct!")
    else:
        print("Syntax Error Found in Rendered Form JS:")
        print(result.stderr)
else:
    print("Could not find x-data tag in rendered HTML form!")
