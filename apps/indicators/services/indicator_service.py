from django.db import transaction

from apps.audit.services import log_audit_event as audit_event
from apps.users.models import User
from django.utils import timezone
from ..models import Indicator, IndicatorVersion


def create_indicator(actor: User, data: dict, request=None):
    """
    Create new indicator with initial version.
    """
    with transaction.atomic():
        indicator = Indicator.objects.create(**data)
        IndicatorVersion.objects.create(
            indicator=indicator,
            version_label="v1.0",
            created_by=actor,
        )
        audit_event(
            actor=actor,
            target_object=indicator,
            action="indicator.create",
            request=request,
        )
        return indicator


def update_indicator(actor: User, indicator: Indicator, updated_fields: dict, request=None):
    """
    Update mutable fields on indicator.
    """
    mutable = {k: v for k, v in updated_fields.items() if k in ['code', 'name', 'unit', 'description', 'source', 'metadata']}
    for field, value in mutable.items():
        setattr(indicator, field, value)
    indicator.save(update_fields=list(mutable.keys()))
    audit_event(
        actor=actor,
        target_object=indicator,
        action="indicator.update",
        changes=mutable,
        request=request,
    )
    return indicator


def delete_indicator(actor: User, indicator: Indicator, request=None):
    """
    Soft-delete indicator.
    """
    indicator.is_active = False
    indicator.save(update_fields=["is_active"])
    audit_event(
        actor=actor,
        target_object=indicator,
        action="indicator.delete",
        request=request,
    )


def record_indicator_ingestion(actor: User, indicator: Indicator, data_snapshot_id: str, request=None):
    """
    Record new version from external ingestion.
    """
    version = IndicatorVersion.objects.create(
        indicator=indicator,
        version_label=f"ingest-{data_snapshot_id}",
        ingestion_timestamp=timezone.now(),
        created_by=actor,
    )
    audit_event(
        actor=actor,
        target_object=version,
        action="indicator.ingestion",
        request=request,
    )
    return version


def get_indicator_features(sector_id: int, date=None):
    """Return a small dict of indicator features for intelligence layer.

    This adapter returns simple aggregates (recent mean, latest value)
    for active indicators linked to a sector.
    """
    try:
        from .models import IndicatorValue
        # naive implementation: return empty if models not accessible
        vals = IndicatorValue.objects.filter(indicator__sector_id=sector_id).order_by('-date')[:30]
        if not vals:
            return {}
        latest = vals[0].value
        # mean over sample
        vlist = [float(v.value) for v in vals if v.value is not None]
        import numpy as _np
        return {
            'indicator_latest': float(latest),
            'indicator_mean_30': float(_np.mean(vlist)) if vlist else 0.0
        }
    except Exception:
        return {}

