from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DashboardViewSet,
    DashboardWidgetViewSet,
    DashboardDataViewSet,
    DashboardAggregationViewSet
)


router = DefaultRouter()
router.register(r'dashboards', DashboardViewSet, basename='dashboard')
router.register(r'widgets', DashboardWidgetViewSet, basename='dashboard-widget')
router.register(r'data', DashboardDataViewSet, basename='dashboard-data')


urlpatterns = [
    path('', include(router.urls)),
    path('aggregation/executive/', DashboardAggregationViewSet.as_view({'get': 'executive'}), name='dashboard-aggregation-executive'),
    path('aggregation/analyst/', DashboardAggregationViewSet.as_view({'get': 'analyst'}), name='dashboard-aggregation-analyst'),
    path('aggregation/audit/', DashboardAggregationViewSet.as_view({'get': 'audit'}), name='dashboard-aggregation-audit'),
    path('aggregation/data-feeder/', DashboardAggregationViewSet.as_view({'get': 'data_feeder'}), name='dashboard-aggregation-data-feeder'),
]