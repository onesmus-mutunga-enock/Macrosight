from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework import serializers as drf_serializers


# Named serializer so schema tools produce a valid component name
class GovernmentNoticeAnalysisSerializer(drf_serializers.Serializer):
    query = drf_serializers.CharField(required=False)
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from apps.governance.permissions import (
    SUPER_ADMIN,
    ECONOMIC_ANALYST,
    DATA_FEEDER
)
from .models import GovernmentNotice, NoticeImpact, NoticeSectorImpact
from .serializers import (
    GovernmentNoticeSerializer,
    NoticeImpactSerializer,
    NoticeSectorImpactSerializer
)


class GovernmentNoticeViewSet(viewsets.ModelViewSet):
    queryset = GovernmentNotice.objects.all()
    serializer_class = GovernmentNoticeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role.code not in [SUPER_ADMIN, ECONOMIC_ANALYST]:
            return self.queryset.filter(created_by=user)
        return self.queryset


class NoticeImpactViewSet(viewsets.ModelViewSet):
    queryset = NoticeImpact.objects.all()
    serializer_class = NoticeImpactSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role.code not in [SUPER_ADMIN, ECONOMIC_ANALYST]:
            return self.queryset.filter(notice__created_by=user)
        return self.queryset


class NoticeSectorImpactViewSet(viewsets.ModelViewSet):
    queryset = NoticeSectorImpact.objects.all()
    serializer_class = NoticeSectorImpactSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role.code not in [SUPER_ADMIN, ECONOMIC_ANALYST]:
            return self.queryset.filter(notice__created_by=user)
        return self.queryset


class GovernmentNoticeAnalysisViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    # Provide a named serializer for schema generation tools
    serializer_class = GovernmentNoticeAnalysisSerializer

    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def impact_analysis(self, request, pk=None):
        user = request.user
        if user.role.code not in [SUPER_ADMIN, ECONOMIC_ANALYST]:
            return Response(
                {"detail": "Not authorized to view impact analysis."},
                status=status.HTTP_403_FORBIDDEN
            )

        # Implementation for impact analysis would go here
        return Response(
            {"detail": "Impact analysis results"},
            status=status.HTTP_200_OK
        )