import uuid

from django.db import models

from apps.sectors.models import Sector


class InputCost(models.Model):
    """
    Input cost driver definition (e.g. fuel, fertilizer) for a sector.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    name = models.CharField(max_length=255)
    sector = models.ForeignKey(
        Sector,
        on_delete=models.PROTECT,
        related_name="input_costs",
    )
    unit = models.CharField(max_length=64, blank=True)

    class Meta:
        db_table = "costs_input_cost"
        unique_together = ("name", "sector")
        ordering = ("name",)

    def __str__(self) -> str:
        return f"{self.name} ({self.sector.code})"


class InputCostValue(models.Model):
    """
    Time series values for input costs.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    cost = models.ForeignKey(
        InputCost,
        on_delete=models.CASCADE,
        related_name="values",
    )
    date = models.DateField()
    value = models.FloatField()

    class Meta:
        db_table = "costs_input_cost_value"
        ordering = ("cost", "date")
        indexes = [
            models.Index(fields=["cost", "date"], name="cst_icv_cost_date_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.cost.name} {self.date} = {self.value}"

