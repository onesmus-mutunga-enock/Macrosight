import hashlib
import json
from typing import Any, Dict, Optional

from django.db import transaction
from django.utils import timezone
from django.http import HttpRequest

from apps.audit.services import log_audit_event

from ..models import DataSnapshot


def _generate_snapshot_hash(payload: Dict[str, Any]) -> str:
    """
    Deterministic hash over the snapshot definition.

    We intentionally only hash the logical definition (context + metadata) and
    not database primary keys of underlying rows, to keep this independent from
    physical storage details. The caller is responsible for embedding stable
    identifiers (e.g., dataset IDs, policy versions) into the context.
    """
    normalized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


@transaction.atomic
def freeze_snapshot(
    *,
    created_by,
    name: str,
    description: str = "",
    context: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    request: Optional[HttpRequest] = None,
) -> DataSnapshot:
    """
    Create a new FROZEN data snapshot with a deterministic content hash.
    """
    context = context or {}
    metadata = metadata or {}

    hash_input = {
        "name": name,
        "description": description,
        "context": context,
        "metadata": metadata,
    }
    content_hash = _generate_snapshot_hash(hash_input)

    snapshot = DataSnapshot.objects.create(
        name=name,
        description=description,
        status=DataSnapshot.Status.FROZEN,
        context=context,
        content_hash=content_hash,
        created_by=created_by,
        metadata=metadata,
    )

    log_audit_event(
        actor=created_by,
        action="snapshot.freeze",
        entity_type="DataSnapshot",
        entity_id=snapshot.pk,
        request=request,
        metadata={
            "content_hash": content_hash,
            "context": context,
        },
    )

    return snapshot


@transaction.atomic
def lock_snapshot(
    *,
    snapshot: DataSnapshot,
    locked_by,
    request: Optional[HttpRequest] = None,
) -> DataSnapshot:
    """
    Transition a snapshot from FROZEN to LOCKED.
    Once LOCKED, context and metadata must not change.
    """
    if snapshot.status == DataSnapshot.Status.LOCKED:
        # Idempotent lock; still log the attempt for auditability.
        log_audit_event(
            actor=locked_by,
            action="snapshot.lock.idempotent",
            entity_type="DataSnapshot",
            entity_id=snapshot.pk,
            request=request,
            metadata={"message": "Snapshot already locked"},
        )
        return snapshot

    before_status = snapshot.status
    snapshot.status = DataSnapshot.Status.LOCKED
    snapshot.locked_by = locked_by
    snapshot.locked_at = timezone.now()
    snapshot.save(update_fields=["status", "locked_by", "locked_at"])

    log_audit_event(
        actor=locked_by,
        action="snapshot.lock",
        entity_type="DataSnapshot",
        entity_id=snapshot.pk,
        request=request,
        metadata={
            "before_status": before_status,
            "after_status": snapshot.status,
            "content_hash": snapshot.content_hash,
        },
    )

    return snapshot

