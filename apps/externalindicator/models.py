import uuid
from django.db import models
from django.utils import timezone


class ExternalSource(models.Model):
    """Describe an external API/source (World Bank, Central Bank, etc.)"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, unique=True)
    base_url = models.CharField(max_length=1000, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "externalindicator_external_source"

    def __str__(self) -> str:
        return self.name


class ExternalIndicator(models.Model):
    """Represents a mapped indicator from a specific external source."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    source = models.ForeignKey(ExternalSource, on_delete=models.CASCADE, related_name="indicators")
    code = models.CharField(max_length=200)  # provider-specific code
    name = models.CharField(max_length=400, blank=True)
    description = models.TextField(blank=True)
    meta = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "externalindicator_indicator"
        unique_together = ("source", "code")

    def __str__(self) -> str:
        return f"{self.source.name}: {self.code}"


class ExternalIndicatorValue(models.Model):
    """Time series value for an ExternalIndicator."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    indicator = models.ForeignKey(ExternalIndicator, on_delete=models.CASCADE, related_name="values")
    date = models.DateField()
    value = models.DecimalField(max_digits=24, decimal_places=8, null=True, blank=True)
    raw_payload = models.JSONField(default=dict, blank=True)
    retrieved_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "externalindicator_indicator_value"
        ordering = ("indicator", "date")
        unique_together = ("indicator", "date")

    def __str__(self) -> str:
        return f"{self.indicator} {self.date} = {self.value}"


class ProviderMapping(models.Model):
    """Map external provider indicators to internal `Indicator` codes used by forecasting."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    source = models.ForeignKey(ExternalSource, on_delete=models.CASCADE, related_name="mappings")
    external_code = models.CharField(max_length=400, help_text="Code or endpoint identifier from the external provider")
    # target indicator FK may be null if mapping is not yet linked
    target_indicator = models.ForeignKey("indicators.Indicator", on_delete=models.SET_NULL, null=True, blank=True, related_name="external_mappings")
    date_key = models.CharField(max_length=128, default="date", help_text="JSON key/path for the date field in provider payloads")
    value_key = models.CharField(max_length=128, default="value", help_text="JSON key/path for the value field in provider payloads")
    config = models.JSONField(default=dict, blank=True, help_text="Optional provider-specific mapping config")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "externalindicator_provider_mapping"
        unique_together = ("source", "external_code")

    def __str__(self) -> str:
        target = self.target_indicator.code if self.target_indicator else "(unmapped)"
        return f"{self.source.name}:{self.external_code} -> {target}"
