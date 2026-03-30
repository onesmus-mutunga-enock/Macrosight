"""Helpers to compute product-level marginal cost proxies.

Provide conservative proxies for marginal cost when direct product-input
cost mappings are not available.
"""
from typing import Optional
from datetime import date
from apps.products.models import Product
from apps.costs.models import InputCostValue


def get_product_marginal_cost(product_id: int, as_of: Optional[date] = None) -> float:
    """Estimate product marginal cost using sector-level input costs.

    Heuristic used:
      - avg sector input cost over recent window
      - divide by number of active products in sector as a simple allocation
    Returns 0.0 if no cost data available.
    """
    try:
        prod = Product.objects.get(pk=product_id)
    except Exception:
        return 0.0

    sector = prod.sector
    if as_of is None:
        from datetime import date as _d
        as_of = _d.today()

    # recent window 30 days
    from datetime import timedelta
    start = as_of - timedelta(days=30)

    qs = InputCostValue.objects.filter(cost__sector_id=sector.id, date__range=[start, as_of])
    values = [v.value for v in qs if v.value is not None]
    if not values:
        return 0.0

    avg_sector_cost = sum(values) / len(values)

    # number of active products in sector
    prod_count = sector.products.filter(is_active=True).count() or 1

    # allocate equally as a conservative marginal cost proxy
    return float(avg_sector_cost / prod_count)
