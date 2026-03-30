from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import ExternalIndicator, ExternalIndicatorValue, ExternalSource
from .serializers import ExternalIndicatorSerializer, ExternalIndicatorValueSerializer, ExternalSourceSerializer


class ExternalSourceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ExternalSource.objects.all()
    serializer_class = ExternalSourceSerializer
    permission_classes = [IsAuthenticated]


class ExternalIndicatorViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ExternalIndicator.objects.all()
    serializer_class = ExternalIndicatorSerializer
    permission_classes = [IsAuthenticated]


class ExternalIndicatorValueViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ExternalIndicatorValue.objects.all()
    serializer_class = ExternalIndicatorValueSerializer
    permission_classes = [IsAuthenticated]
