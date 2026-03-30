from typing import Any, Dict, Optional

from django.db import transaction
from django.http import HttpRequest
from django.utils import timezone
from django.db.models import Model

from apps.audit.services import log_audit_event

from .models import Policy, PolicyVersion


@transaction.atomic
def log_policy_update(
    *,
    actor,
    policy: Model,
    before_state: Dict[str, Any],
    after_state: Dict[str, Any],
    request: Optional[HttpRequest] = None,
) -> None:
    """
    Audit integration hook for policy updates.

    This service does not perform the update itself; instead, policy write
    operations should call it after persisting changes, passing in compact
    'before' and 'after' snapshots (e.g., key attributes and governance flags).
    """
    log_audit_event(
        actor=actor,
        action="policy.update",
        entity_type=policy.__class__.__name__,
        entity_id=policy.pk,
        request=request,
        metadata={
            "before": before_state,
            "after": after_state,
        },
    )


@transaction.atomic
def create_policy(*, actor, data: Dict[str, Any], request: Optional[HttpRequest] = None) -> Policy:
    policy = Policy.objects.create(created_by=actor, **data)
    log_audit_event(
        actor=actor,
        action="policy.create",
        entity_type="Policy",
        entity_id=policy.pk,
        request=request,
        metadata={"data": data},
    )
    return policy


@transaction.atomic
def update_policy(
    *,
    actor,
    policy: Policy,
    updated_fields: Dict[str, Any],
    request: Optional[HttpRequest] = None,
) -> Policy:
    before_state = {
        "code": policy.code,
        "title": policy.title,
        "description": policy.description,
        "is_active": policy.is_active,
        "metadata": policy.metadata,
    }

    for field, value in updated_fields.items():
        setattr(policy, field, value)
    policy.save()

    after_state = {
        "code": policy.code,
        "title": policy.title,
        "description": policy.description,
        "is_active": policy.is_active,
        "metadata": policy.metadata,
    }

    log_policy_update(
        actor=actor,
        policy=policy,
        before_state=before_state,
        after_state=after_state,
        request=request,
    )

    return policy


@transaction.atomic
def delete_policy(*, actor, policy: Policy, request: Optional[HttpRequest] = None) -> None:
    policy_id = policy.pk
    policy_code = policy.code
    policy.delete()

    log_audit_event(
        actor=actor,
        action="policy.delete",
        entity_type="Policy",
        entity_id=policy_id,
        request=request,
        metadata={"code": policy_code},
    )


@transaction.atomic
def approve_policy_version(
    *,
    actor,
    version: PolicyVersion,
    request: Optional[HttpRequest] = None,
) -> PolicyVersion:
    """
    Approve and activate a PolicyVersion for its financial year.
    Only SUPER_ADMIN should be allowed to call this via API layer.
    """
    before_status = version.status

    # Deactivate other ACTIVE versions for this policy + financial year
    PolicyVersion.objects.filter(
        policy=version.policy,
        financial_year=version.financial_year,
        status=PolicyVersion.Status.ACTIVE,
    ).exclude(pk=version.pk).update(status=PolicyVersion.Status.APPROVED)

    version.status = PolicyVersion.Status.ACTIVE
    version.approved_by = actor
    version.approved_at = timezone.now()
    version.activated_at = timezone.now()
    version.rejected_by = None
    version.rejected_at = None
    version.save()

    log_audit_event(
        actor=actor,
        action="policy.version.approve",
        entity_type="PolicyVersion",
        entity_id=version.pk,
        request=request,
        metadata={
            "policy_code": version.policy.code,
            "financial_year": version.financial_year,
            "before_status": before_status,
            "after_status": version.status,
        },
    )

    return version


@transaction.atomic
def reject_policy_version(
    *,
    actor,
    version: PolicyVersion,
    request: Optional[HttpRequest] = None,
) -> PolicyVersion:
    before_status = version.status

    version.status = PolicyVersion.Status.REJECTED
    version.rejected_by = actor
    version.rejected_at = timezone.now()
    version.save()

    log_audit_event(
        actor=actor,
        action="policy.version.reject",
        entity_type="PolicyVersion",
        entity_id=version.pk,
        request=request,
        metadata={
            "policy_code": version.policy.code,
            "financial_year": version.financial_year,
            "before_status": before_status,
            "after_status": version.status,
        },
    )

    return version


def get_policy_features(sector_id: int, date=None) -> dict:
    """Return policy-related numeric proxies for a sector and date.

    Example outputs: {'policy_active_count': 2, 'policy_effective_days': 120}
    This is intentionally simple and non-invasive.
    """
    try:
        from .models import Policy
        policies = Policy.objects.filter(is_active=True)
        count = policies.count()
        return {'policy_active_count': float(count)}
    except Exception:
        return {}

