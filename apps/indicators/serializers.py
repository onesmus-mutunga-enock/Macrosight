from rest_framework import serializers

from .models import Indicator, IndicatorVersion


class IndicatorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Indicator
        fields = [
            "id",
            "code",
            "name",
            "description",
            "source",
            "is_active",
            "metadata",
            "created_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_by", "created_at", "updated_at"]


class IndicatorVersionSerializer(serializers.ModelSerializer):
    indicator = serializers.PrimaryKeyRelatedField(queryset=Indicator.objects.all())

    class Meta:
        model = IndicatorVersion
        fields = [
            "id",
            "indicator",
            "version_label",
            "ingestion_timestamp",
            "source",
            "quality_score",
            "payload_metadata",
        ]
        read_only_fields = ["id", "ingestion_timestamp"]

