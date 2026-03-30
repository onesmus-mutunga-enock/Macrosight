from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import InputCostViewSet, InputCostValueViewSet

router = DefaultRouter()
router.register(r"input-costs", InputCostViewSet, basename="input-cost")
router.register(r"input-cost-values", InputCostValueViewSet, basename="input-cost-value")

urlpatterns = [
    path("", include(router.urls)),
]