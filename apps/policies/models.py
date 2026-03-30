import uuid
from django.db import models
from apps.sectors.models import Sector
from apps.users.models import User
from apps.governance.models import SUPER_ADMIN  


class Policy(models.Model):
    """
    Core policy definition for economic impact analysis.
    """

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        ACTIVE = "ACTIVE", "Active"
        INACTIVE = "INACTIVE", "Inactive"
        ARCHIVED = "ARCHIVED", "Archived"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    code = models.CharField(
        max_length=64,
        unique=True,
        help_text="Stable code for the policy (e.g. 'VAT_CHANGE_2025').",
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.DRAFT)
    sector = models.ForeignKey(
        Sector,
        on_delete=models.PROTECT,
        related_name="policies",
    )
    type = models.CharField(
        max_length=64,
        help_text="Policy type (e.g. 'tax', 'subsidy', 'regulation').",
    )
    effective_date = models.DateField()
    expiry_date = models.DateField(null=True, blank=True)
    parameters = models.JSONField(
        default=dict,
        blank=True,
        help_text="Policy-specific parameters and configuration.",
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional policy metadata.",
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="created_policies",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "policies_policy"
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"{self.code} - {self.name}"


class PolicyVersion(models.Model):
    """
    Versioned implementation of a policy for simulation purposes.
    """

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        ACTIVE = "ACTIVE", "Active"
        INACTIVE = "INACTIVE", "Inactive"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    policy = models.ForeignKey(
        Policy,
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
        help_text="Policy implementation details for simulations.",
    )
    assumptions = models.JSONField(
        default=dict,
        blank=True,
        help_text="Assumptions underlying this policy version.",
    )
    effective_date = models.DateField()
    expiry_date = models.DateField(null=True, blank=True)

    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="created_policy_versions",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "policies_policy_version"
        ordering = ("-created_at",)
        unique_together = ("policy", "version_label")

    def __str__(self) -> str:
        return f"{self.policy.code} / {self.version_label}"


class PolicySimulation(models.Model):
    """
    Simulation run using a specific PolicyVersion against economic baseline.
    """

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        RUNNING = "RUNNING", "Running"
        COMPLETED = "COMPLETED", "Completed"
        FAILED = "FAILED", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    policy_version = models.ForeignKey(
        PolicyVersion,
        on_delete=models.CASCADE,
        related_name="simulations",
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    baseline_snapshot = models.CharField(max_length=36, help_text="DataSnapshot UUID")
    parameters = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.PENDING)
    results = models.JSONField(default=dict, blank=True, null=True)

    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="policy_simulations",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "policies_policy_simulation"
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.policy_version} - {self.name}"


class PolicyImpactAnalysis(models.Model):
    """
    Analysis of simulation results vs baseline.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    simulation = models.ForeignKey(
        PolicySimulation,
        on_delete=models.CASCADE,
        related_name="analyses",
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    sectors = models.ManyToManyField(Sector, blank=True)
    metrics = models.JSONField(default=dict, blank=True)
    key_findings = models.TextField(blank=True)
    recommendations = models.TextField(blank=True)

    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="policy_analyses",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "policies_policy_impact_analysis"
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.simulation} - {self.name}"


class PolicySimulationComparison(models.Model):
    """
    Comparison between multiple simulations / baselines.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    simulations = models.ManyToManyField(
        PolicySimulation,
        related_name="comparisons",
    )
    baseline_simulation = models.ForeignKey(
        PolicySimulation,
        on_delete=models.CASCADE,
        related_name="baseline_comparisons",
    )
    comparison_metrics = models.JSONField(default=dict, blank=True)
    key_differences = models.TextField(blank=True)

    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="policy_comparisons",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "policies_policy_simulation_comparison"
        ordering = ("-created_at",)

    def __str__(self):
        return self.name

