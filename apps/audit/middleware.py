import uuid


class AuditMiddleware:
    """
    Lightweight middleware that enriches the request with a correlation ID.

    Domain services can attach this correlation ID to AuditLog entries to
    correlate user actions with downstream events (e.g., snapshot locks).
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        correlation_id = str(uuid.uuid4())
        request.correlation_id = correlation_id

        response = self.get_response(request)
        # Expose correlation ID to clients for debugging / traceability
        response["X-Correlation-ID"] = correlation_id
        return response

