from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    AlertViewSet,
    DataSnapshotViewSet,
    admin_jobs_history,
    admin_jobs_list,
    admin_system_usage,
    dashboard_analyst,
    dashboard_audit,
    dashboard_data_feeder,
    dashboard_executive,
    AdminJobsPauseView,
    AdminJobsResumeView,
    SystemBackupView,
    system_config_get,
    system_config_put,
    system_health,
)

router = DefaultRouter()
router.register(r"data/snapshots", DataSnapshotViewSet, basename="data-snapshot")
router.register(r"alerts", AlertViewSet, basename="alert")

urlpatterns = [
    *router.urls,
    path("system/health/", system_health, name="system-health"),
    path("system/config/", system_config_get, name="system-config-get"),
    path("system/config/", system_config_put, name="system-config-put"),
    path("system/backup/", SystemBackupView.as_view(), name="system-backup"),
    path("admin/jobs/", admin_jobs_list, name="admin-jobs"),
    path("admin/jobs/<uuid:id>/pause/", AdminJobsPauseView.as_view(), name="admin-jobs-pause"),
    path("admin/jobs/<uuid:id>/resume/", AdminJobsResumeView.as_view(), name="admin-jobs-resume"),
    path("admin/jobs/history/", admin_jobs_history, name="admin-jobs-history"),
    path("admin/system/usage/", admin_system_usage, name="admin-system-usage"),
    path("dashboard/executive/", dashboard_executive, name="dashboard-executive"),
    path("dashboard/analyst/", dashboard_analyst, name="dashboard-analyst"),
    path("dashboard/audit/", dashboard_audit, name="dashboard-audit"),
    path("dashboard/data-feeder/", dashboard_data_feeder, name="dashboard-data-feeder"),
]

