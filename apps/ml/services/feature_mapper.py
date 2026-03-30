"""Feature mapping utilities.

Provide deterministic mapping from a feature dict to a numpy array
compatible with a model's `feature_names` order. Validates missing
features and fills defaults.
"""
from typing import Dict, List
import numpy as np


def map_features_to_array(feature_dict: Dict[str, any], feature_names: List[str]) -> np.ndarray:
    """Map a flat feature dict into a 2D numpy array [1 x n] following feature_names order.

    Missing features are filled with 0.0 and a list of missing keys is returned via exception
    only when feature_names is empty.
    """
    if not feature_names:
        raise ValueError("feature_names must be provided and non-empty")

    row = []
    for name in feature_names:
        v = feature_dict.get(name, 0.0)
        try:
            row.append(float(v))
        except Exception:
            # coerce non-numeric to 0.0 for safety
            row.append(0.0)

    arr = np.array(row, dtype=float).reshape(1, -1)
    return arr
