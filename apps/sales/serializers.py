from rest_framework import serializers
from .models import Sale, SaleSummary


class SaleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sale
        fields = [
            "id",
            "product",
            "sector",
            "date",
            "units_sold",
            "revenue",
            "price",
            "region",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class SaleSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = SaleSummary
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]