from typing import Any, Dict, Optional

from django.db import transaction
from django.http import HttpRequest
from django.utils import timezone

from apps.audit.services import log_audit_event

from ..models import Forecast
from ..tasks import run_forecast_task


@transaction.atomic
def create_forecast_from_request(
    *,
    actor,
    payload: Dict[str, Any],
    request: Optional[HttpRequest] = None,
) -> Forecast:
    forecast = Forecast.objects.create(
        name=payload["name"],
        description=payload.get("description", ""),
        snapshot=payload["snapshot"],
        policy_version=payload["policy_version"],
        indicator_version=payload["indicator_version"],
        assumptions=payload.get("assumptions", {}) or {},
        status=Forecast.Status.RUNNING,
        created_by=actor,
        generated_at=timezone.now(),
    )

    log_audit_event(
        actor=actor,
        action="forecast.generate",
        entity_type="Forecast",
        entity_id=forecast.pk,
        request=request,
        metadata={
            "snapshot_id": str(forecast.snapshot_id),
            "policy_version_id": str(forecast.policy_version_id),
            "indicator_version_id": str(forecast.indicator_version_id),
        },
    )

    # Trigger asynchronous computation
    run_forecast_task.delay(str(forecast.pk))

    return forecast


@transaction.atomic
def submit_forecast(*, actor, forecast: Forecast, request: Optional[HttpRequest] = None) -> Forecast:
    if forecast.created_by_id != actor.id:
        # In a stricter system, we might allow submission by supervisors; for now require creator.
        raise PermissionError("Only the creator may submit a forecast.")

    before_status = forecast.status
    forecast.status = Forecast.Status.SUBMITTED
    forecast.submitted_at = timezone.now()
    forecast.save(update_fields=["status", "submitted_at"])

    log_audit_event(
        actor=actor,
        action="forecast.submit",
        entity_type="Forecast",
        entity_id=forecast.pk,
        request=request,
        metadata={"before_status": before_status, "after_status": forecast.status},
    )
    return forecast


@transaction.atomic
def approve_forecast(*, actor, forecast: Forecast, request: Optional[HttpRequest] = None) -> Forecast:
    before_status = forecast.status
    forecast.status = Forecast.Status.APPROVED
    forecast.approved_by = actor
    forecast.approved_at = timezone.now()
    forecast.rejected_at = None
    forecast.invalidated_at = None
    forecast.save(update_fields=["status", "approved_by", "approved_at", "rejected_at", "invalidated_at"])

    log_audit_event(
        actor=actor,
        action="forecast.approve",
        entity_type="Forecast",
        entity_id=forecast.pk,
        request=request,
        metadata={"before_status": before_status, "after_status": forecast.status},
    )
    return forecast


@transaction.atomic
def reject_forecast(*, actor, forecast: Forecast, request: Optional[HttpRequest] = None) -> Forecast:
    before_status = forecast.status
    forecast.status = Forecast.Status.REJECTED
    forecast.rejected_at = timezone.now()
    forecast.save(update_fields=["status", "rejected_at"])

    log_audit_event(
        actor=actor,
        action="forecast.reject",
        entity_type="Forecast",
        entity_id=forecast.pk,
        request=request,
        metadata={"before_status": before_status, "after_status": forecast.status},
    )
    return forecast


@transaction.atomic
def invalidate_forecast(*, actor, forecast: Forecast, request: Optional[HttpRequest] = None) -> Forecast:
    before_status = forecast.status
    forecast.status = Forecast.Status.INVALIDATED
    forecast.invalidated_at = timezone.now()
    forecast.save(update_fields=["status", "invalidated_at"])

    log_audit_event(
        actor=actor,
        action="forecast.invalidate",
        entity_type="Forecast",
        entity_id=forecast.pk,
        request=request,
        metadata={"before_status": before_status, "after_status": forecast.status},
    )
    return forecast


@transaction.atomic
def record_actuals_and_update_accuracy(
    *,
    actor,
    forecast: Forecast,
    actuals_payload: Dict[str, Any],
    request: Optional[HttpRequest] = None,
) -> Forecast:
    """
    Stub for actuals ingestion and accuracy computation.
    Stores the payload in diagnostics, and computes a fake RMSE/MAPE.
    """
    accuracy = {
        "rmse": 0.0,
        "mape": 0.0,
        "mae": 0.0,
        "notes": "Stub accuracy metrics; real implementation will use ML outputs.",
    }
    forecast.accuracy_summary = accuracy
    diagnostics = forecast.diagnostics or {}
    diagnostics.setdefault("actuals_history", []).append(actuals_payload)
    forecast.diagnostics = diagnostics
    forecast.save(update_fields=["accuracy_summary", "diagnostics"])

    log_audit_event(
        actor=actor,
        action="forecast.actuals.ingested",
        entity_type="Forecast",
        entity_id=forecast.pk,
        request=request,
        metadata={"actuals": actuals_payload, "accuracy": accuracy},
    )

    return forecast


def compute_delta_stub(*, base: Forecast, other: Forecast) -> Dict[str, Any]:
    """
    Stub comparison between two forecasts.
    """
    return {
        "base_id": str(base.pk),
        "other_id": str(other.pk),
        "summary": "Delta comparison is stubbed; real implementation will compute scenario deltas.",
    }

