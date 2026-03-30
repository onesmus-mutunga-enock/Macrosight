from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from .models import Role, Permission, RolePermission
from .serializers import RoleSerializer, PermissionSerializer, RolePermissionSerializer
from apps.audit.models import AuditLog
from django.db import transaction


class RoleListView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        roles = Role.objects.all()
        return Response(RoleSerializer(roles, many=True).data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = RoleSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        with transaction.atomic():
            role = serializer.save(created_by=request.user)
            AuditLog.objects.create(
                user=request.user,
                action='ROLE_CREATE',
                object_type='Role',
                object_id=str(role.id)
            )

        return Response(RoleSerializer(role).data, status=status.HTTP_201_CREATED)


class RoleDetailView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request, pk):
        try:
            role = Role.objects.get(id=pk)
            return Response(RoleSerializer(role).data, status=status.HTTP_200_OK)
        except Role.DoesNotExist:
            return Response(
                {"error": "Role not found"},
                status=status.HTTP_404_NOT_FOUND
            )

    def put(self, request, pk):
        try:
            role = Role.objects.get(id=pk)
            serializer = RoleSerializer(role, data=request.data)
            if not serializer.is_valid():
                return Response(
                    {"errors": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )

            with transaction.atomic():
                serializer.save()
                AuditLog.objects.create(
                    user=request.user,
                    action='ROLE_UPDATE',
                    object_type='Role',
                    object_id=str(role.id)
                )

            return Response(RoleSerializer(role).data, status=status.HTTP_200_OK)
        except Role.DoesNotExist:
            return Response(
                {"error": "Role not found"},
                status=status.HTTP_404_NOT_FOUND
            )

    def delete(self, request, pk):
        try:
            role = Role.objects.get(id=pk)
            if role.name in ['SUPER_ADMIN', 'ECONOMIC_ANALYST', 'DATA_SCIENTIST', 'AUDITOR', 'EXECUTIVE_VIEWER', 'DATA_FEEDER']:
                return Response(
                    {"error": "Cannot delete system role"},
                    status=status.HTTP_403_FORBIDDEN
                )

            with transaction.atomic():
                role.delete()
                AuditLog.objects.create(
                    user=request.user,
                    action='ROLE_DELETE',
                    object_type='Role',
                    object_id=str(pk)
                )

            return Response(status=status.HTTP_204_NO_CONTENT)
        except Role.DoesNotExist:
            return Response(
                {"error": "Role not found"},
                status=status.HTTP_404_NOT_FOUND
            )


class RolePermissionView(APIView):
    permission_classes = [IsAdminUser]

    def put(self, request, pk):
        try:
            role = Role.objects.get(id=pk)
            serializer = RolePermissionSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(
                    {"errors": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )

            with transaction.atomic():
                permissions = serializer.validated_data.get('permissions', [])
                role.permissions = permissions
                role.save()
                AuditLog.objects.create(
                    user=request.user,
                    action='ROLE_PERMISSION_UPDATE',
                    object_type='Role',
                    object_id=str(role.id)
                )

            return Response(RoleSerializer(role).data, status=status.HTTP_200_OK)
        except Role.DoesNotExist:
            return Response(
                {"error": "Role not found"},
                status=status.HTTP_404_NOT_FOUND
            )


class PermissionListView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        permissions = Permission.objects.all()
        return Response(PermissionSerializer(permissions, many=True).data, status=status.HTTP_200_OK)


class UserListView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        users = User.objects.select_related('primary_role').all()
        return Response(UserSerializer(users, many=True).data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = UserCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        with transaction.atomic():
            user = serializer.save(created_by=request.user)
            AuditLog.objects.create(
                user=request.user,
                action='USER_CREATE',
                object_type='User',
                object_id=str(user.id)
            )

        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class UserDetailView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request, pk):
        try:
            user = User.objects.get(id=pk)
            return Response(UserSerializer(user).data, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response(
                {"error": "User not found"},
                status=status.HTTP_404_NOT_FOUND
            )

    def put(self, request, pk):
        try:
            user = User.objects.get(id=pk)
            serializer = UserUpdateSerializer(user, data=request.data)
            if not serializer.is_valid():
                return Response(
                    {"errors": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )

            with transaction.atomic():
                serializer.save()
                AuditLog.objects.create(
                    user=request.user,
                    action='USER_UPDATE',
                    object_type='User',
                    object_id=str(user.id)
                )

            return Response(UserSerializer(user).data, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response(
                {"error": "User not found"},
                status=status.HTTP_404_NOT_FOUND
            )

    def delete(self, request, pk):
        try:
            user = User.objects.get(id=pk)
            if user.email == request.user.email:
                return Response(
                    {"error": "Cannot delete own account"},
                    status=status.HTTP_403_FORBIDDEN
                )

            with transaction.atomic():
                user.delete()
                AuditLog.objects.create(
                    user=request.user,
                    action='USER_DELETE',
                    object_type='User',
                    object_id=str(pk)
                )

            return Response(status=status.HTTP_204_NO_CONTENT)
        except User.DoesNotExist:
            return Response(
                {"error": "User not found"},
                status=status.HTTP_404_NOT_FOUND
            )


class UserDisableView(APIView):
    permission_classes = [IsAdminUser]

    def put(self, request, pk):
        try:
            user = User.objects.get(id=pk)
            if user.email == request.user.email:
                return Response(
                    {"error": "Cannot disable own account"},
                    status=status.HTTP_403_FORBIDDEN
                )

            with transaction.atomic():
                user.is_disabled = True
                user.save()
                AuditLog.objects.create(
                    user=request.user,
                    action='USER_DISABLE',
                    object_type='User',
                    object_id=str(user.id)
                )

            return Response(status=status.HTTP_204_NO_CONTENT)
        except User.DoesNotExist:
            return Response(
                {"error": "User not found"},
                status=status.HTTP_404_NOT_FOUND
            )


class UserEnableView(APIView):
    permission_classes = [IsAdminUser]

    def put(self, request, pk):
        try:
            user = User.objects.get(id=pk)
            with transaction.atomic():
                user.is_disabled = False
                user.save()
                AuditLog.objects.create(
                    user=request.user,
                    action='USER_ENABLE',
                    object_type='User',
                    object_id=str(user.id)
                )

            return Response(status=status.HTTP_204_NO_CONTENT)
        except User.DoesNotExist:
            return Response(
                {"error": "User not found"},
                status=status.HTTP_404_NOT_FOUND
            )


class UserResetCredentialsView(APIView):
    permission_classes = [IsAdminUser]

    def put(self, request, pk):
        try:
            user = User.objects.get(id=pk)
            if user.email == request.user.email:
                return Response(
                    {"error": "Cannot reset own credentials"},
                    status=status.HTTP_403_FORBIDDEN
                )

            with transaction.atomic():
                user.set_password('password123')
                user.must_change_password = True
                user.save()
                AuditLog.objects.create(
                    user=request.user,
                    action='USER_RESET_CREDENTIALS',
                    object_type='User',
                    object_id=str(user.id)
                )

            return Response(status=status.HTTP_204_NO_CONTENT)
        except User.DoesNotExist:
            return Response(
                {"error": "User not found"},
                status=status.HTTP_404_NOT_FOUND
            )


class UserRoleView(APIView):
    permission_classes = [IsAdminUser]

    def put(self, request, pk):
        try:
            user = User.objects.get(id=pk)
            role_id = request.data.get('role_id')
            try:
                role = Role.objects.get(id=role_id)
            except Role.DoesNotExist:
                return Response(
                    {"error": "Role not found"},
                    status=status.HTTP_404_NOT_FOUND
                )

            with transaction.atomic():
                user.primary_role = role
                user.save()
                AuditLog.objects.create(
                    user=request.user,
                    action='USER_ROLE_UPDATE',
                    object_type='User',
                    object_id=str(user.id)
                )

            return Response(UserSerializer(user).data, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response(
                {"error": "User not found"},
                status=status.HTTP_404_NOT_FOUND
            )