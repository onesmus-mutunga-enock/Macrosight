"""Lightweight tasks module for online update orchestration.

This module is intentionally simple: it exposes `enqueue_online_update`
which will attempt to perform a best-effort incremental update using
`OnlineModelService`. In production this could be backed by Celery.
"""
import logging
from typing import Any

logger = logging.getLogger(__name__)


def enqueue_online_update(instance: Any) -> None:
    """Best-effort hook for incremental learning.

    Steps (best-effort, non-blocking):
      - Identify a suitable active ModelRegistry (sales model)
      - Build runtime features (if product/date available)
      - Map features to array and attempt to extract a numeric target from the instance
      - Call OnlineModelService.partial_fit(X, y) and persist

    This function is intentionally defensive: failures are logged but not raised.
    """
    try:
        # Defer imports to runtime to avoid circular imports at module load
        from apps.ml.models import ModelRegistry
        from apps.ml.services.online_model_service import OnlineModelService
        from apps.ml.services.feature_mapper import map_features_to_array
        from apps.intelligence.services import build_features

        # Pick the first ACTIVE LinearRegression model as candidate
        model_registry = ModelRegistry.objects.filter(status=ModelRegistry.Status.ACTIVE).order_by('-id').first()
        if not model_registry:
            logger.debug('No active model registry found for online update')
            return

        # Attempt to build features from instance
        product_id = getattr(instance, 'product_id', None) or getattr(instance, 'product', None)
        inst_date = getattr(instance, 'date', None)
        # normalize product object
        if hasattr(product_id, 'id'):
            product_id = product_id.id

        if product_id is None:
            logger.debug('Instance has no product; skipping online update')
            return

        # Build runtime features
        try:
            feature_dict = build_features(product_id=product_id, date=inst_date)
        except Exception as e:
            logger.exception('Failed to build features for online update: %s', e)
            return

        # Load or initialize online service
        try:
            online = OnlineModelService(model_registry.feature_set, model_registry)
            try:
                online.load(model_registry)
            except Exception:
                online.initialize_from_feature_set()
        except Exception as e:
            logger.exception('Failed to init OnlineModelService: %s', e)
            return

        # Map feature dict to array using model_registry.feature_set spec if available
        feature_names = None
        try:
            feature_names = model_registry.feature_set.spec.get('features', None)
        except Exception:
            feature_names = None

        try:
            if feature_names:
                X = map_features_to_array(feature_dict, feature_names)
            else:
                # fallback: use OnlineModelService.feature_names if present
                fn = getattr(online, 'feature_names', None) or []
                X = map_features_to_array(feature_dict, fn)
        except Exception as e:
            logger.exception('Failed to map features to array: %s', e)
            return

        # Extract a numeric target (best-effort). Look for common attributes
        y_val = None
        for attr in ('value', 'quantity', 'amount'):
            if hasattr(instance, attr):
                try:
                    y_val = float(getattr(instance, attr))
                    break
                except Exception:
                    y_val = None

        if y_val is None:
            logger.debug('No numeric target found on instance; skipping partial_fit')
            return

        # Perform partial fit
        try:
            import numpy as _np
            online.partial_fit(X, _np.array([y_val]))
            # Persist the updated online model
            if model_registry:
                online.save(model_registry)
        except Exception as e:
            logger.exception('Online partial_fit failed: %s', e)

    except Exception as e:
        try:
            logger.exception('enqueue_online_update unexpected error: %s', e)
        except Exception:
            pass
from celery import shared_task
from django.utils import timezone

from apps.audit.services import log_audit_event

from .models import TrainingJob, ModelRegistry


@shared_task
def run_training_job(job_id: str) -> None:
    """
    Stubbed asynchronous training job.

    This does NOT perform any heavy ML; it simply transitions status and
    records placeholder metrics for governance and integration testing.
    """
    try:
        job = TrainingJob.objects.select_related("model").get(pk=job_id)
    except TrainingJob.DoesNotExist:
        return

    job.status = TrainingJob.Status.RUNNING
    job.started_at = timezone.now()
    job.save(update_fields=["status", "started_at"])

    # Simulated training work...
    # In a real implementation this is where we would call out to an ML service.

    job.status = TrainingJob.Status.COMPLETED
    job.completed_at = timezone.now()
    job.metrics = {
        "rmse": 0.0,
        "mape": 0.0,
        "mae": 0.0,
        "notes": "Stub metrics; replace with real training output.",
    }
    job.save(update_fields=["status", "completed_at", "metrics"])

    log_audit_event(
        actor=job.created_by,
        action="ml.training.completed",
        entity_type="TrainingJob",
        entity_id=job.pk,
        request=None,
        metadata={
            "model_id": str(job.model_id),
            "metrics": job.metrics,
        },
    )

