"""Optional signal receivers to trigger online updates when new data arrives.

These receivers are intentionally non-invasive: they attempt to call
`apps.ml.tasks.enqueue_online_update` if present. They will not raise
errors if the tasks module or function does not exist.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save)
def ml_post_save_receiver(sender, instance, created, **kwargs):
    """Generic hook: if the project defines `apps.ml.tasks.enqueue_online_update`, call it."""
    try:
        from apps.ml import tasks as _tasks
        if hasattr(_tasks, 'enqueue_online_update'):
            try:
                _tasks.enqueue_online_update(instance)
            except Exception:
                # swallow errors to avoid breaking domain saves
                pass
    except Exception:
        pass
