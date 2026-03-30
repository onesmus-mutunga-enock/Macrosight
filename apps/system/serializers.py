from rest_framework import serializers

from .models import DataSnapshot


class DataSnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataSnapshot
        fields = [
            "id",
            "name",
            "description",
            "status",
            "context",
            "content_hash",
            "created_by",
            "locked_by",
            "frozen_at",
            "locked_at",
            "metadata",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "status",
            "content_hash",
            "created_by",
            "locked_by",
            "frozen_at",
            "locked_at",
            "created_at",
            "updated_at",
        ]

