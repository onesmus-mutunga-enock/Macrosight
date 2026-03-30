"""Prediction constraint utilities to enforce realistic outputs.

Keep predictions within economically sensible bounds, e.g.
price >= cost and demand >= 0.
"""
from typing import Union, Dict


def enforce_constraints(prediction: Union[float, Dict[str, float]], cost: float) -> Union[float, Dict[str, float]]:
    """Enforce minimal economic constraints on predictions.

    Args:
        prediction: either a numeric price/demand value or a dict containing
                    keys like 'price' and 'demand'.
        cost: cost floor for prices.

    Returns:
        Adjusted prediction with constraints enforced.
    """
    if isinstance(prediction, dict):
        p = prediction.copy()
        # Enforce price floor
        if 'price' in p:
            try:
                p['price'] = max(float(p['price']), float(cost))
            except Exception:
                p['price'] = float(cost)

        # Enforce non-negative demand
        if 'demand' in p:
            try:
                p['demand'] = max(float(p['demand']), 0.0)
            except Exception:
                p['demand'] = 0.0

        return p

    # Numeric prediction assumed to be price: enforce price >= cost
    try:
        return max(float(prediction), float(cost))
    except Exception:
        return float(cost)
