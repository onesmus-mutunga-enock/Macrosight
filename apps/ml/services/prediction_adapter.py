"""Adapter to run predictions using feature dicts and apply economic checks.

Provides `predict_with_economic_checks` which converts a feature dict
into the model's expected numpy array, runs prediction, applies
economic constraints and returns explainable results.
"""
from typing import Dict, Any
import numpy as np

from apps.economic_models.services.constraints import enforce_constraints
from apps.economic_models.services.elasticity import compute_price_elasticity


def predict_with_economic_checks(model_service, feature_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Predict using a LinearRegressionModelService-like object.

    Args:
        model_service: instance with attributes: model, scaler, feature_names, feature_set (optional)
        feature_dict: mapping of feature_name -> value

    Returns:
        dict containing 'raw_prediction', 'adjusted_prediction', and optional 'elasticity'
    """
    if getattr(model_service, 'model', None) is None:
        raise ValueError('Model not loaded in model_service')

    feature_names = getattr(model_service, 'feature_names', [])
    if not feature_names:
        # Try to read from feature_set sample row
        feature_names = getattr(model_service, 'feature_set', None) and getattr(model_service.feature_set, 'feature_names', []) or []

    # Build feature vector in same order
    X = np.array([[float(feature_dict.get(fn, 0.0)) for fn in feature_names]])

    scaler = getattr(model_service, 'scaler', None)
    if scaler is not None:
        X_scaled = scaler.transform(X)
    else:
        X_scaled = X

    raw_pred = float(model_service.model.predict(X_scaled).flatten()[0])

    # Try to apply constraints: if cost available in features use it
    cost = float(feature_dict.get('current_cost', feature_dict.get('avg_cost_30d', 0.0)))
    adjusted = enforce_constraints(raw_pred, cost)

    out = {
        'raw_prediction': raw_pred,
        'adjusted_prediction': adjusted,
    }

    # Compute elasticity if possible
    try:
        feature_index_map = {name: i for i, name in enumerate(feature_names)}
        elasticity = compute_price_elasticity(model_service, feature_index_map)
        out['elasticity'] = elasticity
    except Exception:
        out['elasticity'] = None

    # Attach coefficient explainability when available
    try:
        coefs = getattr(model_service.model, 'coef_', None)
        if coefs is not None and feature_names:
            feat_imp = {fn: float(coefs[i]) for i, fn in enumerate(feature_names) if i < len(coefs)}
            out['feature_coefficients'] = feat_imp
    except Exception:
        out['feature_coefficients'] = None

    return out
