from rest_framework import viewsets
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from .services.ingestion_service import SalesIngestionService
from django.http import HttpResponse
from .models import Sale, SaleSummary
from .serializers import SaleSerializer, SaleSummarySerializer


class SaleViewSet(viewsets.ModelViewSet):
    queryset = Sale.objects.all()
    serializer_class = SaleSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'])
    def upload(self, request):
        if 'file' not in request.FILES:
            return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
        csv_file = request.FILES['file'].read().decode('utf-8')
        service = SalesIngestionService()
        result = service.process_csv(csv_file, request.user.id)
        return Response(result, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def status(self, request):
        ingestion_id = request.query_params.get('ingestion_id')
        if not ingestion_id:
            return Response({'error': 'ingestion_id required'}, status=status.HTTP_400_BAD_REQUEST)
        service = SalesIngestionService()
        status_data = service.get_status(ingestion_id)
        return Response(status_data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def export(self, request):
        service = SalesIngestionService()
        csv_content = service.export_csv(self.queryset.all())
        response = HttpResponse(csv_content, content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=\"sales.csv\"'
        return response


class SaleSummaryViewSet(viewsets.ModelViewSet):
    queryset = SaleSummary.objects.all()
    serializer_class = SaleSummarySerializer
    permission_classes = [IsAuthenticated]