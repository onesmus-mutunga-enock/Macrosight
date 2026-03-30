from django.urls import path
from .views import (
    LoginView,
    RefreshTokenView,
    LogoutView,
    MeView,
    ChangePasswordView,
    MFAVerifyView,
    ForceLogoutView,
    LoginHistoryView,
)

urlpatterns = [
    path("auth/login/", LoginView.as_view(), name="auth-login"),
    path("auth/refresh/", RefreshTokenView.as_view(), name="auth-refresh"),
    path("auth/logout/", LogoutView.as_view(), name="auth-logout"),
    path("auth/me/", MeView.as_view(), name="auth-me"),
    path("auth/change-password/", ChangePasswordView.as_view(), name="auth-change-password"),
    path("auth/mfa/verify/", MFAVerifyView.as_view(), name="auth-mfa-verify"),
    path("auth/force-logout/<str:user_id>/", ForceLogoutView.as_view(), name="auth-force-logout"),
    path("auth/login-history/", LoginHistoryView.as_view(), name="auth-login-history"),
]
