from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    IndicatorViewSet,
    indicators_ingestion_log,
    indicators_quality_report,
    indicators_source_update,
    indicators_sync,
)

router = DefaultRouter()
router.register(r"indicators", IndicatorViewSet, basename="indicator")

urlpatterns = [
    *router.urls,
    path("admin/indicators/sync/", indicators_sync, name="indicators-sync"),
    path("admin/indicators/source/", indicators_source_update, name="indicators-source"),
    path("admin/indicators/quality-report/", indicators_quality_report, name="indicators-quality"),
    path("admin/indicators/ingestion-log/", indicators_ingestion_log, name="indicators-ingestion"),
]

