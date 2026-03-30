"""
Cost feature extraction service.
Extracts time-series cost features for ML compatibility.
"""
from typing import Dict, Any, Union, Optional
from datetime import timedelta, date
import numpy as np
from django.db.models import Avg
from apps.costs.models import InputCostValue


def get_cost_features(
    sector_id: int,
    date: date,
    days_back: int = 30
) -> Dict[str, float]:
    """Extract cost time-series features for a sector around a date.

    Returns:
        avg_cost_30d, cost_trend_30d, total_cost_volume, cost_volatility_30d,
        current_cost, lagged_cost_7d
    """
    end_date = date
    start_date = date - timedelta(days=days_back)

    costs_qs = InputCostValue.objects.filter(
        cost__sector_id=sector_id,
        date__range=[start_date, end_date]
    ).order_by('date')

    features = {
        'avg_cost_30d': 0.0,
        'cost_trend_30d': 0.0,
        'total_cost_volume': 0.0,
        'cost_volatility_30d': 0.0,
        'current_cost': 0.0,
        'lagged_cost_7d': 0.0,
    }

    values = list(costs_qs.values_list('value', flat=True))
    if not values:
        return features

    arr = np.array(values, dtype=float)
    features['avg_cost_30d'] = float(np.mean(arr))
    features['total_cost_volume'] = float(np.sum(arr))
    features['cost_volatility_30d'] = float(np.std(arr, ddof=1)) if arr.size > 1 else 0.0

    # trend (slope)
    x = np.arange(len(arr))
    if len(arr) > 1:
        A = np.vstack([x, np.ones(len(x))]).T
        slope, _ = np.linalg.lstsq(A, arr, rcond=None)[0]
        features['cost_trend_30d'] = float(slope)
    else:
        features['cost_trend_30d'] = 0.0

    # current and lagged
    features['current_cost'] = float(arr[-1])
    features['lagged_cost_7d'] = float(arr[-8]) if arr.size > 7 else float(arr[0])

    return features
