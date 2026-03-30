from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action, permission_classes, api_view
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import serializers as drf_serializers
from rest_framework.generics import GenericAPIView
from django.utils.decorators import method_decorator


# Local named serializer for schema tools
class SystemBackupSerializer(drf_serializers.Serializer):
    force = drf_serializers.BooleanField(required=False, help_text="Force backup")
from rest_framework.response import Response

from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
)

from apps.governance.permissions import (
    HasAnyRole,
    admin_only,
    require_roles,
    _get_user_role_code,
)

from .models import Alert, DataSnapshot, SystemConfig, SystemJob
from .serializers import DataSnapshotSerializer
from .serializers_alerts import AlertSerializer, SystemConfigSerializer, SystemJobSerializer
from .services.snapshots import freeze_snapshot, lock_snapshot


@extend_schema_view(
    list=extend_schema(
        summary="List data snapshots",
        description="List frozen data snapshots available for ML and forecasting.",
        tags=["System - Snapshots"],
        responses={200: DataSnapshotSerializer},
    ),
    retrieve=extend_schema(
        summary="Retrieve data snapshot",
        description="Retrieve a single data snapshot by ID.",
        tags=["System - Snapshots"],
        responses={200: DataSnapshotSerializer},
    ),
    create=extend_schema(
        summary="Freeze data snapshot",
        description="Freeze a new data snapshot from approved sources. SUPER_ADMIN only.",
        tags=["System - Snapshots"],
        responses={201: DataSnapshotSerializer},
    ),
)
class DataSnapshotViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    """
    Implements the Data Snapshot & Freeze API:

    - POST /api/v1/data/snapshots/freeze/       (create)
    - GET  /api/v1/data/snapshots/             (list)
    - GET  /api/v1/data/snapshots/{id}/        (retrieve)
    - POST /api/v1/data/snapshots/{id}/lock/   (lock)

    Access per contract:
    - SUPER_ADMIN: full access (freeze, list, detail, lock)
    - DATA_SCIENTIST: read-only (list, detail)
    """

    queryset = DataSnapshot.objects.all()
    serializer_class = DataSnapshotSerializer
    permission_classes = [IsAuthenticated, HasAnyRole]

    # Used by HasAnyRole to constrain access to SUPER_ADMIN + DATA_SCIENTIST
    required_role_codes = ("SUPER_ADMIN", "DATA_SCIENTIST")

    def get_queryset(self):
        # In future, this can enforce organisation / tenant scoping.
        return super().get_queryset()

    @require_roles("SUPER_ADMIN")
    def create(self, request, *args, **kwargs):
        """
        Freeze a new snapshot.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Only allow context & metadata inputs; name/description are also accepted.
        name = serializer.validated_data.get("name")
        description = serializer.validated_data.get("description", "")
        context = serializer.validated_data.get("context", {})
        metadata = serializer.validated_data.get("metadata", {})

        snapshot = freeze_snapshot(
            created_by=request.user,
            name=name,
            description=description,
            context=context,
            metadata=metadata,
            request=request,
        )

        output_serializer = self.get_serializer(snapshot)
        headers = self.get_success_headers(output_serializer.data)
        return Response(
            output_serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    @extend_schema(
        summary="Lock snapshot",
        description="Lock an existing snapshot, preventing further changes.",
        tags=["System - Snapshots"],
        responses={200: DataSnapshotSerializer},
    )
    @action(detail=True, methods=["post"], url_path="lock")
    @admin_only
    def lock(self, request, pk=None):
        snapshot = self.get_object()
        snapshot = lock_snapshot(snapshot=snapshot, locked_by=request.user, request=request)
        serializer = self.get_serializer(snapshot)
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(
    summary="Health check",
    description="Basic system health status for monitoring.",
    tags=["System"],
    responses={200: OpenApiResponse(description="Health status")},
)
@api_view(["GET"])
@permission_classes([AllowAny])
def system_health(request):
    payload = {
        "status": "ok",
        "version": "1.0.0",
    }
    return Response(payload, status=status.HTTP_200_OK)


@extend_schema(
    summary="Get system configuration",
    description="Retrieve system configuration. SUPER_ADMIN only.",
    tags=["System"],
    responses={200: SystemConfigSerializer},
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def system_config_get(request):
    role_code = _get_user_role_code(request.user)
    if role_code != "SUPER_ADMIN" and not request.user.is_superuser:
        return Response({"detail": "Admin privileges required."}, status=status.HTTP_403_FORBIDDEN)

    config, _ = SystemConfig.objects.get_or_create(name="default")
    serializer = SystemConfigSerializer(config)
    return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(
    summary="Update system configuration",
    description="Update system configuration. SUPER_ADMIN only.",
    tags=["System"],
    request=SystemConfigSerializer,
    responses={200: SystemConfigSerializer},
)
@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def system_config_put(request):
    role_code = _get_user_role_code(request.user)
    if role_code != "SUPER_ADMIN" and not request.user.is_superuser:
        return Response({"detail": "Admin privileges required."}, status=status.HTTP_403_FORBIDDEN)

    config, _ = SystemConfig.objects.get_or_create(name="default")
    serializer = SystemConfigSerializer(config, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    config.config = serializer.validated_data.get("config", config.config)
    config.updated_by = request.user
    config.save(update_fields=["config", "updated_by", "updated_at"])
    output = SystemConfigSerializer(config)
    return Response(output.data, status=status.HTTP_200_OK)


@extend_schema(
    summary="List system jobs",
    description="Admin job monitoring endpoint.",
    tags=["System - Jobs"],
    responses={200: SystemJobSerializer(many=True)},
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def admin_jobs_list(request):
    role_code = _get_user_role_code(request.user)
    if role_code != "SUPER_ADMIN" and not request.user.is_superuser:
        return Response({"detail": "Admin privileges required."}, status=status.HTTP_403_FORBIDDEN)

    jobs = SystemJob.objects.all()
    serializer = SystemJobSerializer(jobs, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(
    summary="Pause system job",
    description="Pause a system job. SUPER_ADMIN only.",
    tags=["System - Jobs"],
    responses={200: SystemJobSerializer},
)
@method_decorator(admin_only, name="dispatch")
class AdminJobsPauseView(GenericAPIView):
    serializer_class = SystemJobSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, id: str):
        role_code = _get_user_role_code(request.user)
        if role_code != "SUPER_ADMIN" and not request.user.is_superuser:
            return Response({"detail": "Admin privileges required."}, status=status.HTTP_403_FORBIDDEN)

        job = SystemJob.objects.get(pk=id)
        job.status = SystemJob.Status.PAUSED
        job.save(update_fields=["status"])
        serializer = SystemJobSerializer(job)
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(
    summary="Resume system job",
    description="Resume a paused system job. SUPER_ADMIN only.",
    tags=["System - Jobs"],
    responses={200: SystemJobSerializer},
)
@method_decorator(admin_only, name="dispatch")
class AdminJobsResumeView(GenericAPIView):
    serializer_class = SystemJobSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, id: str):
        role_code = _get_user_role_code(request.user)
        if role_code != "SUPER_ADMIN" and not request.user.is_superuser:
            return Response({"detail": "Admin privileges required."}, status=status.HTTP_403_FORBIDDEN)

        job = SystemJob.objects.get(pk=id)
        job.status = SystemJob.Status.RUNNING
        job.save(update_fields=["status"])
        serializer = SystemJobSerializer(job)
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(
    summary="Jobs history",
    description="Return recent job history events (placeholder, using SystemJob records).",
    tags=["System - Jobs"],
    responses={200: SystemJobSerializer(many=True)},
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def admin_jobs_history(request):
    role_code = _get_user_role_code(request.user)
    if role_code != "SUPER_ADMIN" and not request.user.is_superuser:
        return Response({"detail": "Admin privileges required."}, status=status.HTTP_403_FORBIDDEN)

    jobs = SystemJob.objects.order_by("-updated_at")[:200]
    serializer = SystemJobSerializer(jobs, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema_view(
    list=extend_schema(
        summary="List alerts",
        description="List alerts and thresholds. Roles: SUPER_ADMIN, ECONOMIC_ANALYST.",
        tags=["Alerts"],
        responses={200: AlertSerializer},
    ),
    create=extend_schema(
        summary="Create alert",
        description="Create a new alert. Roles: SUPER_ADMIN, ECONOMIC_ANALYST.",
        tags=["Alerts"],
        responses={201: AlertSerializer},
        examples=[
            OpenApiExample(
                "Create alert request",
                value={
                    "title": "Forecast accuracy below threshold",
                    "message": "MAPE exceeded 15% for sector AGRICULTURE.",
                    "severity": "WARNING",
                    "threshold_config": {
                        "metric": "MAPE",
                        "threshold": 0.15,
                        "window": "30d",
                    },
                },
                request_only=True,
            ),
        ],
    ),
)
class AlertViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    """
    Alerts & Threshold API:

    - POST /api/v1/alerts/
    - GET  /api/v1/alerts/
    - POST /api/v1/alerts/{id}/acknowledge/
    """

    queryset = Alert.objects.all()
    serializer_class = AlertSerializer
    permission_classes = [IsAuthenticated]

    @require_roles("SUPER_ADMIN", "ECONOMIC_ANALYST")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @require_roles("SUPER_ADMIN", "ECONOMIC_ANALYST")
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        alert = Alert.objects.create(
            title=serializer.validated_data["title"],
            message=serializer.validated_data["message"],
            severity=serializer.validated_data.get("severity", Alert.Severity.INFO),
            threshold_config=serializer.validated_data.get("threshold_config", {}) or {},
            created_by=request.user,
        )
        output = self.get_serializer(alert)
        headers = self.get_success_headers(output.data)
        return Response(output.data, status=status.HTTP_201_CREATED, headers=headers)

    @extend_schema(
        summary="Acknowledge alert",
        description="Acknowledge an existing alert.",
        tags=["Alerts"],
        responses={200: AlertSerializer},
    )
    @action(detail=True, methods=["post"], url_path="acknowledge")
    @require_roles("SUPER_ADMIN", "ECONOMIC_ANALYST")
    def acknowledge(self, request, pk=None):
        from django.utils import timezone

        alert = self.get_object()
        alert.status = Alert.Status.ACKNOWLEDGED
        alert.acknowledged_by = request.user
        alert.acknowledged_at = timezone.now()
        alert.save(update_fields=["status", "acknowledged_by", "acknowledged_at"])
        serializer = self.get_serializer(alert)
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(
    summary="Executive dashboard data",
    description="Role-specific dashboard aggregation for executives.",
    tags=["Dashboards"],
    responses={200: OpenApiResponse(description="Executive dashboard payload")},
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def dashboard_executive(request):
    role_code = _get_user_role_code(request.user)
    if role_code != "EXECUTIVE_VIEWER" and not request.user.is_superuser:
        return Response({"detail": "Executive role required."}, status=status.HTTP_403_FORBIDDEN)
    payload = {
        "summary": "Executive dashboard stub",
    }
    return Response(payload, status=status.HTTP_200_OK)


@extend_schema(
    summary="Analyst dashboard data",
    description="Role-specific dashboard aggregation for analysts.",
    tags=["Dashboards"],
    responses={200: OpenApiResponse(description="Analyst dashboard payload")},
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def dashboard_analyst(request):
    role_code = _get_user_role_code(request.user)
    if role_code != "ECONOMIC_ANALYST" and not request.user.is_superuser:
        return Response({"detail": "Analyst role required."}, status=status.HTTP_403_FORBIDDEN)
    payload = {
        "summary": "Analyst dashboard stub",
    }
    return Response(payload, status=status.HTTP_200_OK)


@extend_schema(
    summary="Audit dashboard data",
    description="Role-specific dashboard aggregation for auditors.",
    tags=["Dashboards"],
    responses={200: OpenApiResponse(description="Audit dashboard payload")},
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def dashboard_audit(request):
    role_code = _get_user_role_code(request.user)
    if role_code != "AUDITOR" and not request.user.is_superuser:
        return Response({"detail": "Auditor role required."}, status=status.HTTP_403_FORBIDDEN)
    payload = {
        "summary": "Audit dashboard stub",
    }
    return Response(payload, status=status.HTTP_200_OK)


@extend_schema(
    summary="Data feeder dashboard data",
    description="Role-specific dashboard aggregation for data feeders.",
    tags=["Dashboards"],
    responses={200: OpenApiResponse(description="Data Feeder dashboard payload")},
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def dashboard_data_feeder(request):
    role_code = _get_user_role_code(request.user)
    if role_code != "DATA_FEEDER" and not request.user.is_superuser:
        return Response({"detail": "Data Feeder role required."}, status=status.HTTP_403_FORBIDDEN)
    payload = {
        "summary": "Data Feeder dashboard stub",
    }
    return Response(payload, status=status.HTTP_200_OK)


@extend_schema(
    summary="System usage metrics",
    description="Admin-only system usage metrics placeholder.",
    tags=["System"],
    responses={200: OpenApiResponse(description="Usage metrics JSON")},
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def admin_system_usage(request):
    role_code = _get_user_role_code(request.user)
    if role_code != "SUPER_ADMIN" and not request.user.is_superuser:
        return Response({"detail": "Admin privileges required."}, status=status.HTTP_403_FORBIDDEN)
    payload = {
        "users": 0,
        "requests_last_24h": 0,
    }
    return Response(payload, status=status.HTTP_200_OK)


@extend_schema(
    summary="Trigger system backup",
    description="Placeholder endpoint to trigger a system backup job. SUPER_ADMIN only.",
    tags=["System"],
    responses={202: OpenApiResponse(description="Backup request accepted")},
)
class SystemBackupView(GenericAPIView):
    serializer_class = SystemBackupSerializer
    permission_classes = [IsAuthenticated]

    @method_decorator(admin_only, name="dispatch")
    def post(self, request):
        role_code = _get_user_role_code(request.user)
        if role_code != "SUPER_ADMIN" and not request.user.is_superuser:
            return Response({"detail": "Admin privileges required."}, status=status.HTTP_403_FORBIDDEN)
        payload = {
            "status": "backup-request-accepted",
        }
        return Response(payload, status=status.HTTP_202_ACCEPTED)

