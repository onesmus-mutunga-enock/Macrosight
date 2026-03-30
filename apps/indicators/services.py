from typing import Any, Dict, Optional

from django.db import transaction
from django.http import HttpRequest

from apps.audit.services import log_audit_event
from .models import Indicator, IndicatorVersion


@transaction.atomic
def create_indicator(*, actor, data: Dict[str, Any], request: Optional[HttpRequest] = None) -> Indicator:
    indicator = Indicator.objects.create(created_by=actor, **data)
    log_audit_event(
        actor=actor,
        action="indicator.create",
        entity_type="Indicator",
        entity_id=indicator.pk,
        request=request,
        metadata={"data": data},
    )
    return indicator


@transaction.atomic
def update_indicator(
    *,
    actor,
    indicator: Indicator,
    updated_fields: Dict[str, Any],
    request: Optional[HttpRequest] = None,
) -> Indicator:
    before = {
        "code": indicator.code,
        "name": indicator.name,
        "description": indicator.description,
        "source": indicator.source,
        "is_active": indicator.is_active,
        "metadata": indicator.metadata,
    }

    for field, value in updated_fields.items():
        setattr(indicator, field, value)
    indicator.save()

    after = {
        "code": indicator.code,
        "name": indicator.name,
        "description": indicator.description,
        "source": indicator.source,
        "is_active": indicator.is_active,
        "metadata": indicator.metadata,
    }

    log_audit_event(
        actor=actor,
        action="indicator.update",
        entity_type="Indicator",
        entity_id=indicator.pk,
        request=request,
        metadata={"before": before, "after": after},
    )

    return indicator


@transaction.atomic
def delete_indicator(*, actor, indicator: Indicator, request: Optional[HttpRequest] = None) -> None:
    indicator_id = indicator.pk
    indicator_code = indicator.code
    indicator.delete()

    log_audit_event(
        actor=actor,
        action="indicator.delete",
        entity_type="Indicator",
        entity_id=indicator_id,
        request=request,
        metadata={"code": indicator_code},
    )


@transaction.atomic
def record_indicator_ingestion(
    *,
    actor,
    indicator: Indicator,
    version_label: str,
    source: str,
    payload_metadata: Dict[str, Any],
    quality_score: Optional[float] = None,
    request: Optional[HttpRequest] = None,
) -> IndicatorVersion:
    """
    Creates an IndicatorVersion entry representing an ingestion event.
    """
    version = IndicatorVersion.objects.create(
        indicator=indicator,
        version_label=version_label,
        source=source,
        quality_score=quality_score,
        payload_metadata=payload_metadata,
    )

    log_audit_event(
        actor=actor,
        action="indicator.ingestion",
        entity_type="IndicatorVersion",
        entity_id=version.pk,
        request=request,
        metadata={
            "indicator_code": indicator.code,
            "version_label": version_label,
            "source": source,
        },
    )

    return version

