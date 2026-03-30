from django.shortcuts import get_object_or_404
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action, permission_classes, api_view
from rest_framework import serializers as drf_serializers
from rest_framework.generics import GenericAPIView
from django.utils.decorators import method_decorator


# Small local serializers to help schema generation
class ForecastActualsSerializer(drf_serializers.Serializer):
    actuals = drf_serializers.JSONField(help_text="Actuals payload (free-form JSON)")


class OrchestrateSerializer(drf_serializers.Serializer):
    pass
from rest_framework.permissions import IsAuthenticated
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
)

from .models import Forecast, ForecastSchedule
from .serializers import (
    ForecastGenerateRequestSerializer,
    ForecastScheduleSerializer,
    ForecastSerializer,
)
from .services.forecasts import (
    approve_forecast,
    compute_delta_stub,
    create_forecast_from_request,
    invalidate_forecast,
    record_actuals_and_update_accuracy,
    reject_forecast,
    submit_forecast,
)
from .services.schedules import (
    create_schedule,
    orchestrate_schedules,
    pause_schedule,
    resume_schedule,
)


@extend_schema_view(
    list=extend_schema(
        summary="List forecasts",
        description="List forecasts. ECONOMIC_ANALYST can list all; EXECUTIVE_VIEWER can see approved forecasts.",
        tags=["Forecasts"],
        responses={200: ForecastSerializer},
    ),
    retrieve=extend_schema(
        summary="Retrieve forecast",
        description="Retrieve a forecast by ID.",
        tags=["Forecasts"],
        responses={200: ForecastSerializer},
    ),
)
class ForecastViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """
    Forecast Results API (partial for lifecycle):

    - POST /api/v1/forecasts/generate/                 (Analyst)
    - GET  /api/v1/forecasts/                          (Analyst)
    - GET  /api/v1/forecasts/{id}/                     (Executive, Analyst)
    - POST /api/v1/forecasts/{id}/submit/              (Analyst)
    - POST /api/v1/admin/forecasts/{id}/approve/       (SuperAdmin/Executive)
    - POST /api/v1/admin/forecasts/{id}/reject/        (SuperAdmin/Executive)
    - PUT  /api/v1/admin/forecasts/{id}/invalidate/    (Admin)
    - POST /api/v1/forecasts/{id}/actuals/             (Analyst/Data Scientist)
    - GET  /api/v1/forecasts/{id}/accuracy/            (Analyst/Executive)
    - GET  /api/v1/forecasts/{id}/delta/               (Analyst/Executive)
    """

    queryset = Forecast.objects.all()
    serializer_class = ForecastSerializer
    permission_classes = [IsAuthenticated, HasAnyRole]

    # By default, allow ECONOMIC_ANALYST and EXECUTIVE_VIEWER to read forecasts.
    required_role_codes = ("ECONOMIC_ANALYST", "EXECUTIVE_VIEWER")

    def get_queryset(self):
        # Later this can apply tenant or role-based filters (e.g. EXECUTIVE_VIEWER sees only approved).
        qs = super().get_queryset()
        user = self.request.user
        role = getattr(user, "primary_role", None)
        role_code = getattr(role, "code", "") if role else ""
        if role_code == "EXECUTIVE_VIEWER":
            qs = qs.filter(status=Forecast.Status.APPROVED)
        return qs

    @extend_schema(
        summary="Generate forecast",
        description="Generate a new forecast asynchronously. Role: ECONOMIC_ANALYST.",
        tags=["Forecasts"],
        request=ForecastGenerateRequestSerializer,
        responses={201: ForecastSerializer},
        examples=[
            OpenApiExample(
                "Generate forecast request",
                value={
                    "name": "Q1 Demand Forecast",
                    "description": "Baseline forecast using current VAT and indicators.",
                    "snapshot": "00000000-0000-0000-0000-000000000001",
                    "policy_version": "00000000-0000-0000-0000-000000000002",
                    "indicator_version": "00000000-0000-0000-0000-000000000003",
                    "assumptions": {
                        "growth_rate": 0.03,
                        "notes": "Assumes stable fuel prices.",
                    },
                },
                request_only=True,
            ),
            OpenApiExample(
                "Generate forecast response",
                value={
                    "id": "11111111-1111-1111-1111-111111111111",
                    "name": "Q1 Demand Forecast",
                    "status": "RUNNING",
                    "snapshot": "00000000-0000-0000-0000-000000000001",
                    "policy_version": "00000000-0000-0000-0000-000000000002",
                    "indicator_version": "00000000-0000-0000-0000-000000000003",
                    "assumptions": {"growth_rate": 0.03, "notes": "Assumes stable fuel prices."},
                },
                response_only=True,
            ),
        ],
    )
    @action(detail=False, methods=["post"], url_path="generate")
    @require_roles("ECONOMIC_ANALYST")
    def generate(self, request):
        serializer = ForecastGenerateRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        forecast = create_forecast_from_request(
            actor=request.user,
            payload=serializer.validated_data,
            request=request,
        )
        output_serializer = ForecastSerializer(forecast)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

    @extend_schema(
        summary="Submit forecast for approval",
        description="Submit a forecast for approval. ECONOMIC_ANALYST only.",
        tags=["Forecasts"],
        responses={200: ForecastSerializer},
    )
    @action(detail=True, methods=["post"], url_path="submit")
    @require_roles("ECONOMIC_ANALYST")
    def submit(self, request, pk=None):
        forecast = self.get_object()
        forecast = submit_forecast(actor=request.user, forecast=forecast, request=request)
        serializer = ForecastSerializer(forecast)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Approve forecast",
        description="Approve a submitted forecast. SUPER_ADMIN or EXECUTIVE_VIEWER with approval authority.",
        tags=["Forecasts"],
        responses={200: ForecastSerializer},
    )
    @action(detail=True, methods=["post"], url_path="approve")
    @require_roles("SUPER_ADMIN", "EXECUTIVE_VIEWER")
    def approve(self, request, pk=None):
        forecast = self.get_object()
        forecast = approve_forecast(actor=request.user, forecast=forecast, request=request)
        serializer = ForecastSerializer(forecast)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Reject forecast",
        description="Reject a submitted forecast. SUPER_ADMIN or EXECUTIVE_VIEWER with approval authority.",
        tags=["Forecasts"],
        responses={200: ForecastSerializer},
    )
    @action(detail=True, methods=["post"], url_path="reject")
    @require_roles("SUPER_ADMIN", "EXECUTIVE_VIEWER")
    def reject(self, request, pk=None):
        forecast = self.get_object()
        forecast = reject_forecast(actor=request.user, forecast=forecast, request=request)
        serializer = ForecastSerializer(forecast)
        return Response(serializer.data, status=status.HTTP_200_OK)


