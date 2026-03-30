from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    FertilizerViewSet,
    SeedViewSet,
    PesticideViewSet,
    FuelViewSet,
    InputSummaryViewSet
)


router = DefaultRouter()
router.register(r'fertilizers', FertilizerViewSet, basename='fertilizer')
router.register(r'seeds', SeedViewSet, basename='seed')
router.register(r'pesticides', PesticideViewSet, basename='pesticide')
router.register(r'fuels', FuelViewSet, basename='fuel')
router.register(r'summaries', InputSummaryViewSet, basename='input-summary')


urlpatterns = [
    path('', include(router.urls)),
    path('summary/', InputSummaryViewSet.as_view({'get': 'summary'}), name='input-summary-list'),
]