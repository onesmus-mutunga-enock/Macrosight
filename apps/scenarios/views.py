from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import serializers as drf_serializers
from drf_spectacular.utils import extend_schema
from apps.governance.permissions import (
    SUPER_ADMIN,
    ECONOMIC_ANALYST,
    DATA_SCIENTIST
)
from .models import Scenario, Simulation, ScenarioComparison
from .serializers import (
    ScenarioSerializer,
    SimulationSerializer,
    ScenarioComparisonSerializer
)


class ScenarioViewSet(viewsets.ModelViewSet):
    queryset = Scenario.objects.all()
    serializer_class = ScenarioSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role.code not in [SUPER_ADMIN, ECONOMIC_ANALYST]:
            return self.queryset.filter(created_by=user)
        return self.queryset


class SimulationViewSet(viewsets.ModelViewSet):
    queryset = Simulation.objects.all()
    serializer_class = SimulationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role.code not in [SUPER_ADMIN, DATA_SCIENTIST]:
            return self.queryset.filter(created_by=user)
        return self.queryset


class ScenarioComparisonViewSet(viewsets.ModelViewSet):
    queryset = ScenarioComparison.objects.all()
    serializer_class = ScenarioComparisonSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role.code not in [SUPER_ADMIN, ECONOMIC_ANALYST]:
            return self.queryset.filter(created_by=user)
        return self.queryset


class SimulationRunRequestSerializer(drf_serializers.Serializer):
    run_options = drf_serializers.JSONField(required=False)


class ScenarioSimulationViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = SimulationRunRequestSerializer

    @extend_schema(request=SimulationRunRequestSerializer, responses={202: None})
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def run_simulation(self, request, pk=None):
        user = request.user
        if user.role.code not in [SUPER_ADMIN, DATA_SCIENTIST]:
            return Response(
                {"detail": "Not authorized to run simulations."},
                status=status.HTTP_403_FORBIDDEN
            )

        # Implementation for running simulation would go here
        return Response(
            {"detail": "Simulation running"},
            status=status.HTTP_202_ACCEPTED
        )