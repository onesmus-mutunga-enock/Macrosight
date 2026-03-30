import uuid

from django.db import models

from apps.products.models import Product
from apps.sectors.models import Sector


class Sale(models.Model):
    """
    Normalized sales data model used for ML feature generation and reporting.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="sales",
    )
    sector = models.ForeignKey(
        Sector,
        on_delete=models.PROTECT,
        related_name="sales",
    )

    date = models.DateField()
    units_sold = models.DecimalField(max_digits=18, decimal_places=2)
    revenue = models.DecimalField(max_digits=18, decimal_places=2)
    price = models.DecimalField(
        max_digits=18,
        decimal_places=4,
        help_text="Unit price for the product on this date.",
    )
    region = models.CharField(max_length=128, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "sales_sale"
        ordering = ("-date",)
        indexes = [
            models.Index(fields=["product", "date"], name="sal_sale_prod_date_idx"),
            models.Index(fields=["sector", "date"], name="sal_sale_sect_date_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.product_id} @ {self.date}"


class SaleSummary(models.Model):
    """
    Aggregated sales summary for a given period (daily, weekly, monthly).
    Used for reporting and quick lookups instead of computing aggregates on the fly.
    """

    PERIOD_DAILY = "daily"
    PERIOD_WEEKLY = "weekly"
    PERIOD_MONTHLY = "monthly"

    PERIOD_CHOICES = [
        (PERIOD_DAILY, "Daily"),
        (PERIOD_WEEKLY, "Weekly"),
        (PERIOD_MONTHLY, "Monthly"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="summaries",
    )
    sector = models.ForeignKey(
        Sector,
        on_delete=models.PROTECT,
        related_name="summaries",
    )

    # The date representing the start of the period (e.g. day, week start, month start)
    period_start = models.DateField()
    period = models.CharField(max_length=16, choices=PERIOD_CHOICES, default=PERIOD_DAILY)

    total_units = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    total_revenue = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    average_price = models.DecimalField(max_digits=18, decimal_places=4, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "sales_salesummary"
        ordering = ("-period_start",)
        constraints = [
            models.UniqueConstraint(
                fields=["product", "sector", "period", "period_start"],
                name="uniq_sale_summary_prod_sect_period_start",
            )
        ]
        indexes = [
            models.Index(fields=["product", "period_start"], name="sal_sum_prod_date_idx"),
            models.Index(fields=["sector", "period_start"], name="sal_sum_sect_date_idx"),
        ]

    def __str__(self) -> str:
        return f"Summary {self.product_id} {self.period} @ {self.period_start}"

