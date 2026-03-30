from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AgriculturalInputViewSet, AgriculturalInputValueViewSet

router = DefaultRouter()
router.register(r"agricultural-inputs", AgriculturalInputViewSet, basename="agricultural-input")
router.register(r"agricultural-input-values", AgriculturalInputValueViewSet, basename="agricultural-input-value")

urlpatterns = [
    path("", include(router.urls)),
]