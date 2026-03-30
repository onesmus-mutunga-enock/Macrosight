import uuid

from django.db import models

from apps.forecasts.models import Forecast


class Dataset(models.Model):
    """
    Logical training dataset built from approved data sources.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    # Snapshot / policy / sector scope etc. encoded as JSON to stay DB-portable.
    definition = models.JSONField(
        default=dict,
        blank=True,
        help_text="Declarative description of dataset inputs (snapshots, sectors, policies, date ranges).",
    )

    created_by = models.ForeignKey(
        "users.User",
        on_delete=models.PROTECT,
        related_name="created_datasets",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ml_dataset"
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return self.name


class FeatureSet(models.Model):
    """
    Feature engineering artifacts built from Datasets.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    dataset = models.ForeignKey(
        Dataset,
        on_delete=models.CASCADE,
        related_name="feature_sets",
    )

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    # JSON structure describing transformations (lag features, rolling averages, etc.)
    spec = models.JSONField(
        default=dict,
        blank=True,
        help_text="Feature engineering specification and metadata.",
    )

    created_by = models.ForeignKey(
        "users.User",
        on_delete=models.PROTECT,
        related_name="created_feature_sets",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ml_feature_set"
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return self.name


class ModelRegistry(models.Model):
    """
    Registered ML models and their metadata (not weights).
    """

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        CANDIDATE = "CANDIDATE", "Candidate"
        ACTIVE = "ACTIVE", "Active"
        DEPRECATED = "DEPRECATED", "Deprecated"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    algorithm = models.CharField(
        max_length=128,
        help_text="Algorithm identifier (e.g., XGBoost, LSTM, TFT).",
    )

    status = models.CharField(
        max_length=32,
        choices=Status.choices,
        default=Status.DRAFT,
    )

    # Pointers to data/feature lineage for the "current" model version.
    dataset = models.ForeignKey(
        Dataset,
        on_delete=models.PROTECT,
        related_name="models",
    )
    feature_set = models.ForeignKey(
        FeatureSet,
        on_delete=models.PROTECT,
        related_name="models",
    )

    # Training configuration and hyperparameters
    train_config = models.JSONField(
        default=dict,
        blank=True,
        help_text="Training configuration, hyperparameters, and preprocessing options.",
    )

    # Code / artifact references; storage-specific details live elsewhere.
    artifact_path = models.CharField(
        max_length=512,
        blank=True,
        help_text="Reference to persisted model artifacts (e.g. object storage path).",
    )
    code_version = models.CharField(
        max_length=128,
        blank=True,
        help_text="Git/SemVer identifier of training code.",
    )

    created_by = models.ForeignKey(
        "users.User",
        on_delete=models.PROTECT,
        related_name="created_models",
    )
    promoted_by = models.ForeignKey(
        "users.User",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="promoted_models",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    promoted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "ml_model_registry"
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"{self.name} ({self.status})"


class TrainingJob(models.Model):
    """
    Asynchronous training job, backed by Celery tasks.
    """

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        RUNNING = "RUNNING", "Running"
        COMPLETED = "COMPLETED", "Completed"
        FAILED = "FAILED", "Failed"
        CANCELLED = "CANCELLED", "Cancelled"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    model = models.ForeignKey(
        ModelRegistry,
        on_delete=models.CASCADE,
        related_name="training_jobs",
    )
    dataset = models.ForeignKey(
        Dataset,
        on_delete=models.PROTECT,
        related_name="training_jobs",
    )
    feature_set = models.ForeignKey(
        FeatureSet,
        on_delete=models.PROTECT,
        related_name="training_jobs",
    )

    status = models.CharField(
        max_length=32,
        choices=Status.choices,
        default=Status.PENDING,
    )

    # HPO vs single-run flag
    is_hpo = models.BooleanField(default=False)

    # Hyperparameters / search spaces expressed as JSON
    hyperparameters = models.JSONField(
        default=dict,
        blank=True,
        help_text="Hyperparameters or search space definition.",
    )

    # Lightweight metrics summary
    metrics = models.JSONField(
        default=dict,
        blank=True,
        help_text="Aggregated training/validation metrics.",
    )

    # Execution metadata
    celery_task_id = models.CharField(max_length=255, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    created_by = models.ForeignKey(
        "users.User",
        on_delete=models.PROTECT,
        related_name="created_training_jobs",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ml_training_job"
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"{self.id} ({self.status})"


class MLDataset(models.Model):
    """
    Concrete materialized dataset used for ML training, scoped by snapshot and sector.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    snapshot = models.ForeignKey(
        "system.DataSnapshot",
        on_delete=models.PROTECT,
        related_name="ml_datasets",
    )
    sector = models.ForeignKey(
        "sectors.Sector",
        on_delete=models.PROTECT,
        related_name="ml_datasets",
    )

    start_date = models.DateField()
    end_date = models.DateField()

    created_by = models.ForeignKey(
        "users.User",
        on_delete=models.PROTECT,
        related_name="created_ml_datasets",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ml_ml_dataset"
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"{self.sector.code} {self.start_date}..{self.end_date}"


class MLDatasetRow(models.Model):
    """
    Denormalized per-date feature row for ML training.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    dataset = models.ForeignKey(
        MLDataset,
        on_delete=models.CASCADE,
        related_name="rows",
    )
    date = models.DateField()

    sales = models.FloatField(null=True, blank=True)
    price = models.FloatField(null=True, blank=True)
    inflation = models.FloatField(null=True, blank=True)
    fuel_cost = models.FloatField(null=True, blank=True)
    tax_rate = models.FloatField(null=True, blank=True)

    other_features = models.JSONField(
        default=dict,
        blank=True,
        help_text="JSON bag for additional features.",
    )

    class Meta:
        db_table = "ml_ml_dataset_row"
        ordering = ("dataset", "date")
        indexes = [
            models.Index(fields=["dataset", "date"], name="ml_dsrw_dset_date_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.dataset_id} / {self.date}"


class ForecastResult(models.Model):
    """
    Forecast predictions with confidence intervals.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    forecast = models.ForeignKey(
        Forecast,
        on_delete=models.CASCADE,
        related_name="results",
    )
    
    model = models.ForeignKey(
        ModelRegistry,
        on_delete=models.CASCADE,
        related_name="forecast_results",
    )

    # Forecast values
    predicted_value = models.DecimalField(max_digits=20, decimal_places=6)
    confidence_lower = models.DecimalField(max_digits=20, decimal_places=6, null=True, blank=True)
    confidence_upper = models.DecimalField(max_digits=20, decimal_places=6, null=True, blank=True)
    
    # Forecast metadata
    prediction_date = models.DateField()
    horizon_months = models.IntegerField()
    
    # Model performance metrics for this specific forecast
    model_metrics = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ml_forecast_result"
        ordering = ("-prediction_date",)
        unique_together = ["forecast", "model", "prediction_date"]

    def __str__(self) -> str:
        return f"Forecast {self.forecast.id} - {self.prediction_date} - {self.predicted_value}"


class ModelExplainability(models.Model):
    """
    Econometric analysis and explainability results.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    model = models.ForeignKey(
        ModelRegistry,
        on_delete=models.CASCADE,
        related_name="explainability_results",
    )

    # Coefficient analysis
    coefficients = models.JSONField(default=dict, blank=True)
    p_values = models.JSONField(default=dict, blank=True)
    confidence_intervals = models.JSONField(default=dict, blank=True)
    
    # Model statistics
    r_squared = models.FloatField(null=True, blank=True)
    adjusted_r_squared = models.FloatField(null=True, blank=True)
    f_statistic = models.FloatField(null=True, blank=True)
    f_p_value = models.FloatField(null=True, blank=True)
    
    # Diagnostic tests
    durbin_watson = models.FloatField(null=True, blank=True)
    jarque_bera = models.FloatField(null=True, blank=True)
    jarque_bera_p_value = models.FloatField(null=True, blank=True)
    
    # Feature importance (if applicable)
    feature_importance = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ml_model_explainability"
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"Explainability for {self.model.name} v{self.model.version}"


