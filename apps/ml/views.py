from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action, permission_classes, api_view
from rest_framework.permissions import IsAuthenticated
from rest_framework import serializers as drf_serializers
from rest_framework.generics import GenericAPIView
from django.utils.decorators import method_decorator


# Small named serializers for schema generation
class HpoRunSerializer(drf_serializers.Serializer):
    config = drf_serializers.JSONField(required=False)

from rest_framework.response import Response

from django.shortcuts import get_object_or_404

from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
)

from apps.audit.models import AuditLog
from apps.governance.permissions import HasAnyRole, admin_only, require_roles, _get_user_role_code

from .models import Dataset, FeatureSet, ModelRegistry, TrainingJob
from .serializers import (
    DatasetSerializer,
    FeatureSetSerializer,
    ModelRegistrySerializer,
    TrainingJobCreateSerializer,
    TrainingJobSerializer,
)
from .services.ml_services import (
    cancel_training_job,
    create_dataset,
    create_feature_set,
    create_model_registry_entry,
    promote_model,
    request_training_job,
)


@extend_schema_view(
    list=extend_schema(
        summary="List training datasets",
        description="List versioned training datasets. DATA_SCIENTIST only.",
        tags=["ML Datasets"],
        responses={200: DatasetSerializer},
    ),
    retrieve=extend_schema(
        summary="Retrieve dataset",
        description="Retrieve a dataset by ID. DATA_SCIENTIST only.",
        tags=["ML Datasets"],
        responses={200: DatasetSerializer},
    ),
    create=extend_schema(
        summary="Build training dataset",
        description="Build a versioned training dataset from approved sources. DATA_SCIENTIST only.",
        tags=["ML Datasets"],
        responses={201: DatasetSerializer},
    ),
    destroy=extend_schema(
        summary="Delete dataset",
        description="Delete a training dataset. SUPER_ADMIN or DATA_SCIENTIST.",
        tags=["ML Datasets"],
        responses={204: OpenApiResponse(description="Dataset deleted")},
    ),
)
class DatasetViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """
    Training Dataset Builder API:

    - POST /api/v1/ml/datasets/build/
    - GET  /api/v1/ml/datasets/
    - GET  /api/v1/ml/datasets/{id}/
    - DELETE /api/v1/ml/datasets/{id}/
    """

    queryset = Dataset.objects.all()
    serializer_class = DatasetSerializer
    permission_classes = [IsAuthenticated]

    @require_roles("DATA_SCIENTIST")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @require_roles("DATA_SCIENTIST")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary="Build dataset",
        description="Alias for dataset creation endpoint. Role: DATA_SCIENTIST.",
        tags=["ML Datasets"],
        responses={201: DatasetSerializer},
        examples=[
            OpenApiExample(
                "Build dataset request",
                value={
                    "name": "Training Dataset FY2025",
                    "description": "Sales + indicators + policies for FY2025.",
                    "definition": {
                        "sales_snapshot_id": "00000000-0000-0000-0000-000000000010",
                        "indicator_version_id": "00000000-0000-0000-0000-000000000011",
                        "policy_version_id": "00000000-0000-0000-0000-000000000012",
                        "sector_scope": ["AGRICULTURE", "MANUFACTURING"],
                        "date_range": ["2025-01-01", "2025-12-31"],
                    },
                },
                request_only=True,
            ),
        ],
    )
    @action(detail=False, methods=["post"], url_path="build")
    @require_roles("DATA_SCIENTIST")
    def build(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        dataset = create_dataset(actor=request.user, data=serializer.validated_data, request=request)
        output = self.get_serializer(dataset)
        return Response(output.data, status=status.HTTP_201_CREATED)

    @require_roles("SUPER_ADMIN", "DATA_SCIENTIST")
    def create(self, request, *args, **kwargs):
        return self.build(request)

    @require_roles("SUPER_ADMIN", "DATA_SCIENTIST")
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema_view(
    list=extend_schema(
        summary="List feature sets",
        description="List feature engineering configurations. DATA_SCIENTIST only.",
        tags=["ML Features"],
        responses={200: FeatureSetSerializer},
    ),
    retrieve=extend_schema(
        summary="Retrieve feature set",
        description="Retrieve a feature set by ID. DATA_SCIENTIST only.",
        tags=["ML Features"],
        responses={200: FeatureSetSerializer},
    ),
    create=extend_schema(
        summary="Generate feature set",
        description="Generate features for ML training. DATA_SCIENTIST only.",
        tags=["ML Features"],
        responses={201: FeatureSetSerializer},
    ),
    update=extend_schema(
        summary="Update feature set",
        description="Update feature engineering configuration. DATA_SCIENTIST only.",
        tags=["ML Features"],
        responses={200: FeatureSetSerializer},
    ),
    destroy=extend_schema(
        summary="Delete feature set",
        description="Delete a feature set. DATA_SCIENTIST only.",
        tags=["ML Features"],
        responses={204: OpenApiResponse(description="Feature set deleted")},
    ),
)
class FeatureSetViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """
    Feature Engineering API:

    - POST /api/v1/ml/features/generate/
    - GET  /api/v1/ml/features/
    - GET  /api/v1/ml/features/{id}/
    - PUT  /api/v1/ml/features/{id}/
    - DELETE /api/v1/ml/features/{id}/
    """

    queryset = FeatureSet.objects.all()
    serializer_class = FeatureSetSerializer
    permission_classes = [IsAuthenticated]

    @require_roles("DATA_SCIENTIST")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @require_roles("DATA_SCIENTIST")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary="Generate feature set",
        description="Alias for feature set creation endpoint.",
        tags=["ML Features"],
        responses={201: FeatureSetSerializer},
    )
    @action(detail=False, methods=["post"], url_path="generate")
    @require_roles("DATA_SCIENTIST")
    def generate(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        feature_set = create_feature_set(
            actor=request.user, data=serializer.validated_data, request=request
        )
        output = self.get_serializer(feature_set)
        return Response(output.data, status=status.HTTP_201_CREATED)

    @require_roles("DATA_SCIENTIST")
    def create(self, request, *args, **kwargs):
        return self.generate(request)

    @require_roles("DATA_SCIENTIST")
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        instance.spec = serializer.validated_data.get("spec", instance.spec)
        instance.save(update_fields=["spec"])
        output = self.get_serializer(instance)
        return Response(output.data)

    @require_roles("DATA_SCIENTIST")
    def partial_update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return self.update(request, *args, **kwargs)

    @require_roles("DATA_SCIENTIST")
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema_view(
    list=extend_schema(
        summary="List models",
        description="List registered models. DATA_SCIENTIST and SUPER_ADMIN.",
        tags=["ML Models"],
        responses={200: ModelRegistrySerializer},
    ),
    retrieve=extend_schema(
        summary="Retrieve model",
        description="Retrieve model metadata by ID.",
        tags=["ML Models"],
        responses={200: ModelRegistrySerializer},
    ),
    create=extend_schema(
        summary="Register model",
        description="Register a new model in the registry. DATA_SCIENTIST.",
        tags=["ML Models"],
        responses={201: ModelRegistrySerializer},
    ),
    update=extend_schema(
        summary="Update model metadata",
        description="Update model metadata. DATA_SCIENTIST.",
        tags=["ML Models"],
        responses={200: ModelRegistrySerializer},
    ),
    destroy=extend_schema(
        summary="Delete model",
        description="Delete a model registry entry. SUPER_ADMIN only.",
        tags=["ML Models"],
        responses={204: OpenApiResponse(description="Model deleted")},
    ),
)
class ModelRegistryViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """
    Model Registry & Promotion API:

    - GET  /api/v1/ml/models/
    - GET  /api/v1/ml/models/{id}/
    - PUT  /api/v1/ml/models/{id}/
    - DELETE /api/v1/ml/models/{id}/
    - POST /api/v1/ml/models/{id}/request-promotion/   (Data Scientist)
    - POST /api/v1/admin/models/{id}/approve/          (SuperAdmin)
    - POST /api/v1/admin/models/{id}/reject/           (SuperAdmin)
    """

    queryset = ModelRegistry.objects.all()
    serializer_class = ModelRegistrySerializer
    permission_classes = [IsAuthenticated]

    @require_roles("DATA_SCIENTIST", "SUPER_ADMIN")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @require_roles("DATA_SCIENTIST", "SUPER_ADMIN")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @require_roles("DATA_SCIENTIST")
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        model = create_model_registry_entry(
            actor=request.user, data=serializer.validated_data, request=request
        )
        output = self.get_serializer(model)
        headers = self.get_success_headers(output.data)
        return Response(output.data, status=status.HTTP_201_CREATED, headers=headers)

    @require_roles("DATA_SCIENTIST")
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        for field in ["description", "train_config", "artifact_path", "code_version"]:
            if field in serializer.validated_data:
                setattr(instance, field, serializer.validated_data[field])
        instance.save()
        output = self.get_serializer(instance)
        return Response(output.data)

    @require_roles("SUPER_ADMIN")
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        summary="Request model promotion",
        description="Data Scientist requests promotion of a model to production.",
        tags=["ML Models"],
        responses={202: OpenApiResponse(description="Promotion request accepted")},
    )
    @action(detail=True, methods=["post"], url_path="request-promotion")
    @require_roles("DATA_SCIENTIST")
    def request_promotion(self, request, pk=None):
        model = self.get_object()
        # For now, this is a no-op that simply logs an audit event.
        from apps.audit.services import log_audit_event

        log_audit_event(
            actor=request.user,
            action="ml.model.promotion.requested",
            entity_type="ModelRegistry",
            entity_id=model.pk,
            request=request,
            metadata={},
        )
        return Response({"status": "promotion-requested"}, status=status.HTTP_202_ACCEPTED)


