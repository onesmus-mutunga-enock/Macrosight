import uuid
from django.db import models
from apps.sectors.models import Sector
from apps.users.models import User


class Fertilizer(models.Model):
    """
    Agricultural fertilizer input data.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    sector = models.ForeignKey(Sector, on_delete=models.PROTECT, related_name='fertilizers')
    type = models.CharField(max_length=100, help_text="Type of fertilizer (e.g., NPK, Urea, etc.)")
    unit = models.CharField(max_length=50, default='kg')
    price_per_unit = models.DecimalField(max_digits=12, decimal_places=4)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_fertilizers')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "inputs_fertilizer"
        ordering = ('name',)
        unique_together = ('name', 'sector')

    def __str__(self):
        return f"{self.name} ({self.sector.code})"


class Seed(models.Model):
    """
    Agricultural seed input data.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    sector = models.ForeignKey(Sector, on_delete=models.PROTECT, related_name='seeds')
    crop_type = models.CharField(max_length=100, help_text="Type of crop (e.g., maize, wheat, etc.)")
    variety = models.CharField(max_length=100, blank=True)
    unit = models.CharField(max_length=50, default='kg')
    price_per_unit = models.DecimalField(max_digits=12, decimal_places=4)
    yield_per_unit = models.DecimalField(max_digits=8, decimal_places=2, help_text="Expected yield per unit")
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_seeds')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "inputs_seed"
        ordering = ('name',)
        unique_together = ('name', 'sector')

    def __str__(self):
        return f"{self.name} ({self.sector.code})"


class Pesticide(models.Model):
    """
    Agricultural pesticide input data.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    sector = models.ForeignKey(Sector, on_delete=models.PROTECT, related_name='pesticides')
    type = models.CharField(max_length=100, help_text="Type of pesticide (e.g., herbicide, insecticide, etc.)")
    unit = models.CharField(max_length=50, default='liter')
    price_per_unit = models.DecimalField(max_digits=12, decimal_places=4)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_pesticides')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "inputs_pesticide"
        ordering = ('name',)
        unique_together = ('name', 'sector')

    def __str__(self):
        return f"{self.name} ({self.sector.code})"


class Fuel(models.Model):
    """
    Agricultural fuel input data.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    sector = models.ForeignKey(Sector, on_delete=models.PROTECT, related_name='fuels')
    type = models.CharField(max_length=100, help_text="Type of fuel (e.g., diesel, petrol, etc.)")
    unit = models.CharField(max_length=50, default='liter')
    price_per_unit = models.DecimalField(max_digits=12, decimal_places=4)
    energy_content = models.DecimalField(max_digits=8, decimal_places=2, help_text="Energy content per unit (MJ)")
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_fuels')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "inputs_fuel"
        ordering = ('name',)
        unique_together = ('name', 'sector')

    def __str__(self):
        return f"{self.name} ({self.sector.code})"


class InputSummary(models.Model):
    """
    Summary of agricultural inputs by sector.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sector = models.ForeignKey(Sector, on_delete=models.CASCADE, related_name='input_summaries')
    date = models.DateField()
    total_fertilizer_cost = models.DecimalField(max_digits=12, decimal_places=4, default=0)
    total_seed_cost = models.DecimalField(max_digits=12, decimal_places=4, default=0)
    total_pesticide_cost = models.DecimalField(max_digits=12, decimal_places=4, default=0)
    total_fuel_cost = models.DecimalField(max_digits=12, decimal_places=4, default=0)
    total_cost = models.DecimalField(max_digits=12, decimal_places=4, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "inputs_summary"
        ordering = ('-date', 'sector')
        unique_together = ('sector', 'date')

    def __str__(self):
        return f"{self.sector.code} - {self.date} - Total: {self.total_cost}"