from functools import wraps
from typing import Callable, Iterable

from django.http import HttpRequest
from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied
from .models import SUPER_ADMIN, ECONOMIC_ANALYST, DATA_FEEDER, DATA_SCIENTIST, AUDITOR, EXECUTIVE_VIEWER


def _get_user_role_code(user) -> str:
    role = getattr(user, "primary_role", None)
    return getattr(role, "code", "") or ""


def require_roles(*allowed_role_codes: str) -> Callable:
    """
    Decorator enforcing that the authenticated user has one of the given role codes.

    Designed for DRF ViewSet methods: (self, request, *args, **kwargs).
    """

    def decorator(view_method: Callable) -> Callable:
        @wraps(view_method)
        def _wrapped(self, request: HttpRequest, *args, **kwargs):
            user = request.user
            if not user or not user.is_authenticated:
                raise PermissionDenied("Authentication required.")

            role_code = _get_user_role_code(user)
            if role_code not in allowed_role_codes and not user.is_superuser:
                raise PermissionDenied("Insufficient role for this operation.")

            return view_method(self, request, *args, **kwargs)

        return _wrapped

    return decorator


def admin_only(view_method: Callable) -> Callable:
    """
    Guard ensuring only SUPER_ADMIN (or Django superuser) can call the endpoint.
    """

    @wraps(view_method)
    def _wrapped(self, request: HttpRequest, *args, **kwargs):
        user = request.user
        if not user or not user.is_authenticated:
            raise PermissionDenied("Authentication required.")

        role_code = _get_user_role_code(user)
        if role_code != "SUPER_ADMIN" and not user.is_superuser:
            raise PermissionDenied("Admin privileges required.")

        return view_method(self, request, *args, **kwargs)

    return _wrapped


def auditor_read_only(view_method: Callable) -> Callable:
    """
    Guard for Auditor read-only endpoints.
    - Requires AUDITOR role (or superuser)
    - Only allows SAFE_METHODS (GET, HEAD, OPTIONS)
    """

    @wraps(view_method)
    def _wrapped(self, request: HttpRequest, *args, **kwargs):
        user = request.user
        if not user or not user.is_authenticated:
            raise PermissionDenied("Authentication required.")

        role_code = _get_user_role_code(user)
        if role_code != "AUDITOR" and not user.is_superuser:
            raise PermissionDenied("Auditor privileges required.")

        if request.method not in permissions.SAFE_METHODS:
            raise PermissionDenied("Auditor endpoints are read-only.")

        return view_method(self, request, *args, **kwargs)

    return _wrapped


class IsSuperAdmin(permissions.BasePermission):
    """
    DRF permission class equivalent to admin_only decorator.
    """

    def has_permission(self, request, view) -> bool:
        user = request.user
        if not user or not user.is_authenticated:
            return False
        role_code = _get_user_role_code(user)
        return role_code == "SUPER_ADMIN" or bool(user.is_superuser)


class HasAnyRole(permissions.BasePermission):
    """
    Permission that checks membership of any of the provided role codes.
    Use via view attribute: required_role_codes = ("SUPER_ADMIN", "DATA_SCIENTIST")
    """

    def has_permission(self, request, view) -> bool:
        user = request.user
        if not user or not user.is_authenticated:
            return False

        required: Iterable[str] = getattr(view, "required_role_codes", ())
        if not required:
            return True

        role_code = _get_user_role_code(user)
        return role_code in required or bool(user.is_superuser)

