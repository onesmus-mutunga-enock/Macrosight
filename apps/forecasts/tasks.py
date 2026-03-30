from celery import shared_task

from apps.audit.services import log_audit_event

from .models import Forecast, ForecastSchedule


@shared_task
def run_forecast_task(forecast_id: str) -> None:
    """
    Lightweight stub for asynchronous forecast computation.
    In later phases this will orchestrate ML models and data retrieval.
    """
    try:
        forecast = Forecast.objects.get(pk=forecast_id)
    except Forecast.DoesNotExist:
        return

    # Stubbed computation: simply mark as COMPLETED and attach placeholder diagnostics.
    forecast.status = Forecast.Status.COMPLETED
    forecast.diagnostics = {
        "engine": "stub",
        "message": "Forecast computed via stub task.",
    }
    forecast.save(update_fields=["status", "diagnostics"])

    log_audit_event(
        actor=forecast.created_by,
        action="forecast.compute.completed",
        entity_type="Forecast",
        entity_id=forecast.pk,
        request=None,
        metadata={"diagnostics": forecast.diagnostics},
    )


@shared_task
def run_forecast_schedule(schedule_id: str) -> None:
    """
    Stub orchestration for running a single schedule.
    In a full implementation this would evaluate schedule_spec and create
    new Forecast instances based on template definitions.
    """
    try:
        schedule = ForecastSchedule.objects.get(pk=schedule_id)
    except ForecastSchedule.DoesNotExist:
        return

    # No-op for now; orchestration logic will be added later.
    log_audit_event(
        actor=None,
        action="forecast.schedule.run",
        entity_type="ForecastSchedule",
        entity_id=schedule.pk,
        request=None,
        metadata={"schedule_spec": schedule.schedule_spec},
    )

