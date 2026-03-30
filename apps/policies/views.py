from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import serializers as drf_serializers


# Named serializer for schema generation
class PolicySimulationAnalysisSerializer(drf_serializers.Serializer):
    params = drf_serializers.JSONField(required=False)

SUPER_ADMIN = "SUPER_ADMIN"
ECONOMIC_ANALYST = "ECONOMIC_ANALYST"
DATA_SCIENTIST = "DATA_SCIENTIST"

from .models import PolicySimulation, PolicyImpactAnalysis, PolicySimulationComparison
from .serializers import (
    PolicySimulationSerializer,
    PolicyImpactAnalysisSerializer,
    PolicySimulationComparisonSerializer
)


class PolicySimulationViewSet(viewsets.ModelViewSet):
    queryset = PolicySimulation.objects.all()
    serializer_class = PolicySimulationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role.code not in [SUPER_ADMIN, DATA_SCIENTIST]:
            return self.queryset.filter(created_by=user)
        return self.queryset


class PolicyImpactAnalysisViewSet(viewsets.ModelViewSet):
    queryset = PolicyImpactAnalysis.objects.all()
    serializer_class = PolicyImpactAnalysisSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role.code not in [SUPER_ADMIN, ECONOMIC_ANALYST]:
            return self.queryset.filter(simulation__created_by=user)
        return self.queryset


class PolicySimulationComparisonViewSet(viewsets.ModelViewSet):
    queryset = PolicySimulationComparison.objects.all()
    serializer_class = PolicySimulationComparisonSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role.code not in [SUPER_ADMIN, ECONOMIC_ANALYST]:
            return self.queryset.filter(created_by=user)
        return self.queryset


class PolicySimulationAnalysisViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = PolicySimulationAnalysisSerializer

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def run_analysis(self, request, pk=None):
        user = request.user
        if user.role.code not in [SUPER_ADMIN, DATA_SCIENTIST]:
            return Response(
                {"detail": "Not authorized to run policy analysis."},
                status=status.HTTP_403_FORBIDDEN
            )

        # Implementation for running policy analysis would go here
        return Response(
            {"detail": "Policy analysis running"},
            status=status.HTTP_202_ACCEPTED
        )