@method_decorator(admin_only, name="dispatch")
class ApproveModelPromotionView(GenericAPIView):
    serializer_class = ModelRegistrySerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Approve model promotion",
        description="SuperAdmin approves promotion of a model.",
        tags=["ML Models"],
        responses={200: ModelRegistrySerializer},
        operation_id="ml_approve_model_promotion",
    )
    def post(self, request, id: str):
        model = get_object_or_404(ModelRegistry, pk=id)
        model = promote_model(actor=request.user, model=model, request=request)
        serializer = ModelRegistrySerializer(model)
        return Response(serializer.data, status=status.HTTP_200_OK)


@method_decorator(admin_only, name="dispatch")
class RejectModelPromotionView(GenericAPIView):
    serializer_class = ModelRegistrySerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Reject model promotion",
        description="SuperAdmin rejects promotion of a model.",
        tags=["ML Models"],
        responses={200: ModelRegistrySerializer},
        operation_id="ml_reject_model_promotion",
    )
    def post(self, request, id: str):
        model = get_object_or_404(ModelRegistry, pk=id)
        from apps.audit.services import log_audit_event

        log_audit_event(
            actor=request.user,
            action="ml.model.promote.reject",
            entity_type="ModelRegistry",
            entity_id=model.pk,
            request=request,
            metadata={},
        )
        serializer = ModelRegistrySerializer(model)
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema_view(
    list=extend_schema(
        summary="List training jobs",
        description="List training jobs for monitoring. DATA_SCIENTIST only.",
        tags=["ML Training"],
        responses={200: TrainingJobSerializer},
    ),
    retrieve=extend_schema(
        summary="Retrieve training job",
        description="Retrieve training job by ID.",
        tags=["ML Training"],
        responses={200: TrainingJobSerializer},
    ),
)
class TrainingJobViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """
    Training Job API:

    - POST /api/v1/ml/train/
    - GET  /api/v1/ml/train/jobs/
    - GET  /api/v1/ml/train/jobs/{id}/
    - POST /api/v1/ml/train/jobs/{id}/cancel/
    """

    queryset = TrainingJob.objects.select_related("model", "dataset", "feature_set")
    serializer_class = TrainingJobSerializer
    permission_classes = [IsAuthenticated]

    @require_roles("DATA_SCIENTIST")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @require_roles("DATA_SCIENTIST")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary="Request training job",
        description="Create a training job and trigger async training. DATA_SCIENTIST only.",
        tags=["ML Training"],
        request=TrainingJobCreateSerializer,
        responses={201: TrainingJobSerializer},
    )
    @api_view(["POST"])
    def create_training_job(request):
        role_code = _get_user_role_code(request.user)
        if role_code != "DATA_SCIENTIST" and not request.user.is_superuser:
            return Response({"detail": "Insufficient role."}, status=status.HTTP_403_FORBIDDEN)

        serializer = TrainingJobCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        job = request_training_job(
            actor=request.user,
            data=serializer.validated_data,
            request=request,
        )
        output = TrainingJobSerializer(job)
        return Response(output.data, status=status.HTTP_201_CREATED)

    @extend_schema(
        summary="Cancel training job",
        description="Cancel a pending or running training job. DATA_SCIENTIST only.",
        tags=["ML Training"],
        responses={200: TrainingJobSerializer},
    )
    @action(detail=True, methods=["post"], url_path="cancel")
    @require_roles("DATA_SCIENTIST")
    def cancel(self, request, pk=None):
        job = self.get_object()
        job = cancel_training_job(actor=request.user, job=job, request=request)
        serializer = TrainingJobSerializer(job)
        return Response(serializer.data, status=status.HTTP_200_OK)


