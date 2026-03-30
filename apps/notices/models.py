import uuid
from django.db import models
from apps.users.models import User


class GovernmentNotice(models.Model):
    """
    Government notices and official communications.
    """

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        PUBLISHED = "PUBLISHED", "Published"
        ARCHIVED = "ARCHIVED", "Archived"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    content = models.TextField()
    notice_type = models.CharField(max_length=100, help_text="Type of notice (e.g., policy, regulation, announcement)")
    reference_number = models.CharField(max_length=100, blank=True, help_text="Official reference number")
    publication_date = models.DateField()
    effective_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.DRAFT)
    tags = models.JSONField(default=list, blank=True, help_text="Tags for categorization")

    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_government_notices')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "notices_government_notice"
        ordering = ('-publication_date',)

    def __str__(self):
        return f"{self.title} ({self.publication_date})"


class NoticeImpact(models.Model):
    """
    Impact analysis of government notices on economic indicators.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    notice = models.ForeignKey(GovernmentNotice, on_delete=models.CASCADE, related_name='impacts')
    indicator = models.CharField(max_length=255, help_text="Economic indicator affected")
    baseline_value = models.DecimalField(max_digits=12, decimal_places=4)
    projected_impact = models.DecimalField(max_digits=12, decimal_places=4)
    impact_percentage = models.DecimalField(max_digits=8, decimal_places=2)
    confidence_interval = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "notices_notice_impact"
        ordering = ('notice', 'indicator')

    def __str__(self):
        return f"{self.indicator} - {self.impact_percentage}%"


class NoticeSectorImpact(models.Model):
    """
    Sector-specific impact of government notices.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    notice = models.ForeignKey(GovernmentNotice, on_delete=models.CASCADE, related_name='sector_impacts')
    sector = models.ForeignKey('sectors.Sector', on_delete=models.PROTECT, related_name='notice_impacts')
    impact_type = models.CharField(max_length=100, help_text="Type of impact (e.g., positive, negative, neutral)")
    impact_score = models.DecimalField(max_digits=5, decimal_places=2, help_text="Impact score (0-10)")
    description = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "notices_notice_sector_impact"
        ordering = ('notice', 'sector')

    def __str__(self):
        return f"{self.sector.code} - {self.impact_type}"