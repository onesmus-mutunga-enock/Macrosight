from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from apps.governance.permissions import (
    SUPER_ADMIN,
    ECONOMIC_ANALYST,
    AUDITOR,
    EXECUTIVE_VIEWER,
    DATA_FEEDER
)
from .services.dashboard_service import DashboardService
from .models import Dashboard, DashboardWidget, DashboardData
from .serializers import (
    DashboardSerializer,
    DashboardWidgetSerializer,
    DashboardDataSerializer
)


class DashboardViewSet(viewsets.ModelViewSet):
    queryset = Dashboard.objects.all()
    serializer_class = DashboardSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role.code not in [SUPER_ADMIN, ECONOMIC_ANALYST]:
            return self.queryset.filter(created_by=user)
        return self.queryset


class DashboardWidgetViewSet(viewsets.ModelViewSet):
    queryset = DashboardWidget.objects.all()
    serializer_class = DashboardWidgetSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role.code not in [SUPER_ADMIN, ECONOMIC_ANALYST]:
            return self.queryset.filter(dashboard__created_by=user)
        return self.queryset


class DashboardDataViewSet(viewsets.ModelViewSet):
    queryset = DashboardData.objects.all()
    serializer_class = DashboardDataSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role.code not in [SUPER_ADMIN, ECONOMIC_ANALYST]:
            return self.queryset.filter(widget__dashboard__created_by=user)
        return self.queryset


class DashboardAggregationViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    # Generic serializer class to satisfy schema generation; endpoints return dicts
    serializer_class = DashboardDataSerializer

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def executive(self, request):
        user = request.user
        if user.role.code not in [SUPER_ADMIN, EXECUTIVE_VIEWER]:
            return Response(
                {"detail": "Not authorized to view executive dashboard."},
                status=status.HTTP_403_FORBIDDEN
            )

        service = DashboardService()
        data = service.get_executive_data()
        return Response(data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def analyst(self, request):
        user = request.user
        if user.role.code not in [SUPER_ADMIN, ECONOMIC_ANALYST]:
            return Response(
                {"detail": "Not authorized to view analyst dashboard."},
                status=status.HTTP_403_FORBIDDEN
            )

        service = DashboardService()
        data = service.get_analyst_data()
        return Response(data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def audit(self, request):
        user = request.user
        if user.role.code not in [SUPER_ADMIN, AUDITOR]:
            return Response(
                {"detail": "Not authorized to view audit dashboard."},
                status=status.HTTP_403_FORBIDDEN
            )

        service = DashboardService()
        data = service.get_audit_data()
        return Response(data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def data_feeder(self, request):
        user = request.user
        if user.role.code not in [SUPER_ADMIN, DATA_FEEDER]:
            return Response(
                {"detail": "Not authorized to view data feeder dashboard."},
                status=status.HTTP_403_FORBIDDEN
            )

        service = DashboardService()
        data = service.get_data_feeder_data()
        return Response(data, status=status.HTTP_200_OK)

