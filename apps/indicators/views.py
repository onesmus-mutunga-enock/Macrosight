from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiResponse

from apps.governance.permissions import admin_only, require_roles

from .models import Indicator, IndicatorVersion
from .serializers import IndicatorSerializer, IndicatorVersionSerializer
from .services import (
    create_indicator,
    delete_indicator,
    record_indicator_ingestion,
    update_indicator,
)


@extend_schema_view(
    list=extend_schema(
        summary="List indicators",
        description="List external indicators. ECONOMIC_ANALYST role required.",
        tags=["Indicators"],
        responses={200: IndicatorSerializer},
    ),
    retrieve=extend_schema(
        summary="Retrieve indicator",
        description="Retrieve a specific indicator. ECONOMIC_ANALYST role required.",
        tags=["Indicators"],
        responses={200: IndicatorSerializer},
    ),
    create=extend_schema(
        summary="Create indicator",
        description="Create a new indicator. ECONOMIC_ANALYST role required.",
        tags=["Indicators"],
        responses={201: IndicatorSerializer},
    ),
    update=extend_schema(
        summary="Update indicator",
        description="Update an indicator. ECONOMIC_ANALYST role required.",
        tags=["Indicators"],
        responses={200: IndicatorSerializer},
    ),
    partial_update=extend_schema(
        summary="Partially update indicator",
        description="Partially update an indicator. ECONOMIC_ANALYST role required.",
        tags=["Indicators"],
        responses={200: IndicatorSerializer},
    ),
    destroy=extend_schema(
        summary="Delete indicator",
        description="Delete an indicator. SUPER_ADMIN only.",
        tags=["Indicators"],
        responses={204: OpenApiResponse(description="Indicator deleted")},
    ),
)
class IndicatorViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """
    External Indicators API:

    Analyst:
    - GET  /api/v1/indicators/
    - POST /api/v1/indicators/
    - PUT  /api/v1/indicators/{id}/

    Admin:
    - DELETE /api/v1/indicators/{id}/
    - POST   /api/v1/admin/indicators/sync/
    - PUT    /api/v1/admin/indicators/source/
    - GET    /api/v1/admin/indicators/quality-report/
    - GET    /api/v1/admin/indicators/ingestion-log/
    """

    queryset = Indicator.objects.all()
    serializer_class = IndicatorSerializer
    permission_classes = [IsAuthenticated]

    @require_roles("ECONOMIC_ANALYST")
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        indicator = create_indicator(
            actor=request.user, data=serializer.validated_data, request=request
        )
        output_serializer = self.get_serializer(indicator)
        headers = self.get_success_headers(output_serializer.data)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @require_roles("ECONOMIC_ANALYST")
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        mutable_data = {
            key: value
            for key, value in serializer.validated_data.items()
            if key in {"code", "name", "description", "source", "is_active", "metadata"}
        }
        indicator = update_indicator(
            actor=request.user,
            indicator=instance,
            updated_fields=mutable_data,
            request=request,
        )
        output_serializer = self.get_serializer(indicator)
        return Response(output_serializer.data)

    @require_roles("ECONOMIC_ANALYST")
    def partial_update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return self.update(request, *args, **kwargs)

    @require_roles("ECONOMIC_ANALYST")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @require_roles("ECONOMIC_ANALYST")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @admin_only
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        delete_indicator(actor=request.user, indicator=instance, request=request)
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(
    summary="Sync indicators from external sources",
    description="Admin-only operation to trigger indicator synchronization pipeline.",
    tags=["Indicators Admin"],
    responses={202: OpenApiResponse(description="Sync accepted")},
)
@admin_only
def indicators_sync(request):
    # Placeholder for future async job trigger.
    return Response({"status": "sync-accepted"}, status=status.HTTP_202_ACCEPTED)


@extend_schema(
    summary="Update global indicator source configuration",
    description="Admin-only endpoint to update system-wide indicator source settings.",
    tags=["Indicators Admin"],
    responses={200: OpenApiResponse(description="Source configuration updated")},
)
@admin_only
def indicators_source_update(request):
    # Placeholder for future configuration persistence.
    return Response({"status": "source-updated", "payload": request.data}, status=status.HTTP_200_OK)


@extend_schema(
    summary="Indicator quality report",
    description="Admin-only aggregated view of indicator ingestion quality.",
    tags=["Indicators Admin"],
    responses={200: IndicatorVersionSerializer(many=True)},
)
@admin_only
def indicators_quality_report(request):
    versions = IndicatorVersion.objects.all().order_by("-ingestion_timestamp")[:200]
    serializer = IndicatorVersionSerializer(versions, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(
    summary="Indicator ingestion log",
    description="Admin-only view of recent indicator ingestion events.",
    tags=["Indicators Admin"],
    responses={200: IndicatorVersionSerializer(many=True)},
)
@admin_only
def indicators_ingestion_log(request):
    versions = IndicatorVersion.objects.all().order_by("-ingestion_timestamp")[:200]
    serializer = IndicatorVersionSerializer(versions, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

