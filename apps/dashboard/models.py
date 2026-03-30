import uuid
from django.db import models
from apps.users.models import User


class Dashboard(models.Model):
    """
    Dashboard configuration and layout.
    """

    class Type(models.TextChoices):
        EXECUTIVE = "EXECUTIVE", "Executive"
        ANALYST = "ANALYST", "Analyst"
        AUDITOR = "AUDITOR", "Auditor"
        DATA_FEEDER = "DATA_FEEDER", "Data Feeder"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    dashboard_type = models.CharField(max_length=32, choices=Type.choices)
    layout = models.JSONField(default=dict, blank=True, help_text="Dashboard layout configuration")
    widgets = models.JSONField(default=list, blank=True, help_text="List of widgets and their configurations")

    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_dashboards')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "dashboard_dashboard"
        ordering = ('-created_at',)

    def __str__(self):
        return f"{self.name} ({self.dashboard_type})"


class DashboardWidget(models.Model):
    """
    Individual widget configuration for dashboards.
    """

    class Type(models.TextChoices):
        CHART = "CHART", "Chart"
        TABLE = "TABLE", "Table"
        KPI = "KPI", "KPI"
        MAP = "MAP", "Map"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    dashboard = models.ForeignKey(Dashboard, on_delete=models.CASCADE, related_name='dashboard_widgets')
    widget_type = models.CharField(max_length=32, choices=Type.choices)
    title = models.CharField(max_length=255)
    configuration = models.JSONField(default=dict, blank=True, help_text="Widget-specific configuration")
    position = models.JSONField(default=dict, blank=True, help_text="Widget position in the layout")
    size = models.JSONField(default=dict, blank=True, help_text="Widget size configuration")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "dashboard_widget"
        ordering = ('dashboard', 'id')

    def __str__(self):
        return f"{self.title} ({self.widget_type})"


class DashboardData(models.Model):
    """
    Aggregated data for dashboard widgets.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    widget = models.ForeignKey(DashboardWidget, on_delete=models.CASCADE, related_name='data')
    data = models.JSONField(default=dict, blank=True, help_text="Aggregated data for the widget")
    refresh_time = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "dashboard_data"
        ordering = ('-refresh_time',)

    def __str__(self):
        return f"Data for {self.widget.title}"