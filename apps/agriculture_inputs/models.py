import uuid
from django.db import models
from apps.sectors.models import Sector
from apps.users.models import User


class AgriculturalInput(models.Model):
    """
    Agricultural input definition (e.g. seeds, pesticides, fertilizers).
    """

    class InputType(models.TextChoices):
        SEED = "SEED", "Seed"
        FERTILIZER = "FERTILIZER", "Fertilizer"
        PESTICIDE = "PESTICIDE", "Pesticide"
        HERBICIDE = "HERBICIDE", "Herbicide"
        OTHER = "OTHER", "Other"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    name = models.CharField(max_length=255)
    type = models.CharField(max_length=32, choices=InputType.choices)
    sector = models.ForeignKey(
        Sector,
        on_delete=models.PROTECT,
        related_name="agricultural_inputs",
    )
    unit = models.CharField(max_length=64, blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="created_agricultural_inputs",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "agriculture_inputs_agricultural_input"
        unique_together = ("name", "sector", "type")
        ordering = ("name",)

    def __str__(self) -> str:
        return f"{self.name} ({self.type})"


class AgriculturalInputValue(models.Model):
    """
    Time series values for agricultural inputs.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    input = models.ForeignKey(
        AgriculturalInput,
        on_delete=models.CASCADE,
        related_name="values",
    )
    date = models.DateField()
    value = models.FloatField()
    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="Unit price for the input on this date.",
    )
    total_cost = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Total cost (value * unit_price).",
    )

    class Meta:
        db_table = "agriculture_inputs_agricultural_input_value"
        ordering = ("input", "date")
        indexes = [
            models.Index(fields=["input", "date"], name="agr_aiv_inp_date_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.input.name} {self.date} = {self.value}"