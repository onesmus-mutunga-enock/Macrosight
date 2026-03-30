import uuid
from django.db import models
from apps.users.models import User


class Sector(models.Model):
    """
    Economic sector definition (e.g. agriculture, manufacturing, services).
    """

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        INACTIVE = "INACTIVE", "Inactive"
        ARCHIVED = "ARCHIVED", "Archived"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    code = models.CharField(
        max_length=64,
        unique=True,
        help_text="Stable code for the sector (e.g. 'AGR', 'MAN', 'SER').",
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.ACTIVE)
    parent_sector = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sub_sectors",
        help_text="Parent sector for hierarchical organization.",
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional sector metadata.",
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="created_sectors",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "sectors_sector"
        ordering = ("code",)

    def __str__(self) -> str:
        return f"{self.code} - {self.name}"