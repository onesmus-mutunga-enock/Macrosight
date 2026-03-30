from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SaleViewSet, SaleSummaryViewSet

router = DefaultRouter()
router.register(r"sales", SaleViewSet, basename="sale")
router.register(r"sales-summary", SaleSummaryViewSet, basename="sale-summary")

urlpatterns = [
    path("", include(router.urls)),
]