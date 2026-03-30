from django.apps import AppConfig

class IntelligenceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.intelligence'
    verbose_name = 'Intelligence'

    def ready(self):
        # Import signals module if present to register receivers without
        # forcing a hard dependency. This mirrors common Django app patterns.
        try:
            import apps.intelligence.signals  # noqa: F401
        except Exception:
            # Signals are optional for this app; ignore import errors
            pass
