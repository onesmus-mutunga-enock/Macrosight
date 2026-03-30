import uuid

from django.db import models

from apps.indicators.models import IndicatorVersion
from apps.policies.models import PolicyVersion
from apps.system.models import DataSnapshot


class Forecast(models.Model):
    """
    Governance-aware forecast entity.
    Actual numeric results are intentionally not modeled yet; they will be
    attached via domain-specific result tables or external stores in later phases.
    """

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        RUNNING = "RUNNING", "Running"
        COMPLETED = "COMPLETED", "Completed"
        FAILED = "FAILED", "Failed"
        SUBMITTED = "SUBMITTED", "Submitted for approval"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"
        INVALIDATED = "INVALIDATED", "Invalidated"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    status = models.CharField(
        max_length=32,
        choices=Status.choices,
        default=Status.DRAFT,
    )

    # Snapshot / policy / indicator references
    snapshot = models.ForeignKey(
        DataSnapshot,
        on_delete=models.PROTECT,
        related_name="forecasts",
    )
    policy_version = models.ForeignKey(
        PolicyVersion,
        on_delete=models.PROTECT,
        related_name="forecasts",
    )
    indicator_version = models.ForeignKey(
        IndicatorVersion,
        on_delete=models.PROTECT,
        related_name="forecasts",
    )

    # Analyst assumptions & notes
    assumptions = models.JSONField(
        default=dict,
        blank=True,
        help_text="Analyst assumptions and notes backing this forecast.",
    )

    # Governance actors
    created_by = models.ForeignKey(
        "users.User",
        on_delete=models.PROTECT,
        related_name="created_forecasts",
    )
    approved_by = models.ForeignKey(
        "users.User",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="approved_forecasts",
    )

    # Lifecycle timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    generated_at = models.DateTimeField(null=True, blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    rejected_at = models.DateTimeField(null=True, blank=True)
    invalidated_at = models.DateTimeField(null=True, blank=True)

    # Accuracy & diagnostics (lightweight, JSON-form; heavy analytics live elsewhere)
    accuracy_summary = models.JSONField(
        default=dict,
        blank=True,
        help_text="Aggregated accuracy metrics for this forecast.",
    )
    diagnostics = models.JSONField(
        default=dict,
        blank=True,
        help_text="Miscellaneous diagnostics (e.g. runtime info, warnings).",
    )

    class Meta:
        db_table = "forecasts_forecast"
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"{self.name} ({self.status})"


class ForecastSchedule(models.Model):
    """
    Represents a scheduled forecast job as per the Forecast Scheduling & Orchestration API.
    """

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        PAUSED = "PAUSED", "Paused"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.ACTIVE,
    )

    # Simple cron-like or interval expression; interpreted by orchestration layer.
    schedule_spec = models.JSONField(
        default=dict,
        blank=True,
        help_text="Schedule definition (e.g. cron, interval, sector scope).",
    )

    # Template for forecasts this schedule should trigger
    template = models.JSONField(
        default=dict,
        blank=True,
        help_text="Template payload for forecast generation requests.",
    )

    last_run_at = models.DateTimeField(null=True, blank=True)
    next_run_at = models.DateTimeField(null=True, blank=True)

    created_by = models.ForeignKey(
        "users.User",
        on_delete=models.PROTECT,
        related_name="created_forecast_schedules",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "forecasts_schedule"
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return self.name

