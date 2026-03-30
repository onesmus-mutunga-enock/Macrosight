from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    GovernmentNoticeViewSet,
    NoticeImpactViewSet,
    NoticeSectorImpactViewSet,
    GovernmentNoticeAnalysisViewSet
)


router = DefaultRouter()
router.register(r'notices', GovernmentNoticeViewSet, basename='government-notice')
router.register(r'impact-analyses', NoticeImpactViewSet, basename='notice-impact')
router.register(r'sector-impacts', NoticeSectorImpactViewSet, basename='notice-sector-impact')


urlpatterns = [
    path('', include(router.urls)),
    path('notices/<int:pk>/impact-analysis/', GovernmentNoticeAnalysisViewSet.as_view({'get': 'impact_analysis'}), name='government-notice-impact-analysis'),
]