"""apps.economic_models.services.elasticity
Utilities to interpret linear regression coefficients as elasticities.

The functions here intentionally keep a light dependency on the
project's linear regression service. They attempt to infer feature
means from the model's scaler when available and fall back to
feature-set data if provided.
"""
from typing import Dict, Optional
import numpy as np

try:
    # Import the LR service class to satisfy typing in the environment
    from apps.ml.services.linear_regression_model import LinearRegressionModelService
except Exception:
    LinearRegressionModelService = object


def compute_price_elasticity(model, feature_index_map: Dict[str, int], *, target_name: str = 'sales_target') -> Dict[str, float]:
    """Compute price elasticity from a trained linear regression service.

    Elasticity formula (approx):
        E_p = beta_price * (mean_price / mean_quantity)

    Args:
        model: instance of LinearRegressionModelService (or compatible)
        feature_index_map: mapping from feature name to column index
        target_name: name of the target column in training dataset (optional)

    Returns:
        dict with keys: ``price_elasticity``, ``price_coef``, ``mean_price``, ``mean_quantity``
    """
    if getattr(model, 'model', None) is None:
        raise ValueError('Provided model is not loaded or trained')

    # Identify price coefficient index (common feature names)
    possible_price_keys = ['avg_price_30d', 'avg_price', 'price']
    price_index = None
    for k in possible_price_keys:
        if k in feature_index_map:
            price_index = feature_index_map[k]
            price_key = k
            break
    if price_index is None:
        raise ValueError('No price feature found in feature_index_map')

    # Extract coefficient
    coef_array = getattr(model.model, 'coef_', None)
    if coef_array is None:
        raise ValueError('Underlying sklearn model has no coefficients')

    price_coef = float(coef_array[price_index])

    # Try to infer mean price from StandardScaler if available
    mean_price: Optional[float] = None
    scaler = getattr(model, 'scaler', None)
    if scaler is not None and hasattr(scaler, 'mean_'):
        try:
            mean_price = float(scaler.mean_[price_index])
        except Exception:
            mean_price = None

    # Infer mean quantity (target) from feature_set dataset rows if available
    mean_quantity: Optional[float] = None
    feature_set = getattr(model, 'feature_set', None)
    try:
        if feature_set is not None and hasattr(feature_set, 'dataset'):
            rows = feature_set.dataset.rows.all()
            if rows.exists():
                vals = [r.data.get(target_name, None) for r in rows if r.data.get(target_name) is not None]
                if vals:
                    mean_quantity = float(np.mean(vals))
    except Exception:
        mean_quantity = None

    # Fallbacks
    if mean_price is None:
        mean_price = 1.0
    if mean_quantity is None or mean_quantity == 0:
        mean_quantity = 1.0

    elasticity = price_coef * (mean_price / mean_quantity)

    return {
        'price_elasticity': float(elasticity),
        'price_coef': float(price_coef),
        'mean_price': float(mean_price),
        'mean_quantity': float(mean_quantity),
        'price_feature_key': price_key
    }
