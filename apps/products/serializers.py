from rest_framework import serializers
from .models import Product, ProductPlaceholder


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "description",
            "sku",
            "category",
            "unit_of_measure",
            "sector",
            "is_active",
            "created_at",
            "updated_at",
            "updated_by",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "updated_by"]


class ProductPlaceholderSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductPlaceholder
        fields = ["id", "created_at"]
        read_only_fields = ["id", "created_at"]
