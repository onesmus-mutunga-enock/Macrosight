from rest_framework import status, serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from django.contrib.auth import authenticate
from django.contrib.auth.models import update_last_login
from .serializers import (
    LoginSerializer,
    ChangePasswordSerializer,
    MFASerializer,
    UserSerializer,
    UserCreateSerializer,
    UserUpdateSerializer
)
from .models import User, LoginHistory, MFADevice
from apps.governance.models import Role
from apps.audit.models import AuditLog
from datetime import datetime, timedelta
import pyotp


class LoginView(APIView):
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        email = serializer.validated_data.get('email')
        password = serializer.validated_data.get('password')
        user = authenticate(request, email=email, password=password)

        if not user or not user.is_active:
            return Response(
                {"error": "Invalid credentials"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if user.is_disabled:
            return Response(
                {"error": "Account is disabled"},
                status=status.HTTP_403_FORBIDDEN
            )

        if user.must_change_password:
            return Response(
                {"error": "Must change password"},
                status=status.HTTP_403_FORBIDDEN
            )

        login_successful = True
        failure_reason = ""
        try:
            refresh = RefreshToken.for_user(user)
            update_last_login(None, user)

            LoginHistory.objects.create(
                user=user,
                ip_address=request.META.get('REMOTE_ADDR', 'unknown'),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                login_successful=True
            )

            AuditLog.objects.create(
                user=user,
                action='LOGIN_SUCCESS',
                object_type='User',
                object_id=str(user.id),
                ip_address=request.META.get('REMOTE_ADDR', 'unknown'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )

        except Exception as e:
            login_successful = False
            failure_reason = str(e)
            LoginHistory.objects.create(
                user=user,
                ip_address=request.META.get('REMOTE_ADDR', 'unknown'),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                login_successful=False,
                failure_reason=failure_reason
            )

        if not login_successful:
            return Response(
                {"error": "Login failed"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': UserSerializer(user).data
        }, status=status.HTTP_200_OK)


class RefreshTokenView(TokenRefreshView):
    serializer_class = TokenRefreshSerializer


class LogoutView(APIView):
    serializer_class = TokenRefreshSerializer
    def post(self, request):
        try:
            refresh_token = request.data["refresh_token"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response(
                {"error": "Logout failed"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class MeView(APIView):
    serializer_class = UserSerializer
    def get(self, request):
        user = request.user
        return Response(UserSerializer(user).data, status=status.HTTP_200_OK)


class ChangePasswordView(APIView):
    serializer_class = ChangePasswordSerializer
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = request.user
        password = serializer.validated_data.get('password')
        user.set_password(password)
        user.must_change_password = False
        user.last_password_change_at = datetime.now()
        user.save()

        AuditLog.objects.create(
            user=user,
            action='PASSWORD_CHANGE',
            object_type='User',
            object_id=str(user.id)
        )

        return Response(status=status.HTTP_204_NO_CONTENT)


class MFAVerifyView(APIView):
    serializer_class = MFASerializer
    def post(self, request):
        serializer = MFASerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = request.user
        token = serializer.validated_data.get('token')

        if not user.mfa_secret:
            return Response(
                {"error": "MFA not enabled for user"},
                status=status.HTTP_400_BAD_REQUEST
            )

        totp = pyotp.TOTP(user.mfa_secret)
        if totp.verify(token):
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(
                {"error": "Invalid MFA token"},
                status=status.HTTP_401_UNAUTHORIZED
            )


class ForceLogoutSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False)


class ForceLogoutView(APIView):
    serializer_class = ForceLogoutSerializer
    def post(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
            if not request.user.is_superuser:
                return Response(
                    {"error": "Permission denied"},
                    status=status.HTTP_403_FORBIDDEN
                )

            user.blacklist_all_tokens()
            AuditLog.objects.create(
                user=request.user,
                action='FORCE_LOGOUT',
                object_type='User',
                object_id=str(user_id)
            )

            return Response(status=status.HTTP_204_NO_CONTENT)
        except User.DoesNotExist:
            return Response(
                {"error": "User not found"},
                status=status.HTTP_404_NOT_FOUND
            )


class LoginHistorySerializer(serializers.Serializer):
    user_id = serializers.CharField()
    ip_address = serializers.CharField()
    user_agent = serializers.CharField()
    created_at = serializers.DateTimeField()


class LoginHistoryView(APIView):
    serializer_class = LoginHistorySerializer
    def get(self, request):
        if not request.user.is_superuser:
            return Response(
                {"error": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN
            )

        history = LoginHistory.objects.select_related('user').order_by('-created_at')
        # Return serialized data for history; LoginHistory serializer isn't defined here,
        # so return a list of dicts to keep response stable for schema tools.
        data = [
            {
                "user_id": str(h.user_id),
                "ip_address": h.ip_address,
                "user_agent": h.user_agent,
                "created_at": h.created_at,
            }
            for h in history
        ]
        return Response(data, status=status.HTTP_200_OK)