from rest_framework import serializers

from apps.indicators.models import IndicatorVersion
from apps.policies.models import PolicyVersion
from apps.system.models import DataSnapshot

from .models import Forecast, ForecastSchedule


class ForecastSerializer(serializers.ModelSerializer):
    snapshot = serializers.PrimaryKeyRelatedField(queryset=DataSnapshot.objects.all())
    policy_version = serializers.PrimaryKeyRelatedField(queryset=PolicyVersion.objects.all())
    indicator_version = serializers.PrimaryKeyRelatedField(queryset=IndicatorVersion.objects.all())

    class Meta:
        model = Forecast
        fields = [
            "id",
            "name",
            "description",
            "status",
            "snapshot",
            "policy_version",
            "indicator_version",
            "assumptions",
            "created_by",
            "approved_by",
            "created_at",
            "updated_at",
            "generated_at",
            "submitted_at",
            "approved_at",
            "rejected_at",
            "invalidated_at",
            "accuracy_summary",
            "diagnostics",
        ]
        read_only_fields = [
            "id",
            "status",
            "created_by",
            "approved_by",
            "created_at",
            "updated_at",
            "generated_at",
            "submitted_at",
            "approved_at",
            "rejected_at",
            "invalidated_at",
            "accuracy_summary",
            "diagnostics",
        ]


class ForecastGenerateRequestSerializer(serializers.Serializer):
    """
    Explicit schema for forecast generation requests to avoid over-exposing the model.
    """

    name = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, allow_blank=True)
    snapshot = serializers.PrimaryKeyRelatedField(queryset=DataSnapshot.objects.all())
    policy_version = serializers.PrimaryKeyRelatedField(queryset=PolicyVersion.objects.all())
    indicator_version = serializers.PrimaryKeyRelatedField(queryset=IndicatorVersion.objects.all())
    assumptions = serializers.JSONField(required=False)


class ForecastScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ForecastSchedule
        fields = [
            "id",
            "name",
            "description",
            "status",
            "schedule_spec",
            "template",
            "last_run_at",
            "next_run_at",
            "created_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "status",
            "last_run_at",
            "next_run_at",
            "created_by",
            "created_at",
            "updated_at",
        ]

