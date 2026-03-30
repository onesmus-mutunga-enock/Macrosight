from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views_v1

# V1 Forecasting API router
v1_router = DefaultRouter()
v1_router.register(r'datasets', views_v1.DatasetViewSet, basename='v1-dataset')
v1_router.register(r'feature-sets', views_v1.FeatureSetViewSet, basename='v1-feature-set')
v1_router.register(r'models', views_v1.ModelRegistryViewSet, basename='v1-model')
v1_router.register(r'forecast-results', views_v1.ForecastResultViewSet, basename='v1-forecast-result')
v1_router.register(r'explainability', views_v1.ModelExplainabilityViewSet, basename='v1-explainability')

urlpatterns = [
    path('', include(v1_router.urls)),
    
    # Development endpoints
    path('dev/pipeline/', views_v1.development_pipeline, name='v1_development_pipeline'),
    path('dev/train-linear/', views_v1.development_train_linear_model, name='v1_development_train_linear'),
    path('dev/forecast/', views_v1.development_generate_forecast, name='v1_development_generate_forecast'),
    path('dev/sample-data/', views_v1.development_sample_data, name='v1_development_sample_data'),
]