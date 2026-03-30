from rest_framework import serializers
from .models import ExternalSource, ExternalIndicator, ExternalIndicatorValue


class ExternalSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExternalSource
        fields = ["id", "name", "base_url", "metadata", "created_at"]
        read_only_fields = ["id", "created_at"]


class ExternalIndicatorSerializer(serializers.ModelSerializer):
    # Provide read nested representation and accept a writeable PK via `source_id`.
    source = ExternalSourceSerializer(read_only=True)
    source_id = serializers.PrimaryKeyRelatedField(
        source="source", queryset=ExternalSource.objects.all(), write_only=True, required=False
    )

    class Meta:
        model = ExternalIndicator
        fields = ["id", "source", "source_id", "code", "name", "description", "meta", "created_at"]
        read_only_fields = ["id", "created_at"]


class ExternalIndicatorValueSerializer(serializers.ModelSerializer):
    # nested read representation; allow writes with `indicator_id` PK
    indicator = ExternalIndicatorSerializer(read_only=True)
    indicator_id = serializers.PrimaryKeyRelatedField(
        source="indicator", queryset=ExternalIndicator.objects.all(), write_only=True, required=False
    )

    class Meta:
        model = ExternalIndicatorValue
        fields = ["id", "indicator", "indicator_id", "date", "value", "raw_payload", "retrieved_at"]
        read_only_fields = ["id", "retrieved_at"]

    def validate_value(self, value):
        # allow null/blank decimals but ensure numeric when provided
        if value is None:
            return value
        try:
            float(value)
        except Exception:
            raise serializers.ValidationError("Value must be numeric")
        return value
