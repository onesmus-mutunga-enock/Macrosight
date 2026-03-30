from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    DatasetViewSet,
    FeatureSetViewSet,
    ModelRegistryViewSet,
    TrainingJobViewSet,
    ApproveModelPromotionView,
    audit_ml_code,
    audit_ml_config,
    audit_ml_dataset,
    audit_ml_features,
    data_drift,
    HpoRunView,
    HpoRunDetailView,
    HpoRunsListView,
    model_drift,
    RejectModelPromotionView,
)
from .urls_v1 import urlpatterns as v1_urlpatterns

router = DefaultRouter()
router.register(r"ml/datasets", DatasetViewSet, basename="ml-dataset")
router.register(r"ml/features", FeatureSetViewSet, basename="ml-features")
router.register(r"ml/models", ModelRegistryViewSet, basename="ml-models")
router.register(r"ml/train/jobs", TrainingJobViewSet, basename="ml-training-jobs")

urlpatterns = [
    *router.urls,
    # Training job create endpoint
    path("ml/train/", TrainingJobViewSet.create_training_job, name="ml-train"),
    # Model promotion admin endpoints
    path("ml/models/<uuid:id>/request-promotion/", ModelRegistryViewSet.request_promotion, name="ml-model-request-promotion"),
    path("admin/models/<uuid:id>/approve/", ApproveModelPromotionView.as_view(), name="ml-model-approve"),
    path("admin/models/<uuid:id>/reject/", RejectModelPromotionView.as_view(), name="ml-model-reject"),
    # HPO placeholder endpoints
    path("ml/hpo/run/", HpoRunView.as_view(), name="ml-hpo-run"),
    path("ml/hpo/runs/", HpoRunsListView.as_view(), name="ml-hpo-runs"),
    path("ml/hpo/runs/<uuid:id>/", HpoRunDetailView.as_view(), name="ml-hpo-run-detail"),
    # Drift detection placeholders
    path("ml/drift/data/", data_drift, name="ml-drift-data"),
    path("ml/drift/model/", model_drift, name="ml-drift-model"),
    # Training lineage audit endpoints
    path("audit/ml/dataset/<uuid:model_id>/", audit_ml_dataset, name="audit-ml-dataset"),
    path("audit/ml/features/<uuid:model_id>/", audit_ml_features, name="audit-ml-features"),
    path("audit/ml/config/<uuid:model_id>/", audit_ml_config, name="audit-ml-config"),
    path("audit/ml/code/<uuid:model_id>/", audit_ml_code, name="audit-ml-code"),
    
    # V1 Forecasting API endpoints
    *v1_urlpatterns,
]