class HpoRunView(GenericAPIView):
    serializer_class = HpoRunSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Run HPO",
        description="Placeholder endpoint for hyperparameter optimization runs. DATA_SCIENTIST only.",
        tags=["ML HPO"],
        responses={202: OpenApiResponse(description="HPO run accepted")},
        operation_id="ml_hpo_run",
    )
    def post(self, request):
        role_code = _get_user_role_code(request.user)
        if role_code != "DATA_SCIENTIST" and not request.user.is_superuser:
            return Response({"detail": "Insufficient role."}, status=status.HTTP_403_FORBIDDEN)

        # For now, just acknowledge.
        return Response({"status": "hpo-stub-accepted"}, status=status.HTTP_202_ACCEPTED)


class HpoRunsListView(GenericAPIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="List HPO runs",
        description="Placeholder list endpoint for HPO runs.",
        tags=["ML HPO"],
        responses={200: OpenApiResponse(description="List of HPO runs (stub)")},
        operation_id="ml_hpo_runs_list",
    )
    def get(self, request):
        role_code = _get_user_role_code(request.user)
        if role_code != "DATA_SCIENTIST" and not request.user.is_superuser:
            return Response({"detail": "Insufficient role."}, status=status.HTTP_403_FORBIDDEN)

        return Response([], status=status.HTTP_200_OK)


