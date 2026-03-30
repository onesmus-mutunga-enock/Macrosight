from typing import Any, Optional

from django.http import HttpRequest

from .models import AuditLog


def log_audit_event(
    *,
    actor,
    action: str,
    entity_type: str,
    entity_id: Any,
    request: Optional[HttpRequest] = None,
    metadata: Optional[dict] = None,
) -> AuditLog:
    """
    Central helper used by domain services to create audit entries.

    - actor: User performing the action (may be None for system events)
    - action: high-level code, e.g. 'policy.update', 'role.change', 'snapshot.lock'
    - entity_type: logical entity type, e.g. 'Policy', 'User', 'DataSnapshot'
    - entity_id: identifier of the entity (converted to string)
    - request: optional HttpRequest, to enrich context (IP, method, path, correlation_id)
    - metadata: structured payload stored in JSONField
    """
    actor_role_code = ""
    if actor is not None:
        role = getattr(actor, "primary_role", None)
        actor_role_code = getattr(role, "code", "") or ""

    request_method = ""
    request_path = ""
    ip_address = None
    correlation_id = ""

    if request is not None:
        request_method = request.method
        request_path = request.get_full_path()
        ip_address = request.META.get("REMOTE_ADDR")
        correlation_id = getattr(request, "correlation_id", "")

    log = AuditLog.objects.create(
        actor=actor,
        actor_role_code=actor_role_code,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id),
        request_method=request_method,
        request_path=request_path,
        correlation_id=correlation_id,
        ip_address=ip_address,
        metadata=metadata or {},
    )
    return log

