from rest_framework import serializers
from .models import AgriculturalInput, AgriculturalInputValue


class AgriculturalInputSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgriculturalInput
        fields = [
            "id",
            "name",
            "type",
            "sector",
            "unit",
            "description",
            "is_active",
            "created_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_by", "created_at", "updated_at"]


class AgriculturalInputValueSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgriculturalInputValue
        fields = [
            "id",
            "input",
            "date",
            "value",
            "unit_price",
            "total_cost",
        ]
        read_only_fields = ["id"]