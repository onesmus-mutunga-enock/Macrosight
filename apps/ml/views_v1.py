from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import json

from .models import Dataset, FeatureSet, ModelRegistry, ForecastResult, ModelExplainability
from .serializers import (
    DatasetSerializer, FeatureSetSerializer, ModelRegistrySerializer,
    ForecastResultSerializer, ModelExplainabilitySerializer
)
from .services.feature_engineering import FeatureEngineeringService
from .services.linear_regression_model import LinearRegressionModelService
from .services.econometric_explainability import EconometricExplainabilityService
from .services.forecast_engine import ForecastEngineService
from apps.forecasts.models import Forecast


class DatasetViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing ML datasets.
    """
    queryset = Dataset.objects.all()
    serializer_class = DatasetSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['post'])
    def generate_features(self, request, pk=None):
        """Generate features for a dataset."""
        dataset = self.get_object()
        
        try:
            feature_service = FeatureEngineeringService(dataset)
            feature_set = feature_service.generate_features()
            
            serializer = FeatureSetSerializer(feature_set)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )


class FeatureSetViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing feature sets.
    """
    queryset = FeatureSet.objects.all()
    serializer_class = FeatureSetSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['post'])
    def train_model(self, request, pk=None):
        """Train a Linear Regression model on this feature set."""
        feature_set = self.get_object()
        
        try:
            model_service = LinearRegressionModelService(feature_set)
            model_registry = model_service.train_model()
            
            serializer = ModelRegistrySerializer(model_registry)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def train_multitarget(self, request, pk=None):
        """Train both sales and price models when available."""
        feature_set = self.get_object()

        try:
            from apps.ml.services.multi_target_service import MultiTargetTrainer
            trainer = MultiTargetTrainer(feature_set)
            results = trainer.train()
            return Response(results, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ModelRegistryViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing ML model registry.
    """
    queryset = ModelRegistry.objects.all()
    serializer_class = ModelRegistrySerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['post'])
    def promote(self, request, pk=None):
        """Promote a model to ACTIVE status."""
        model_registry = self.get_object()
        
        if LinearRegressionModelService.promote_model(model_registry):
            serializer = ModelRegistrySerializer(model_registry)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(
                {'error': 'Model does not meet quality thresholds for promotion'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['get'])
    def explainability(self, request, pk=None):
        """Get econometric explainability analysis for a model."""
        model_registry = self.get_object()
        
        try:
            explainability_service = EconometricExplainabilityService(model_registry)
            explainability = explainability_service.generate_explainability()
            
            serializer = ModelExplainabilitySerializer(explainability)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['get'])
    def quality_report(self, request, pk=None):
        """Get comprehensive model quality report."""
        model_registry = self.get_object()
        
        try:
            explainability_service = EconometricExplainabilityService(model_registry)
            report = explainability_service.get_model_quality_report()
            
            return Response(report, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )


class ForecastResultViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for viewing forecast results.
    """
    queryset = ForecastResult.objects.all()
    serializer_class = ForecastResultSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'])
    def generate(self, request):
        """Generate forecasts using a trained model."""
        model_id = request.data.get('model_id')
        forecast_id = request.data.get('forecast_id')
        horizon_months = request.data.get('horizon_months', 12)
        
        if not model_id or not forecast_id:
            return Response(
                {'error': 'model_id and forecast_id are required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        model_registry = get_object_or_404(ModelRegistry, id=model_id, status='ACTIVE')
        forecast = get_object_or_404(Forecast, id=forecast_id)
        
        try:
            engine = ForecastEngineService(model_registry)
            results = engine.generate_forecast(forecast, horizon_months)
            
            serializer = ForecastResultSerializer(results, many=True)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )


class ModelExplainabilityViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for viewing model explainability results.
    """
    queryset = ModelExplainability.objects.all()
    serializer_class = ModelExplainabilitySerializer
    permission_classes = [IsAuthenticated]


# Development Endpoints (for testing the complete pipeline)
@method_decorator(csrf_exempt, name='dispatch')
def development_pipeline(request):
    """
    Development endpoint to test the complete ML pipeline.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Step 1: Create dataset
            dataset_data = data.get('dataset', {})
            dataset = Dataset.objects.create(
                name=dataset_data.get('name', 'Development Dataset'),
                description=dataset_data.get('description', 'Auto-generated for development'),
                definition=dataset_data.get('definition', {}),
                created_by_id=1  # Default user
            )
            
            # Step 2: Generate features
            feature_service = FeatureEngineeringService(dataset)
            feature_set = feature_service.generate_features()
            
            # Step 3: Train model
            model_service = LinearRegressionModelService(feature_set)
            model_registry = model_service.train_model()
            
            # Step 4: Generate explainability
            explainability_service = EconometricExplainabilityService(model_registry)
            explainability = explainability_service.generate_explainability()
            
            # Step 5: Generate sample forecasts (if forecast_id provided)
            forecast_results = []
            if 'forecast_id' in data:
                forecast = get_object_or_404(Forecast, id=data['forecast_id'])
                engine = ForecastEngineService(model_registry)
                results = engine.generate_forecast(forecast, data.get('horizon_months', 6))
                forecast_results = [str(r.id) for r in results]
            
            response_data = {
                'dataset_id': str(dataset.id),
                'feature_set_id': str(feature_set.id),
                'model_id': str(model_registry.id),
                'explainability_id': str(explainability.id),
                'forecast_results': forecast_results,
                'status': 'success'
            }
            
            return JsonResponse(response_data, status=201)
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'POST method required'}, status=405)


