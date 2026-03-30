from rest_framework import serializers

from .models import Dataset, FeatureSet, ModelRegistry, TrainingJob, ForecastResult, ModelExplainability


class DatasetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dataset
        fields = [
            "id",
            "name",
            "description",
            "definition",
            "created_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_by", "created_at", "updated_at"]


class FeatureSetSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeatureSet
        fields = [
            "id",
            "dataset",
            "name",
            "description",
            "spec",
            "created_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_by", "created_at", "updated_at"]


class ModelRegistrySerializer(serializers.ModelSerializer):
    class Meta:
        model = ModelRegistry
        fields = [
            "id",
            "name",
            "description",
            "algorithm",
            "status",
            "dataset",
            "feature_set",
            "train_config",
            "artifact_path",
            "code_version",
            "created_by",
            "promoted_by",
            "created_at",
            "updated_at",
            "promoted_at",
        ]
        read_only_fields = [
            "id",
            "status",
            "created_by",
            "promoted_by",
            "created_at",
            "updated_at",
            "promoted_at",
        ]


class TrainingJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainingJob
        fields = [
            "id",
            "model",
            "dataset",
            "feature_set",
            "status",
            "is_hpo",
            "hyperparameters",
            "metrics",
            "celery_task_id",
            "started_at",
            "completed_at",
            "created_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "status",
            "metrics",
            "celery_task_id",
            "started_at",
            "completed_at",
            "created_by",
            "created_at",
            "updated_at",
        ]


class TrainingJobCreateSerializer(serializers.Serializer):
    """
    Explicit schema for training job creation.
    """

    model = serializers.PrimaryKeyRelatedField(queryset=ModelRegistry.objects.all())
    dataset = serializers.PrimaryKeyRelatedField(queryset=Dataset.objects.all())
    feature_set = serializers.PrimaryKeyRelatedField(queryset=FeatureSet.objects.all())
    is_hpo = serializers.BooleanField(default=False)
    hyperparameters = serializers.JSONField(required=False)


class ForecastResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = ForecastResult
        fields = '__all__'


class ModelExplainabilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = ModelExplainability
        fields = '__all__'

