from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ScenarioViewSet,
    SimulationViewSet,
    ScenarioComparisonViewSet,
    ScenarioSimulationViewSet
)


router = DefaultRouter()
router.register(r'scenarios', ScenarioViewSet, basename='scenario')
router.register(r'simulations', SimulationViewSet, basename='simulation')
router.register(r'comparisons', ScenarioComparisonViewSet, basename='comparison')


urlpatterns = [
    path('', include(router.urls)),
    path('scenarios/<int:pk>/run-simulation/', ScenarioSimulationViewSet.as_view({'post': 'run_simulation'}), name='scenario-run-simulation'),
]