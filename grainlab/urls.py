from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path
from django.http import HttpResponse

def readyz(request):
    return HttpResponse("OK", content_type="text/plain", status=200)

def livez(request):
    return HttpResponse("OK", content_type="text/plain", status=200)

def healthz(request):
    return HttpResponse("OK", content_type="text/plain", status=200)

urlpatterns = [
    path('readyz', readyz, name='readyz'),
    path('readyz/', readyz, name='readyz_slash'),
    path('livez', livez, name='livez'),
    path('livez/', livez, name='livez_slash'),
    path('healthz', healthz, name='healthz'),
    path('healthz/', healthz, name='healthz_slash'),
    path("admin/", admin.site.urls),
    path("login/", auth_views.LoginView.as_view(template_name="login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(next_page="/login/"), name="logout"),
    path("", include("apps.core.urls")),
]
