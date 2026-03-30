import uuid
import pyotp
from datetime import timedelta
from django.core.validators import RegexValidator
import base64
from io import BytesIO
import qrcode
from django.db import models
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone


class UserManager(BaseUserManager):
    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("Users must have an email address")
        email = self.normalize_email(email)

        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.last_password_change_at = timezone.now()
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_superuser", False)
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("is_disabled", False)
        return self._create_user(email=email, password=password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("is_disabled", False)

        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")

        return self._create_user(email=email, password=password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
    )

    email = models.EmailField(
        unique=True,
        error_messages={
            'unique': "A user with that email already exists.",
        }
    )
    phone = models.CharField(
        validators=[phone_regex],
        max_length=17,
        blank=True
    )
    first_name = models.CharField(max_length=255, blank=True)
    last_name = models.CharField(max_length=255, blank=True)
    primary_role = models.ForeignKey(
        "governance.Role",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="primary_users",
    )

    is_active = models.BooleanField(default=True)
    is_disabled = models.BooleanField(
        default=False,
        help_text="If true, user is administratively disabled regardless of is_active.",
    )
    is_staff = models.BooleanField(default=False)

    must_change_password = models.BooleanField(
        default=False,
        help_text="If true, user must change password at next login.",
    )
    mfa_enabled = models.BooleanField(default=False)
    last_password_change_at = models.DateTimeField(null=True, blank=True)
    login_attempts_reset_at = models.DateTimeField(null=True, blank=True)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)

    failed_login_attempts = models.PositiveIntegerField(default=0)

    metadata = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        db_table = "users_user"
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        return self.is_superuser or self.user_permissions.filter(codename=perm).exists()

    def has_module_perms(self, app_label):
        return self.is_superuser or self.user_permissions.filter(codename__startswith=app_label).exists()

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.email

    def get_short_name(self):
        return self.first_name or self.email

    def generate_mfa_secret(self):
        if not self.mfa_secret:
            self.mfa_secret = pyotp.random_base32()
            self.save(update_fields=['mfa_secret'])
        return self.mfa_secret

    def get_mfa_qr_code(self):
        if not self.mfa_secret:
            self.generate_mfa_secret()

        totp = pyotp.TOTP(self.mfa_secret)
        provisioning_uri = totp.provisioning_uri(
            self.email,
            issuer_name="MacroSight"
        )

        qr = qrcode.QRCode()
        qr.add_data(provisioning_uri)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)

        img_base64 = base64.b64encode(buffer.getvalue()).decode()
        return f"data:image/png;base64,{img_base64}"

    def verify_mfa_token(self, token):
        if not self.mfa_secret:
            return False
        totp = pyotp.TOTP(self.mfa_secret)
        return totp.verify(token, valid_window=1)  # Allow 1 time step tolerance


class LoginHistory(models.Model):
    """Track user login attempts for security auditing."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="login_history",
    )

    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)

    login_successful = models.BooleanField()
    failure_reason = models.CharField(max_length=100, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "users_login_history"
        verbose_name = "Login History"
        verbose_name_plural = "Login History"
        ordering = ("-created_at",)

    def __str__(self):
        status = "SUCCESS" if self.login_successful else "FAILED"
        return f"{self.user.email} - {status} - {self.ip_address}"


class MFADevice(models.Model):
    """Store MFA device information for users."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="mfa_devices",
    )

    name = models.CharField(max_length=100)
    device_type = models.CharField(max_length=20, default="totp")
    secret = models.CharField(max_length=32)

    is_primary = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "users_mfa_device"
        verbose_name = "MFA Device"
        verbose_name_plural = "MFA Devices"

    def __str__(self):
        return f"{self.name} ({self.device_type})"