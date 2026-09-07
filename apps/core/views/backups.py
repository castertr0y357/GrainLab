import glob
import os

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.cache import cache
from django.core.files.storage import FileSystemStorage
from django.http import FileResponse, Http404, HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.views import View
from django.views.generic import TemplateView

from apps.core.tasks.backups import create_backup, restore_backup

BACKUP_DIR = os.path.join(settings.BASE_DIR, "backups")


class BackupsStatusView(View):
    def get(self, request, *args, **kwargs):
        return JsonResponse({"maintenance_mode": bool(cache.get("MAINTENANCE_MODE"))})


class BackupsListPartial(LoginRequiredMixin, TemplateView):
    template_name = "partials/backups_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        os.makedirs(BACKUP_DIR, exist_ok=True)
        backups = []
        for file in glob.glob(os.path.join(BACKUP_DIR, "*.sql.gz")):
            backups.append(
                {
                    "name": os.path.basename(file),
                    "size_mb": round(os.path.getsize(file) / (1024 * 1024), 2),
                    "created_at": os.path.getctime(file),
                }
            )
        backups.sort(key=lambda x: x["created_at"], reverse=True)
        context["backups"] = backups
        return context


class BackupCreateView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        create_backup.delay()
        response = HttpResponse(status=204)
        response["HX-Trigger"] = "refreshBackups"
        return response


class BackupRestoreView(LoginRequiredMixin, View):
    def post(self, request, filename, *args, **kwargs):
        filepath = os.path.join(BACKUP_DIR, filename)
        if not os.path.exists(filepath):
            raise Http404("Backup not found")
        restore_backup.delay(filename)
        # We redirect normally so the user is forced to hit the maintenance lock page
        response = HttpResponse(status=204)
        response["HX-Redirect"] = reverse("settings_page")
        return response


class BackupDownloadView(LoginRequiredMixin, View):
    def get(self, request, filename, *args, **kwargs):
        filepath = os.path.join(BACKUP_DIR, filename)
        if not os.path.exists(filepath):
            raise Http404("Backup not found")
        return FileResponse(open(filepath, "rb"), as_attachment=True, filename=filename)


class BackupDeleteView(LoginRequiredMixin, View):
    def post(self, request, filename, *args, **kwargs):
        filepath = os.path.join(BACKUP_DIR, filename)
        if os.path.exists(filepath):
            os.remove(filepath)
        response = HttpResponse(status=204)
        response["HX-Trigger"] = "refreshBackups"
        return response


class BackupUploadView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        if "backup_file" in request.FILES:
            upload = request.FILES["backup_file"]
            if upload.name.endswith(".sql.gz"):
                os.makedirs(BACKUP_DIR, exist_ok=True)
                fs = FileSystemStorage(location=BACKUP_DIR)
                # Overwrite if exists
                if fs.exists(upload.name):
                    fs.delete(upload.name)
                fs.save(upload.name, upload)
        return redirect(reverse("settings_page"))
