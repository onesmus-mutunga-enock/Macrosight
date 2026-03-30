import uuid
from django.db import models
from apps.sectors.models import Sector
from apps.users.models import User


class ScenarioDefinition(models.Model):
    """
    Core scenario definition for economic simulations.
    """

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        ACTIVE = "ACTIVE", "Active"
        INACTIVE = "INACTIVE", "Inactive"
        ARCHIVED = "ARCHIVED", "Archived"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.DRAFT)
    sector = models.ForeignKey(
        Sector,
        on_delete=models.PROTECT,
        related_name="scenario_definitions",
    )
    type = models.CharField(
        max_length=64,
        help_text="Scenario type (e.g. 'baseline', 'stress_test', 'what_if').",
    )
    assumptions = models.JSONField(
        default=dict,
        blank=True,
        help_text="Scenario assumptions and parameters.",
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional scenario metadata.",
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="created_scenario_definitions",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "scenarios_scenario_definition"
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"{self.name} ({self.sector.code})"


class ScenarioVersion(models.Model):
    """
    Versioned implementation of a scenario for simulation purposes.
    """

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        ACTIVE = "ACTIVE", "Active"
        INACTIVE = "INACTIVE", "Inactive"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    scenario_definition = models.ForeignKey(
        ScenarioDefinition,
        on_delete=models.CASCADE,
        related_name="versions",
    )
    version_label = models.CharField(
        max_length=64,
        help_text="Version label (e.g. 'v1.0', '2025-01').",
    )
    description = models.TextField(blank=True)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.DRAFT)
    implementation = models.JSONField(
        default=dict,
        blank=True,
        help_text="Scenario implementation details for simulations.",
    )
    assumptions = models.JSONField(
        default=dict,
        blank=True,
        help_text="Assumptions underlying this scenario version.",
    )
    effective_date = models.DateField()
    expiry_date = models.DateField(null=True, blank=True)

    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="created_scenario_versions",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "scenarios_scenario_version"
        ordering = ("-created_at",)
        unique_together = ("scenario_definition", "version_label")

    def __str__(self) -> str:
        return f"{self.scenario_definition.name} / {self.version_label}"


class Scenario(models.Model):
    """
    Executed scenario simulation result.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    scenario_version = models.ForeignKey(ScenarioVersion, on_delete=models.CASCADE)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    run_date = models.DateTimeField(auto_now_add=True)
    results = models.JSONField(default=dict)
    status = models.CharField(max_length=32, default="COMPLETED")


class Simulation(models.Model):
    """
    Simulation execution record.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    scenario = models.ForeignKey(Scenario, on_delete=models.CASCADE)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    run_date = models.DateTimeField(auto_now_add=True)
    parameters = models.JSONField(default=dict)
    results = models.JSONField(default=dict)


class ScenarioComparison(models.Model):
    """
    Comparison between multiple scenarios.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    scenarios = models.ManyToManyField(Scenario)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    comparison_metrics = models.JSONField(default=dict)
