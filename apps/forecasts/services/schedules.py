from typing import Any, Dict, Optional

from django.db import transaction
from django.http import HttpRequest
from django.utils import timezone

from apps.audit.services import log_audit_event

from ..models import ForecastSchedule
from ..tasks import run_forecast_schedule


@transaction.atomic
def create_schedule(
    *,
    actor,
    data: Dict[str, Any],
    request: Optional[HttpRequest] = None,
) -> ForecastSchedule:
    schedule = ForecastSchedule.objects.create(
        name=data["name"],
        description=data.get("description", ""),
        schedule_spec=data.get("schedule_spec", {}) or {},
        template=data.get("template", {}) or {},
        created_by=actor,
    )

    log_audit_event(
        actor=actor,
        action="forecast.schedule.create",
        entity_type="ForecastSchedule",
        entity_id=schedule.pk,
        request=request,
        metadata={
            "schedule_spec": schedule.schedule_spec,
            "template": schedule.template,
        },
    )
    return schedule


@transaction.atomic
def pause_schedule(
    *,
    actor,
    schedule: ForecastSchedule,
    request: Optional[HttpRequest] = None,
) -> ForecastSchedule:
    before_status = schedule.status
    schedule.status = ForecastSchedule.Status.PAUSED
    schedule.save(update_fields=["status"])

    log_audit_event(
        actor=actor,
        action="forecast.schedule.pause",
        entity_type="ForecastSchedule",
        entity_id=schedule.pk,
        request=request,
        metadata={"before_status": before_status, "after_status": schedule.status},
    )
    return schedule


@transaction.atomic
def resume_schedule(
    *,
    actor,
    schedule: ForecastSchedule,
    request: Optional[HttpRequest] = None,
) -> ForecastSchedule:
    before_status = schedule.status
    schedule.status = ForecastSchedule.Status.ACTIVE
    schedule.save(update_fields=["status"])

    log_audit_event(
        actor=actor,
        action="forecast.schedule.resume",
        entity_type="ForecastSchedule",
        entity_id=schedule.pk,
        request=request,
        metadata={"before_status": before_status, "after_status": schedule.status},
    )
    return schedule


def orchestrate_schedules(*, actor, request: Optional[HttpRequest] = None) -> None:
    """
    Stub orchestration: enqueue Celery tasks for all ACTIVE schedules.
    """
    active_schedules = ForecastSchedule.objects.filter(
        status=ForecastSchedule.Status.ACTIVE
    )
    for schedule in active_schedules:
        run_forecast_schedule.delay(str(schedule.pk))
        log_audit_event(
            actor=actor,
            action="forecast.schedule.orchestrate",
            entity_type="ForecastSchedule",
            entity_id=schedule.pk,
            request=request,
            metadata={"schedule_spec": schedule.schedule_spec},
        )

