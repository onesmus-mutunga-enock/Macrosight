import uuid

from django.db import models


class Indicator(models.Model):
    """
    External indicator definition (e.g., CPI, GDP growth).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    code = models.CharField(
        max_length=64,
        unique=True,
        help_text="Stable code for the indicator (e.g. 'CPI').",
    )
    name = models.CharField(max_length=255)
    unit = models.CharField(
        max_length=64,
        blank=True,
        help_text="Unit of measurement (e.g. '%', 'index').",
    )
    description = models.TextField(blank=True)

    source = models.CharField(
        max_length=255,
        blank=True,
        help_text="Primary data source name (e.g. statistics bureau).",
    )
    is_active = models.BooleanField(default=True)

    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional attributes, e.g. units, frequency.",
    )

    created_by = models.ForeignKey(
        "users.User",
        on_delete=models.PROTECT,
        related_name="created_indicators",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "indicators_indicator"
        ordering = ("code",)

    def __str__(self) -> str:
        return f"{self.code} - {self.name}"


class IndicatorVersion(models.Model):
    """
    Concrete ingestion of indicator data from a specific source/run.
    Powers ingestion logs and quality reports.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    indicator = models.ForeignKey(
        Indicator,
        on_delete=models.CASCADE,
        related_name="versions",
    )

    version_label = models.CharField(
        max_length=64,
        help_text="Free-form version label (e.g. '2025-01-release-1').",
    )

    ingestion_timestamp = models.DateTimeField(auto_now_add=True)
    source = models.CharField(max_length=255, blank=True)

    quality_score = models.FloatField(
        null=True,
        blank=True,
        help_text="Optional quality metric (0-1 or percentage).",
    )

    payload_metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Metadata about the ingested dataset, not the raw data itself.",
    )

    class Meta:
        db_table = "indicators_indicator_version"
        ordering = ("-ingestion_timestamp",)

    def __str__(self) -> str:
        return f"{self.indicator.code} / {self.version_label}"


class IndicatorValue(models.Model):
    """
    Time series values for macro indicators, versioned logically.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    indicator = models.ForeignKey(
        Indicator,
        on_delete=models.CASCADE,
        related_name="values",
    )
    date = models.DateField()
    value = models.FloatField()
    version = models.CharField(max_length=64, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "indicators_indicator_value"
        ordering = ("indicator", "date")
        indexes = [
            models.Index(fields=["indicator", "date"], name="ind_iv_ind_date_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.indicator.code} {self.date} = {self.value}"

