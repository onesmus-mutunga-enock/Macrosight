import uuid

from django.db import models


class Role(models.Model):
    class RoleCode(models.TextChoices):
        SUPER_ADMIN = "SUPER_ADMIN", "Super Admin"
        ECONOMIC_ANALYST = "ECONOMIC_ANALYST", "Economic Analyst"
        DATA_SCIENTIST = "DATA_SCIENTIST", "Data Scientist"
        AUDITOR = "AUDITOR", "Auditor"
        EXECUTIVE_VIEWER = "EXECUTIVE_VIEWER", "Executive Viewer"
        DATA_FEEDER = "DATA_FEEDER", "Data Feeder"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(
        max_length=64,
        choices=RoleCode.choices,
        unique=True,
        help_text="Stable code used in authorization logic and policy definitions.",
    )
    name = models.CharField(max_length=128)
    description = models.TextField(blank=True)

    is_system_role = models.BooleanField(
        default=True,
        help_text="System roles are managed via governance processes, not arbitrarily edited.",
    )
    is_active = models.BooleanField(default=True)

    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Optional governance metadata (e.g., allowed scopes, risk level).",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "governance_role"
        verbose_name = "Role"
        verbose_name_plural = "Roles"

    def __str__(self):
        return f"{self.code}"


class Permission(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(
        max_length=128,
        unique=True,
        help_text="Stable, machine-readable code for use in policy checks.",
    )
    name = models.CharField(max_length=128)
    description = models.TextField(blank=True)

    category = models.CharField(
        max_length=64,
        blank=True,
        help_text="Logical grouping (e.g., 'sales', 'policies', 'ml').",
    )
    is_active = models.BooleanField(default=True)

    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Constraint hints (e.g., sector scoping, read-only flags).",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "governance_permission"
        verbose_name = "Permission"
        verbose_name_plural = "Permissions"

    def __str__(self):
        return self.code


class RolePermission(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        related_name="role_permissions",
    )
    permission = models.ForeignKey(
        Permission,
        on_delete=models.CASCADE,
        related_name="permission_roles",
    )

    is_allowed = models.BooleanField(default=True)
    constraints = models.JSONField(
        default=dict,
        blank=True,
        help_text="Contextual constraints, e.g., sector IDs, indicator sets.",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "governance_role_permission"
        verbose_name = "Role Permission"
        verbose_name_plural = "Role Permissions"
        unique_together = ("role", "permission")

    def __str__(self):
        return f"{self.role.code} -> {self.permission.code}"



SUPER_ADMIN = Role.RoleCode.SUPER_ADMIN
ECONOMIC_ANALYST = Role.RoleCode.ECONOMIC_ANALYST
DATA_FEEDER = Role.RoleCode.DATA_FEEDER
DATA_SCIENTIST = Role.RoleCode.DATA_SCIENTIST
AUDITOR = Role.RoleCode.AUDITOR
EXECUTIVE_VIEWER = Role.RoleCode.EXECUTIVE_VIEWER