class HpoRunDetailView(GenericAPIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Retrieve HPO run",
        description="Placeholder retrieve endpoint for a single HPO run.",
        tags=["ML HPO"],
        responses={200: OpenApiResponse(description="HPO run details (stub)")},
        operation_id="ml_hpo_run_detail",
    )
    def get(self, request, id: str):
        role_code = _get_user_role_code(request.user)
        if role_code != "DATA_SCIENTIST" and not request.user.is_superuser:
            return Response({"detail": "Insufficient role."}, status=status.HTTP_403_FORBIDDEN)

        return Response({"id": id, "status": "stub"}, status=status.HTTP_200_OK)


@extend_schema(
    summary="Data drift status",
    description="Placeholder endpoint for data drift detection.",
    tags=["ML Drift"],
    responses={200: OpenApiResponse(description="Data drift summary (stub)")},
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def data_drift(request):
    role_code = _get_user_role_code(request.user)
    if role_code not in ("DATA_SCIENTIST", "SUPER_ADMIN") and not request.user.is_superuser:
        return Response({"detail": "Insufficient role."}, status=status.HTTP_403_FORBIDDEN)
    return Response({"status": "no-drift-stub"}, status=status.HTTP_200_OK)


@extend_schema(
    summary="Model drift status",
    description="Placeholder endpoint for model drift detection.",
    tags=["ML Drift"],
    responses={200: OpenApiResponse(description="Model drift summary (stub)")},
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def model_drift(request):
    role_code = _get_user_role_code(request.user)
    if role_code not in ("DATA_SCIENTIST", "SUPER_ADMIN") and not request.user.is_superuser:
        return Response({"detail": "Insufficient role."}, status=status.HTTP_403_FORBIDDEN)
    return Response({"status": "no-drift-stub"}, status=status.HTTP_200_OK)


@extend_schema(
    summary="Training dataset lineage for model",
    description="Audit endpoint: dataset used to train a model.",
    tags=["ML Audit"],
    responses={200: OpenApiResponse(description="Dataset lineage JSON")},
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def audit_ml_dataset(request, model_id: str):
    model = get_object_or_404(ModelRegistry, pk=model_id)
    payload = {
        "model_id": str(model.pk),
        "dataset_id": str(model.dataset_id),
        "dataset_definition": model.dataset.definition,
    }
    return Response(payload, status=status.HTTP_200_OK)


@extend_schema(
    summary="Feature set lineage for model",
    description="Audit endpoint: feature set used to train a model.",
    tags=["ML Audit"],
    responses={200: OpenApiResponse(description="Feature set lineage JSON")},
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def audit_ml_features(request, model_id: str):
    model = get_object_or_404(ModelRegistry, pk=model_id)
    payload = {
        "model_id": str(model.pk),
        "feature_set_id": str(model.feature_set_id),
        "feature_spec": model.feature_set.spec,
    }
    return Response(payload, status=status.HTTP_200_OK)


@extend_schema(
    summary="Training config lineage for model",
    description="Audit endpoint: training configuration for a model.",
    tags=["ML Audit"],
    responses={200: OpenApiResponse(description="Training config JSON")},
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def audit_ml_config(request, model_id: str):
    model = get_object_or_404(ModelRegistry, pk=model_id)
    payload = {
        "model_id": str(model.pk),
        "train_config": model.train_config,
    }
    return Response(payload, status=status.HTTP_200_OK)


@extend_schema(
    summary="Training code version for model",
    description="Audit endpoint: code version used for training the model.",
    tags=["ML Audit"],
    responses={200: OpenApiResponse(description="Code version info")},
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def audit_ml_code(request, model_id: str):
    model = get_object_or_404(ModelRegistry, pk=model_id)
    payload = {
        "model_id": str(model.pk),
        "code_version": model.code_version,
    }
    return Response(payload, status=status.HTTP_200_OK)

