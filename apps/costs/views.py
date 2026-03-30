from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import InputCost, InputCostValue
from .serializers import InputCostSerializer, InputCostValueSerializer


class InputCostViewSet(viewsets.ModelViewSet):
    queryset = InputCost.objects.all()
    serializer_class = InputCostSerializer
    permission_classes = [IsAuthenticated]


class InputCostValueViewSet(viewsets.ModelViewSet):
    queryset = InputCostValue.objects.all()
    serializer_class = InputCostValueSerializer
    permission_classes = [IsAuthenticated]