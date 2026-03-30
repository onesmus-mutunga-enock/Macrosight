from typing import Any, Dict, Optional

from django.db import transaction
from django.http import HttpRequest

from apps.audit.services import log_audit_event
from .models import Sector, SectorPolicyMapping


@transaction.atomic
def create_sector(*, actor, data: Dict[str, Any], request: Optional[HttpRequest] = None) -> Sector:
    sector = Sector.objects.create(created_by=actor, **data)
    log_audit_event(
        actor=actor,
        action="sector.create",
        entity_type="Sector",
        entity_id=sector.pk,
        request=request,
        metadata={"data": data},
    )
    return sector


@transaction.atomic
def update_sector(
    *,
    actor,
    sector: Sector,
    updated_fields: Dict[str, Any],
    request: Optional[HttpRequest] = None,
) -> Sector:
    before = {
        "code": sector.code,
        "name": sector.name,
        "description": sector.description,
        "is_active": sector.is_active,
        "metadata": sector.metadata,
    }

    for field, value in updated_fields.items():
        setattr(sector, field, value)
    sector.save()

    after = {
        "code": sector.code,
        "name": sector.name,
        "description": sector.description,
        "is_active": sector.is_active,
        "metadata": sector.metadata,
    }

    log_audit_event(
        actor=actor,
        action="sector.update",
        entity_type="Sector",
        entity_id=sector.pk,
        request=request,
        metadata={"before": before, "after": after},
    )

    return sector


@transaction.atomic
def delete_sector(*, actor, sector: Sector, request: Optional[HttpRequest] = None) -> None:
    sector_id = sector.pk
    sector_code = sector.code
    sector.delete()

    log_audit_event(
        actor=actor,
        action="sector.delete",
        entity_type="Sector",
        entity_id=sector_id,
        request=request,
        metadata={"code": sector_code},
    )


@transaction.atomic
def create_sector_policy_mapping(
    *,
    actor,
    sector: Sector,
    policy,
    metadata: Optional[Dict[str, Any]] = None,
    request: Optional[HttpRequest] = None,
) -> SectorPolicyMapping:
    mapping, created = SectorPolicyMapping.objects.get_or_create(
        sector=sector,
        policy=policy,
        defaults={"metadata": metadata or {}},
    )
    if not created and metadata is not None:
        mapping.metadata = metadata
        mapping.save(update_fields=["metadata"])

    log_audit_event(
        actor=actor,
        action="sector.policy.map",
        entity_type="SectorPolicyMapping",
        entity_id=mapping.pk,
        request=request,
        metadata={
            "sector_code": sector.code,
            "policy_code": policy.code,
        },
    )
    return mapping


@transaction.atomic
def delete_sector_policy_mapping(
    *,
    actor,
    mapping: SectorPolicyMapping,
    request: Optional[HttpRequest] = None,
) -> None:
    mapping_id = mapping.pk
    sector_code = mapping.sector.code
    policy_code = mapping.policy.code
    mapping.delete()

    log_audit_event(
        actor=actor,
        action="sector.policy.unmap",
        entity_type="SectorPolicyMapping",
        entity_id=mapping_id,
        request=request,
        metadata={
            "sector_code": sector_code,
            "policy_code": policy_code,
        },
    )

