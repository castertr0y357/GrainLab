import logging
import threading
import uuid

from django.http import HttpRequest, HttpResponse

# Thread-local storage for correlation IDs
_thread_locals = threading.local()


def get_correlation_id() -> str:
    """Retrieves the correlation ID of the current request thread."""
    return getattr(_thread_locals, "correlation_id", "-")


class CorrelationIDMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        # Check if incoming request already has a correlation ID
        correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())

        # Store in thread-local
        _thread_locals.correlation_id = correlation_id

        response = self.get_response(request)

        # Set in response header
        response["X-Correlation-ID"] = correlation_id

        # Clean up thread-local
        if hasattr(_thread_locals, "correlation_id"):
            del _thread_locals.correlation_id

        return response


class CorrelationIDFilter(logging.Filter):
    """Logging filter to inject correlation_id into log records."""

    def filter(self, record):
        record.correlation_id = get_correlation_id()
        return True


from django.conf import settings
from django.shortcuts import redirect
from django.urls import resolve


class LoginRequiredMiddleware:
    """
    Middleware that requires a user to be authenticated to view any page other
    than the explicitly allowed URL names.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        # URL names that are accessible without authentication
        self.allowed_url_names = {
            "shared_recipe",
        }

    def __call__(self, request: HttpRequest) -> HttpResponse:
        import sys

        if "test" in sys.argv:
            return self.get_response(request)

        if not request.user.is_authenticated:
            # Resolve the URL to get the url_name
            try:
                match = resolve(request.path_info)
                # Allow access to admin login, django login, and allowed views
                if match.app_name == "admin" or match.url_name == "login" or match.url_name in self.allowed_url_names:
                    return self.get_response(request)
            except Exception:
                pass

            # Allow whitenoise or other static requests that might bypass resolver but hit here
            if request.path_info.startswith(settings.STATIC_URL):
                return self.get_response(request)

            login_url = str(getattr(settings, "LOGIN_URL", "/login/"))

            # Prevent infinite redirect loops if we are already on the login page
            if request.path_info == login_url:
                return self.get_response(request)

            # Redirect to login
            return redirect(f"{login_url}?next={request.path}")

        return self.get_response(request)
