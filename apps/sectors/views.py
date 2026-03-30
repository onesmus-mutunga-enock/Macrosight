from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Sector
from .serializers import SectorSerializer


class SectorViewSet(viewsets.ModelViewSet):
    queryset = Sector.objects.all()
    serializer_class = SectorSerializer
    permission_classes = [IsAuthenticated]