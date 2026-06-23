import uuid
import logging
import threading
from django.http import HttpRequest, HttpResponse

# Thread-local storage for correlation IDs
_thread_locals = threading.local()

def get_correlation_id() -> str:
    """Retrieves the correlation ID of the current request thread."""
    return getattr(_thread_locals, 'correlation_id', '-')

class CorrelationIDMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        # Check if incoming request already has a correlation ID
        correlation_id = request.headers.get('X-Correlation-ID') or str(uuid.uuid4())
        
        # Store in thread-local
        _thread_locals.correlation_id = correlation_id
        
        response = self.get_response(request)
        
        # Set in response header
        response['X-Correlation-ID'] = correlation_id
        
        # Clean up thread-local
        if hasattr(_thread_locals, 'correlation_id'):
            del _thread_locals.correlation_id
            
        return response

class CorrelationIDFilter(logging.Filter):
    """Logging filter to inject correlation_id into log records."""
    def filter(self, record):
        record.correlation_id = get_correlation_id()
        return True
