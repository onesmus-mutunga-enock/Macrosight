from typing import Any, Dict, Optional

from django.db import transaction
from django.http import HttpRequest

from apps.audit.services import log_audit_event

from ..models import Dataset, FeatureSet, ModelRegistry, TrainingJob
from ..tasks import run_training_job


@transaction.atomic
def create_dataset(*, actor, data: Dict[str, Any], request: Optional[HttpRequest] = None) -> Dataset:
    dataset = Dataset.objects.create(
        name=data["name"],
        description=data.get("description", ""),
        definition=data.get("definition", {}) or {},
        created_by=actor,
    )
    log_audit_event(
        actor=actor,
        action="ml.dataset.create",
        entity_type="Dataset",
        entity_id=dataset.pk,
        request=request,
        metadata={"definition": dataset.definition},
    )
    return dataset


@transaction.atomic
def create_feature_set(
    *, actor, data: Dict[str, Any], request: Optional[HttpRequest] = None
) -> FeatureSet:
    feature_set = FeatureSet.objects.create(
        dataset=data["dataset"],
        name=data["name"],
        description=data.get("description", ""),
        spec=data.get("spec", {}) or {},
        created_by=actor,
    )
    log_audit_event(
        actor=actor,
        action="ml.features.create",
        entity_type="FeatureSet",
        entity_id=feature_set.pk,
        request=request,
        metadata={"spec": feature_set.spec},
    )
    return feature_set


@transaction.atomic
def create_model_registry_entry(
    *, actor, data: Dict[str, Any], request: Optional[HttpRequest] = None
) -> ModelRegistry:
    model = ModelRegistry.objects.create(
        name=data["name"],
        description=data.get("description", ""),
        algorithm=data["algorithm"],
        dataset=data["dataset"],
        feature_set=data["feature_set"],
        train_config=data.get("train_config", {}) or {},
        artifact_path=data.get("artifact_path", ""),
        code_version=data.get("code_version", ""),
        created_by=actor,
    )
    log_audit_event(
        actor=actor,
        action="ml.model.register",
        entity_type="ModelRegistry",
        entity_id=model.pk,
        request=request,
        metadata={
            "algorithm": model.algorithm,
            "dataset_id": str(model.dataset_id),
            "feature_set_id": str(model.feature_set_id),
        },
    )
    return model


@transaction.atomic
def promote_model(
    *, actor, model: ModelRegistry, request: Optional[HttpRequest] = None
) -> ModelRegistry:
    from django.utils import timezone

    before_status = model.status
    model.status = ModelRegistry.Status.ACTIVE
    model.promoted_by = actor
    model.promoted_at = timezone.now()
    model.save(update_fields=["status", "promoted_by", "promoted_at"])

    log_audit_event(
        actor=actor,
        action="ml.model.promote",
        entity_type="ModelRegistry",
        entity_id=model.pk,
        request=request,
        metadata={"before_status": before_status, "after_status": model.status},
    )
    return model


@transaction.atomic
def request_training_job(
    *,
    actor,
    data: Dict[str, Any],
    request: Optional[HttpRequest] = None,
) -> TrainingJob:
    """
    Creates a TrainingJob and triggers Celery for asynchronous execution.
    """
    model = data["model"]
    dataset = data["dataset"]
    feature_set = data["feature_set"]
    hyperparameters = data.get("hyperparameters", {}) or {}
    is_hpo = data.get("is_hpo", False)

    job = TrainingJob.objects.create(
        model=model,
        dataset=dataset,
        feature_set=feature_set,
        status=TrainingJob.Status.PENDING,
        is_hpo=is_hpo,
        hyperparameters=hyperparameters,
        created_by=actor,
    )

    # Trigger Celery task
    async_result = run_training_job.delay(str(job.pk))
    job.celery_task_id = async_result.id
    job.save(update_fields=["celery_task_id"])

    log_audit_event(
        actor=actor,
        action="ml.training.requested",
        entity_type="TrainingJob",
        entity_id=job.pk,
        request=request,
        metadata={
            "model_id": str(model.pk),
            "dataset_id": str(dataset.pk),
            "feature_set_id": str(feature_set.pk),
            "is_hpo": is_hpo,
        },
    )
    return job


@transaction.atomic
def cancel_training_job(
    *, actor, job: TrainingJob, request: Optional[HttpRequest] = None
) -> TrainingJob:
    before_status = job.status
    job.status = TrainingJob.Status.CANCELLED
    job.save(update_fields=["status"])

    log_audit_event(
        actor=actor,
        action="ml.training.cancelled",
        entity_type="TrainingJob",
        entity_id=job.pk,
        request=request,
        metadata={"before_status": before_status, "after_status": job.status},
    )
    return job

