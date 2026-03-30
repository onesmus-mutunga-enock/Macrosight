from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    ForecastScheduleViewSet,
    ForecastViewSet,
    forecast_accuracy,
    forecast_delta,
    InvalidateForecastView,
    ForecastActualsView,
    ForecastOrchestrateView,
)

router = DefaultRouter()
router.register(r"forecasts", ForecastViewSet, basename="forecast")
router.register(r"forecasts/schedules", ForecastScheduleViewSet, basename="forecast-schedule")

urlpatterns = [
    *router.urls,
    # Admin invalidate endpoint
    path("admin/forecasts/<uuid:id>/invalidate/", InvalidateForecastView.as_view(), name="forecast-invalidate"),
    # Forecast accuracy & delta comparison & actuals
    path("forecasts/<uuid:id>/actuals/", ForecastActualsView.as_view(), name="forecast-actuals"),
    path("forecasts/<uuid:id>/accuracy/", forecast_accuracy, name="forecast-accuracy"),
    path("forecasts/<uuid:id>/delta/", forecast_delta, name="forecast-delta"),
    # Orchestration
    path("forecasts/orchestrate/", ForecastOrchestrateView.as_view(), name="forecast-orchestrate"),
]

