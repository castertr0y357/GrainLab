import os
import sys
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
import django

# Setup django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "grainlab.settings")
django.setup()

from django.test import RequestFactory
from apps.core.views import calculate_recipe_ajax
from apps.core.models import DoughCategory, FormFactor

# Create a mock request
factory = RequestFactory()
post_data = {
    "dough_category": "lean-crusty",
    "form_factor": "standard-9x5-pan",
    "texture_score": "50",
    "crumb_score": "50",
    "flour_type": "all_purpose",
    "flour_maturity": "matured",
    "leaven_type": "yeast",
    "starter_pct": "0",
    "mixing_method": "stand_mixer",
    "proofing_environment": "ambient",
    "secondary_lipid": "unsalted_butter",
    "secondary_liquid": "pure_water",
    "secondary_binder": "none",
    "mill_type": "stoneground",
    "yield_scale": "1.0",
}

request = factory.post("/calculate/", data=post_data)
# Add metadata for HTMX
request.META["HTTP_HX_REQUEST"] = "true"

# Call the view function
response = calculate_recipe_ajax(request)
print("Response status code:", response.status_code)
# Output first 500 characters of the response content
print("Response preview:")
print(response.content.decode("utf-8")[:500])
