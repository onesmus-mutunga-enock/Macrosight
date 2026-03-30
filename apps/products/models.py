from django.db import models
from apps.sectors.models import Sector
from apps.users.models import User


class Product(models.Model):
    """
    Product model for MacroSight platform.
    Represents products that can be sold and forecasted.
    """

    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    sku = models.CharField(max_length=100, unique=True, help_text="Stock Keeping Unit")
    category = models.CharField(max_length=100, blank=True)
    unit_of_measure = models.CharField(max_length=50)
    sector = models.ForeignKey(Sector, on_delete=models.CASCADE, related_name='products')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products_updated'
    )

    class Meta:
        db_table = "products"
        ordering = ['name']
        verbose_name = "Product"
        verbose_name_plural = "Products"

    def __str__(self):
        return f"{self.sku} - {self.name}"

    def get_full_hierarchy(self):
        """Get the full product hierarchy path."""
        path = [self.name]
        parent = self.parent
        while parent:
            path.insert(0, parent.name)
            parent = parent.parent
        return " -> ".join(path)


class ProductPlaceholder(models.Model):
    """
    Placeholder model for products app; full domain models
    will be added in business phases.
    """

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "products_placeholder"




