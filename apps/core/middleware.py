import json
import logging
import os
import sys
import threading
import time
import uuid
from datetime import datetime, timezone
from typing import Dict, Any

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.urls import Resolver404, resolve

APP_NAME = "grainlab"
_debug_enabled = os.environ.get("LOG_LEVEL", "INFO").upper() == "DEBUG" or os.environ.get("DEBUG_LOGGING", "").lower() in ("true", "1")

# Thread-local storage for correlation IDs
_thread_locals = threading.local()


def get_correlation_id() -> str:
    """Retrieves the correlation ID of the current request thread."""
    return getattr(_thread_locals, "correlation_id", "-")


class LokiJsonFormatter(logging.Formatter):
    """Outputs standardized single-line JSON log events for Loki ingestion."""
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "app": APP_NAME,
            "logger": record.name,
            "correlation_id": getattr(record, "correlation_id", get_correlation_id()),
            "action": getattr(record, "action", "general"),
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        context = getattr(record, "context", None)
        if context:
            log_entry["context"] = context
        return json.dumps(log_entry)


def set_debug_logging(enabled: bool):
    global _debug_enabled
    _debug_enabled = enabled
    target_level = logging.DEBUG if enabled else logging.INFO
    for name in ["django", "grainlab", "apps.core", ""]:
        logging.getLogger(name).setLevel(target_level)
    logging.getLogger("grainlab").info(
        f"[Observability] - Debug logging dynamically set to {enabled}",
        extra={"action": "observability.toggle_debug"}
    )


def is_debug_enabled() -> bool:
    return _debug_enabled


# In-memory Prometheus metrics registry for GrainLab
class GrainLabMetrics:
    def __init__(self):
        self.requests_total: Dict[str, int] = {}
        self.actions_total: Dict[str, int] = {}
        self.start_time = time.time()

    def record_request(self, method: str, path: str, status: int):
        normalized = path.split("?")[0]
        if normalized.startswith("/recipe/shared/") and len(normalized.split("/")) > 3:
            normalized = "/recipe/shared/{id}/"
        key = f'{APP_NAME}_http_requests_total{{method="{method}",path="{normalized}",status="{status}"}}'
        self.requests_total[key] = self.requests_total.get(key, 0) + 1

    def record_action(self, action: str, status: str = "success"):
        key = f'{APP_NAME}_actions_total{{action="{action}",status="{status}"}}'
        self.actions_total[key] = self.actions_total.get(key, 0) + 1

    def generate_metrics(self) -> str:
        lines = [
            f"# HELP {APP_NAME}_uptime_seconds Process uptime in seconds",
            f"# TYPE {APP_NAME}_uptime_seconds gauge",
            f"{APP_NAME}_uptime_seconds {round(time.time() - self.start_time, 2)}",
            f"# HELP {APP_NAME}_http_requests_total Total HTTP requests handled",
            f"# TYPE {APP_NAME}_http_requests_total counter"
        ]
        for k, v in sorted(self.requests_total.items()):
            lines.append(f"{k} {v}")
        lines.append(f"# HELP {APP_NAME}_actions_total Total domain actions executed",
                     f"# TYPE {APP_NAME}_actions_total counter")
        for k, v in sorted(self.actions_total.items()):
            lines.append(f"{k} {v}")
        return "\n".join(lines) + "\n"


metrics = GrainLabMetrics()
logger = logging.getLogger("grainlab.requests")


class CorrelationIDMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
        _thread_locals.correlation_id = correlation_id
        start_time = time.perf_counter()

        response = self.get_response(request)
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        response["X-Correlation-ID"] = correlation_id

        metrics.record_request(request.method, request.path, response.status_code)
        if not request.path.endswith("/metrics"):
            logger.info(
                f"{request.method} {request.path} -> {response.status_code} ({duration_ms}ms)",
                extra={
                    "action": "http.request",
                    "correlation_id": correlation_id,
                    "context": {"method": request.method, "path": request.path, "status": response.status_code, "duration_ms": duration_ms}
                }
            )

        if hasattr(_thread_locals, "correlation_id"):
            del _thread_locals.correlation_id

        return response


class CorrelationIDFilter(logging.Filter):
    """Logging filter to inject correlation_id into log records."""
    def filter(self, record):
        record.correlation_id = get_correlation_id()
        if not hasattr(record, "action"):
            record.action = "general"
        return True


class LoginRequiredMiddleware:
    """
    Middleware that requires a user to be authenticated to view any page other
    than the explicitly allowed URL names.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.allowed_url_names = {
            "shared_recipe",
            "metrics_view",
            "debug_logging_toggle_api",
            "readyz",
            "readyz_slash",
            "livez",
            "livez_slash",
            "healthz",
            "healthz_slash",
        }

    def __call__(self, request: HttpRequest) -> HttpResponse:
        if "test" in sys.argv:
            return self.get_response(request)

        # Allow /metrics, /readyz, /livez, /healthz without authentication
        if request.path_info in ("/metrics", "/metrics/", "/readyz", "/readyz/", "/livez", "/livez/", "/healthz", "/healthz/"):
            return self.get_response(request)

        if not request.user.is_authenticated:
            try:
                match = resolve(request.path_info)
                if match.app_name == "admin" or match.url_name == "login" or match.url_name in self.allowed_url_names:
                    return self.get_response(request)
            except Resolver404:
                pass

            if request.path_info.startswith(settings.STATIC_URL):
                return self.get_response(request)

            login_url = str(getattr(settings, "LOGIN_URL", "/login/"))

            if request.path_info == login_url:
                return self.get_response(request)

            if request.headers.get("HX-Request") == "true":
                response = HttpResponse(status=401)
                response["HX-Redirect"] = f"{login_url}?next={request.path}"
                return response

            return redirect(f"{login_url}?next={request.path}")

        return self.get_response(request)
