from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from apps.governance.permissions import (
    SUPER_ADMIN,
    ECONOMIC_ANALYST,
    DATA_FEEDER
)
from .models import Fertilizer, Seed, Pesticide, Fuel, InputSummary
from .serializers import (
    FertilizerSerializer,
    SeedSerializer,
    PesticideSerializer,
    FuelSerializer,
    InputSummarySerializer
)


class FertilizerViewSet(viewsets.ModelViewSet):
    queryset = Fertilizer.objects.all()
    serializer_class = FertilizerSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role.code not in [SUPER_ADMIN, ECONOMIC_ANALYST]:
            return self.queryset.filter(is_active=True)
        return self.queryset


class SeedViewSet(viewsets.ModelViewSet):
    queryset = Seed.objects.all()
    serializer_class = SeedSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role.code not in [SUPER_ADMIN, ECONOMIC_ANALYST]:
            return self.queryset.filter(is_active=True)
        return self.queryset


class PesticideViewSet(viewsets.ModelViewSet):
    queryset = Pesticide.objects.all()
    serializer_class = PesticideSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role.code not in [SUPER_ADMIN, ECONOMIC_ANALYST]:
            return self.queryset.filter(is_active=True)
        return self.queryset


class FuelViewSet(viewsets.ModelViewSet):
    queryset = Fuel.objects.all()
    serializer_class = FuelSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role.code not in [SUPER_ADMIN, ECONOMIC_ANALYST]:
            return self.queryset.filter(is_active=True)
        return self.queryset


class InputSummaryViewSet(viewsets.ModelViewSet):
    queryset = InputSummary.objects.all()
    serializer_class = InputSummarySerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def summary(self, request):
        user = request.user
        if user.role.code not in [SUPER_ADMIN, ECONOMIC_ANALYST]:
            return Response(
                {"detail": "Not authorized to view summary."},
                status=status.HTTP_403_FORBIDDEN
            )

        summaries = InputSummary.objects.all()
        serializer = self.get_serializer(summaries, many=True)
        return Response(serializer.data)