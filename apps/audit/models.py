from django.db import models


class AuditLog(models.Model):
    """
    Centralized, append-only audit record for governance events.
    Intended to cover:
    - Policy lifecycle changes
    - Role & permission changes
    - Data snapshot freezes & locks
    - ML / forecasting governance (later phases)
    """

    actor = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )
    actor_role_code = models.CharField(
        max_length=64,
        blank=True,
        help_text="Primary role code of the actor at the time of the action.",
    )

    action = models.CharField(
        max_length=128,
        help_text="High-level action identifier, e.g. 'policy.update', 'role.change', 'snapshot.lock'.",
    )
    entity_type = models.CharField(
        max_length=128,
        help_text="Logical entity type, e.g. 'Policy', 'User', 'DataSnapshot'.",
    )
    entity_id = models.CharField(
        max_length=128,
        help_text="Primary identifier of the entity at the time of the action.",
    )

    request_method = models.CharField(max_length=16, blank=True)
    request_path = models.CharField(max_length=512, blank=True)
    correlation_id = models.CharField(
        max_length=64,
        blank=True,
        help_text="Per-request correlation ID injected by audit middleware.",
    )

    ip_address = models.GenericIPAddressField(null=True, blank=True)

    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Arbitrary structured payload, e.g. before/after snapshots.",
    )

    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "audit_log"
        indexes = [
            models.Index(fields=["entity_type", "entity_id"], name="aud_audlog_enttyp_entid_idx"),
            models.Index(fields=["timestamp"], name="aud_audlog_ts_idx"),
            models.Index(fields=["action"], name="aud_audlog_act_idx"),
        ]

