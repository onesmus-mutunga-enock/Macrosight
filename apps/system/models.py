from django.db import models
import uuid


class SystemPlaceholder(models.Model):
    """
    Placeholder model for system-level settings; full domain models
    will be added in business phases.
    """

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "system_placeholder"


class SystemConfig(models.Model):
    """
    Singleton-style configuration object backing /system/config endpoints.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    name = models.CharField(
        max_length=128,
        default="default",
        help_text="Configuration profile name (typically 'default').",
    )
    config = models.JSONField(
        default=dict,
        blank=True,
        help_text="Key/value configuration used by the platform.",
    )

    updated_by = models.ForeignKey(
        "users.User",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="updated_system_configs",
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "system_config"

    def __str__(self) -> str:
        return self.name


class DataSnapshot(models.Model):
    """
    Immutable snapshot of the data state used for forecasting / ML.

    This model captures governance-critical metadata without assuming
    any particular storage for the underlying raw data. The `context`
    field is designed to hold references to sales snapshots, indicator
    versions, policy versions, sector scope, and date ranges.
    """

    class Status(models.TextChoices):
        FROZEN = "FROZEN", "Frozen"
        LOCKED = "LOCKED", "Locked"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.FROZEN,
    )

    context = models.JSONField(
        default=dict,
        blank=True,
        help_text=(
            "Structured description of the snapshot, e.g. sales snapshot IDs, "
            "indicator version, policy version, sector scope, date range."
        ),
    )

    content_hash = models.CharField(max_length=64)

    created_by = models.ForeignKey(
        "users.User",
        on_delete=models.PROTECT,
        related_name="created_snapshots",
    )
    locked_by = models.ForeignKey(
        "users.User",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="locked_snapshots",
    )

    frozen_at = models.DateTimeField(auto_now_add=True)
    locked_at = models.DateTimeField(null=True, blank=True)

    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional governance metadata, e.g. approval references.",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "system_data_snapshot"
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"{self.name} ({self.status})"


class SystemJob(models.Model):
    """
    Lightweight representation of system/background jobs for monitoring.
    """

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        RUNNING = "RUNNING", "Running"
        PAUSED = "PAUSED", "Paused"
        COMPLETED = "COMPLETED", "Completed"
        FAILED = "FAILED", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    name = models.CharField(max_length=255)
    category = models.CharField(
        max_length=64,
        blank=True,
        help_text="Logical category, e.g. 'forecast', 'backup', 'maintenance'.",
    )
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.PENDING,
    )

    last_run_at = models.DateTimeField(null=True, blank=True)
    next_run_at = models.DateTimeField(null=True, blank=True)

    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional job information, e.g. linked schedule IDs.",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "system_job"
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"{self.name} ({self.status})"


class Alert(models.Model):
    """
    Alerts & thresholds API resource.
    """

    class Severity(models.TextChoices):
        INFO = "INFO", "Info"
        WARNING = "WARNING", "Warning"
        CRITICAL = "CRITICAL", "Critical"

    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        ACKNOWLEDGED = "ACKNOWLEDGED", "Acknowledged"
        CLOSED = "CLOSED", "Closed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    title = models.CharField(max_length=255)
    message = models.TextField()

    severity = models.CharField(
        max_length=16,
        choices=Severity.choices,
        default=Severity.INFO,
    )
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.OPEN,
    )

    threshold_config = models.JSONField(
        default=dict,
        blank=True,
        help_text="Serialized threshold definition that triggered this alert.",
    )

    created_by = models.ForeignKey(
        "users.User",
        on_delete=models.PROTECT,
        related_name="created_alerts",
    )
    acknowledged_by = models.ForeignKey(
        "users.User",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="acknowledged_alerts",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "system_alert"
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"{self.severity}: {self.title}"