@method_decorator(csrf_exempt, name='dispatch')
def development_train_linear_model(request):
    """
    Development endpoint to train a Linear Regression model.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            feature_set_id = data.get('feature_set_id')
            
            if not feature_set_id:
                return JsonResponse({'error': 'feature_set_id is required'}, status=400)
            
            feature_set = get_object_or_404(FeatureSet, id=feature_set_id)
            
            # Train model
            model_service = LinearRegressionModelService(feature_set)
            model_registry = model_service.train_model()
            
            # Generate explainability
            explainability_service = EconometricExplainabilityService(model_registry)
            explainability = explainability_service.generate_explainability()
            
            response_data = {
                'model_id': str(model_registry.id),
                'model_name': model_registry.name,
                'status': model_registry.status,
                'metrics': model_registry.metrics,
                'explainability_id': str(explainability.id),
                'status': 'success'
            }
            
            return JsonResponse(response_data, status=201)
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'POST method required'}, status=405)


@method_decorator(csrf_exempt, name='dispatch')
def development_generate_forecast(request):
    """
    Development endpoint to generate forecasts.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            model_id = data.get('model_id')
            forecast_id = data.get('forecast_id')
            horizon_months = data.get('horizon_months', 12)
            
            if not model_id or not forecast_id:
                return JsonResponse({'error': 'model_id and forecast_id are required'}, status=400)
            
            model_registry = get_object_or_404(ModelRegistry, id=model_id, status='ACTIVE')
            forecast = get_object_or_404(Forecast, id=forecast_id)
            
            # Generate forecasts
            engine = ForecastEngineService(model_registry)
            results = engine.generate_forecast(forecast, horizon_months)
            
            # Get quality validation
            quality = engine.validate_forecast_quality(results)
            
            response_data = {
                'forecast_id': str(forecast.id),
                'model_id': str(model_registry.id),
                'results_count': len(results),
                'results': [
                    {
                        'id': str(r.id),
                        'prediction_date': r.prediction_date.isoformat(),
                        'predicted_value': float(r.predicted_value),
                        'confidence_lower': float(r.confidence_lower),
                        'confidence_upper': float(r.confidence_upper),
                        'horizon_months': r.horizon_months
                    }
                    for r in results
                ],
                'quality_validation': quality,
                'status': 'success'
            }
            
            return JsonResponse(response_data, status=201)
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'POST method required'}, status=405)


@method_decorator(csrf_exempt, name='dispatch')
def development_sample_data(request):
    """
    Development endpoint to load sample data for testing.
    """
    if request.method == 'POST':
        try:
            # This would load sample sales data, indicators, policies, etc.
            # For now, return success message
            response_data = {
                'message': 'Sample data loading endpoint - implement based on your data models',
                'status': 'success'
            }
            
            return JsonResponse(response_data, status=201)
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'POST method required'}, status=405)