@method_decorator(admin_only, name="dispatch")
class InvalidateForecastView(GenericAPIView):
    queryset = Forecast.objects.all()
    serializer_class = ForecastSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Invalidate forecast",
        description="Invalidate a forecast via admin control. SUPER_ADMIN only.",
        tags=["Forecasts Admin"],
        responses={200: ForecastSerializer},
    )
    def put(self, request, id: str):
        forecast = get_object_or_404(Forecast, pk=id)
        forecast = invalidate_forecast(actor=request.user, forecast=forecast, request=request)
        serializer = ForecastSerializer(forecast)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ForecastActualsView(GenericAPIView):
    serializer_class = ForecastActualsSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Record forecast actuals",
        description="Submit actuals for a forecast to compute accuracy metrics. ECONOMIC_ANALYST and DATA_SCIENTIST.",
        tags=["Forecast Accuracy"],
        request=ForecastActualsSerializer,
        responses={200: ForecastSerializer},
    )
    def post(self, request, id: str):
        from apps.governance.permissions import _get_user_role_code  # reuse helper

        role_code = _get_user_role_code(request.user)
        if role_code not in ("ECONOMIC_ANALYST", "DATA_SCIENTIST") and not request.user.is_superuser:
            return Response({"detail": "Insufficient role."}, status=status.HTTP_403_FORBIDDEN)

        forecast = get_object_or_404(Forecast, pk=id)
        forecast = record_actuals_and_update_accuracy(
            actor=request.user,
            forecast=forecast,
            actuals_payload=request.data,
            request=request,
        )
        serializer = ForecastSerializer(forecast)
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(
    summary="Forecast accuracy summary",
    description="Retrieve accuracy summary for a forecast. ECONOMIC_ANALYST and EXECUTIVE_VIEWER.",
    tags=["Forecast Accuracy"],
    responses={200: OpenApiResponse(description="Accuracy summary JSON")},
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def forecast_accuracy(request, id: str):
    from apps.governance.permissions import _get_user_role_code

    role_code = _get_user_role_code(request.user)
    if role_code not in ("ECONOMIC_ANALYST", "EXECUTIVE_VIEWER") and not request.user.is_superuser:
        return Response({"detail": "Insufficient role."}, status=status.HTTP_403_FORBIDDEN)

    forecast = get_object_or_404(Forecast, pk=id)
    return Response(forecast.accuracy_summary or {}, status=status.HTTP_200_OK)


@extend_schema(
    summary="Forecast delta comparison",
    description="Compare a forecast against a baseline forecast. ECONOMIC_ANALYST and EXECUTIVE_VIEWER.",
    tags=["Forecast Comparison"],
    responses={200: OpenApiResponse(description="Delta comparison JSON")},
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def forecast_delta(request, id: str):
    from apps.governance.permissions import _get_user_role_code

    role_code = _get_user_role_code(request.user)
    if role_code not in ("ECONOMIC_ANALYST", "EXECUTIVE_VIEWER") and not request.user.is_superuser:
        return Response({"detail": "Insufficient role."}, status=status.HTTP_403_FORBIDDEN)

    base = get_object_or_404(Forecast, pk=id)
    other_id = request.query_params.get("other_id")
    if not other_id:
        return Response(
            {"detail": "Query parameter 'other_id' is required."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    other = get_object_or_404(Forecast, pk=other_id)
    delta = compute_delta_stub(base=base, other=other)
    return Response(delta, status=status.HTTP_200_OK)


@extend_schema_view(
    list=extend_schema(
        summary="List forecast schedules",
        description="List all forecast schedules. SUPER_ADMIN and ECONOMIC_ANALYST.",
        tags=["Forecast Scheduling"],
        responses={200: ForecastScheduleSerializer},
    ),
    create=extend_schema(
        summary="Create forecast schedule",
        description="Create a new forecast schedule. SUPER_ADMIN and ECONOMIC_ANALYST.",
        tags=["Forecast Scheduling"],
        responses={201: ForecastScheduleSerializer},
    ),
)
class ForecastScheduleViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    """
    Forecast Scheduling API:

    - POST /api/v1/forecasts/schedule/             (SuperAdmin, Analyst)
    - GET  /api/v1/forecasts/schedules/            (SuperAdmin, Analyst)
    - PUT  /api/v1/forecasts/schedules/{id}/pause/ (SuperAdmin)
    - PUT  /api/v1/forecasts/schedules/{id}/resume/(SuperAdmin)
    """

    queryset = ForecastSchedule.objects.all()
    serializer_class = ForecastScheduleSerializer
    permission_classes = [IsAuthenticated]

    @require_roles("SUPER_ADMIN", "ECONOMIC_ANALYST")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @require_roles("SUPER_ADMIN", "ECONOMIC_ANALYST")
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        schedule = create_schedule(
            actor=request.user,
            data=serializer.validated_data,
            request=request,
        )
        output_serializer = self.get_serializer(schedule)
        headers = self.get_success_headers(output_serializer.data)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @extend_schema(
        summary="Pause schedule",
        description="Pause a forecast schedule. SUPER_ADMIN only.",
        tags=["Forecast Scheduling"],
        responses={200: ForecastScheduleSerializer},
    )
    @action(detail=True, methods=["put"], url_path="pause")
    @require_roles("SUPER_ADMIN")
    def pause(self, request, pk=None):
        schedule = self.get_object()
        schedule = pause_schedule(actor=request.user, schedule=schedule, request=request)
        serializer = self.get_serializer(schedule)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Resume schedule",
        description="Resume a paused forecast schedule. SUPER_ADMIN only.",
        tags=["Forecast Scheduling"],
        responses={200: ForecastScheduleSerializer},
    )
    @action(detail=True, methods=["put"], url_path="resume")
    @require_roles("SUPER_ADMIN")
    def resume(self, request, pk=None):
        schedule = self.get_object()
        schedule = resume_schedule(actor=request.user, schedule=schedule, request=request)
        serializer = self.get_serializer(schedule)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ForecastOrchestrateView(GenericAPIView):
    serializer_class = OrchestrateSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Forecast orchestration",
        description="Run orchestration across all active forecast schedules. SUPER_ADMIN and ECONOMIC_ANALYST.",
        tags=["Forecast Orchestration"],
        responses={202: OpenApiResponse(description="Orchestration triggered")},
    )
    def post(self, request):
        from apps.governance.permissions import _get_user_role_code

        role_code = _get_user_role_code(request.user)
        if role_code not in ("SUPER_ADMIN", "ECONOMIC_ANALYST") and not request.user.is_superuser:
            return Response({"detail": "Insufficient role."}, status=status.HTTP_403_FORBIDDEN)

        orchestrate_schedules(actor=request.user, request=request)
        return Response({"status": "orchestration-triggered"}, status=status.HTTP_202_ACCEPTED)

