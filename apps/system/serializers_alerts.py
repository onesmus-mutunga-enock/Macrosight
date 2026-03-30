from rest_framework import serializers

from .models import Alert, SystemConfig, SystemJob


class AlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alert
        fields = [
            "id",
            "title",
            "message",
            "severity",
            "status",
            "threshold_config",
            "created_by",
            "acknowledged_by",
            "created_at",
            "acknowledged_at",
            "closed_at",
        ]
        read_only_fields = [
            "id",
            "status",
            "created_by",
            "acknowledged_by",
            "created_at",
            "acknowledged_at",
            "closed_at",
        ]


class SystemConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemConfig
        fields = ["id", "name", "config", "updated_by", "updated_at"]
        read_only_fields = ["id", "name", "updated_by", "updated_at"]


class SystemJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemJob
        fields = [
            "id",
            "name",
            "category",
            "status",
            "last_run_at",
            "next_run_at",
            "metadata",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

