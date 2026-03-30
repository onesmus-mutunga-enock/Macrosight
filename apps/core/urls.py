from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TimeStampedModelViewSet

router = DefaultRouter()
router.register(r"time-stamped-models", TimeStampedModelViewSet, basename="time-stamped-model")

urlpatterns = [
    path("", include(router.urls)),
]