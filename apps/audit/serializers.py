from rest_framework import serializers
from .models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = [
            "id",
            "actor",
            "actor_role_code",
            "action",
            "entity_type",
            "entity_id",
            "request_method",
            "request_path",
            "correlation_id",
            "ip_address",
            "metadata",
            "timestamp",
        ]
        read_only_fields = ["id", "timestamp"]