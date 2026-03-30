from typing import Optional

from django.db import transaction
from django.http import HttpRequest

from apps.audit.services import log_audit_event
from apps.users.models import User

from .models import Role


@transaction.atomic
def change_user_primary_role(
    *,
    actor: User,
    target_user: User,
    new_role: Optional[Role],
    request: Optional[HttpRequest] = None,
) -> User:
    """
    Governance-aware primary role change.

    Rules (can be extended later):
    - Only SUPER_ADMIN (or Django superuser) can change roles.
    - Super admin cannot accidentally remove their own SUPER_ADMIN role.
    - Every change is logged into AuditLog with before/after.
    """
    if actor is None or not actor.is_authenticated:
        raise PermissionError("Authenticated actor required for role changes.")

    actor_role = getattr(actor, "primary_role", None)
    actor_role_code = getattr(actor_role, "code", "") if actor_role else ""

    if actor_role_code != "SUPER_ADMIN" and not actor.is_superuser:
        raise PermissionError("Only SUPER_ADMIN may change user roles.")

    if actor.pk == target_user.pk and new_role is None:
        raise PermissionError("Refusing to remove own primary role.")

    before_role_code = getattr(target_user.primary_role, "code", None)
    after_role_code = getattr(new_role, "code", None) if new_role else None

    target_user.primary_role = new_role
    target_user.save(update_fields=["primary_role"])

    log_audit_event(
        actor=actor,
        action="role.change",
        entity_type="User",
        entity_id=target_user.pk,
        request=request,
        metadata={
            "before_role_code": before_role_code,
            "after_role_code": after_role_code,
        },
    )

    return target_user

