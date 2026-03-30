from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import AgriculturalInput, AgriculturalInputValue
from .serializers import AgriculturalInputSerializer, AgriculturalInputValueSerializer


class AgriculturalInputViewSet(viewsets.ModelViewSet):
    queryset = AgriculturalInput.objects.all()
    serializer_class = AgriculturalInputSerializer
    permission_classes = [IsAuthenticated]


class AgriculturalInputValueViewSet(viewsets.ModelViewSet):
    queryset = AgriculturalInputValue.objects.all()
    serializer_class = AgriculturalInputValueSerializer
    permission_classes = [IsAuthenticated]