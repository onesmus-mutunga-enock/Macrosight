from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ExternalSourceViewSet, ExternalIndicatorViewSet, ExternalIndicatorValueViewSet

router = DefaultRouter()
router.register(r"sources", ExternalSourceViewSet, basename="external-source")
router.register(r"indicators", ExternalIndicatorViewSet, basename="external-indicator")
router.register(r"values", ExternalIndicatorValueViewSet, basename="external-indicator-value")

urlpatterns = [
    path("", include(router.urls)),
]
