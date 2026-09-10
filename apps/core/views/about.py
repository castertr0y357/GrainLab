import os

from django.conf import settings
from django.views.generic import TemplateView


def get_local_commit_hash():
    git_dir = os.path.join(settings.BASE_DIR, ".git")
    try:
        with open(os.path.join(git_dir, "HEAD")) as f:
            head_content = f.read().strip()
        if head_content.startswith("ref: "):
            ref_path = head_content.split(" ")[1]
            with open(os.path.join(git_dir, ref_path)) as f:
                return f.read().strip()
        else:
            return head_content
    except Exception:
        return None


class AboutPageView(TemplateView):
    template_name = "about.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["local_commit_hash"] = get_local_commit_hash()
        return context
