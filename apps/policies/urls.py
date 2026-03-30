from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PolicySimulationViewSet,
    PolicyImpactAnalysisViewSet,
    PolicySimulationComparisonViewSet,
    PolicySimulationAnalysisViewSet
)


router = DefaultRouter()
router.register(r'simulations', PolicySimulationViewSet, basename='policy-simulation')
router.register(r'impact-analyses', PolicyImpactAnalysisViewSet, basename='policy-impact-analysis')
router.register(r'comparisons', PolicySimulationComparisonViewSet, basename='policy-comparison')


urlpatterns = [
    path('', include(router.urls)),
    path('simulations/<int:pk>/run-analysis/', PolicySimulationAnalysisViewSet.as_view({'post': 'run_analysis'}), name='policy-simulation-run-analysis'),
]