"""
Sales feature extraction service.
Returns ML-ready numeric features for given product/sector/date.
"""
from typing import Dict, Any, Union, Optional
from datetime import timedelta, date
import numpy as np
from django.db.models import Avg
from django.utils import timezone
from apps.sales.models import Sale
from apps.products.models import Product


def get_sales_features(
    product_id: Optional[Union[int, str, Product]] = None,
    sector_id: Optional[int] = None,
    as_of: Optional[date] = None,
    window_days: int = 30
) -> Dict[str, float]:
    """Return sales-oriented features for a product/sector as of a date.

    - rolling average over window_days
    - rolling std (volatility)
    - recent_sales_7d
    - recent_sales_30d
    - demand_trend: simple linear trend estimate (slope)
    """
    if as_of is None:
        as_of = timezone.now().date()

    start_date = as_of - timedelta(days=window_days)

    qs = Sale.objects.all()
    if product_id is not None:
        if isinstance(product_id, Product):
            qs = qs.filter(product_id=product_id.id)
        else:
            qs = qs.filter(product_id=product_id)
    elif sector_id is not None:
        qs = qs.filter(product__sector_id=sector_id)

    qs = qs.filter(date__range=[start_date, as_of]).order_by('date')

    values = list(qs.values_list('quantity', flat=True))

    if not values:
        return {
            'avg_sales_30d': 0.0,
            'sales_std_30d': 0.0,
            'recent_sales_7d': 0.0,
            'recent_sales_30d': 0.0,
            'demand_trend': 0.0,
            'sales_volatility': 0.0,
        }

    arr = np.array(values, dtype=float)
    avg_30 = float(np.mean(arr))
    std_30 = float(np.std(arr, ddof=1)) if arr.size > 1 else 0.0
    recent_7 = float(np.sum(arr[-7:])) if arr.size >= 1 else 0.0
    recent_30 = float(np.sum(arr))

    # Simple trend: slope from linear regression over time indices
    x = np.arange(len(arr))
    if len(arr) > 1:
        A = np.vstack([x, np.ones(len(x))]).T
        slope, _ = np.linalg.lstsq(A, arr, rcond=None)[0]
        demand_trend = float(slope)
    else:
        demand_trend = 0.0

    return {
        'avg_sales_30d': avg_30,
        'sales_std_30d': std_30,
        'recent_sales_7d': recent_7,
        'recent_sales_30d': recent_30,
        'demand_trend': demand_trend,
        'sales_volatility': std_30,
    }
