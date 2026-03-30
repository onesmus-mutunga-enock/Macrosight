"""Simulation helpers for scenario analysis.

Lightweight functions that run small, explainable scenarios using the
feature builder, equilibrium and elasticity helpers.
"""
from typing import Optional, Dict
from datetime import date

from apps.intelligence.services.feature_builder import build_features
from .equilibrium import compute_equilibrium_price
from .constraints import enforce_constraints


def simulate_price_change(product_id: int, as_of: Optional[date] = None, delta_cost: Optional[float] = None, delta_demand: Optional[float] = None) -> Dict:
    """Run a simple scenario analysis when cost or demand shifts.

    Steps:
    - Build baseline features
    - Read cost baseline and demand proxy
    - Apply deltas and compute new equilibrium
    - Enforce constraints and return results
    """
    if as_of is None:
        as_of = date.today()

    features = build_features(product_id=product_id, date=as_of)

    # Extract simple proxies
    cost = float(features.get('avg_cost_30d', features.get('current_cost', 0.0)))
    demand_proxy = float(features.get('recent_sales_30d', features.get('avg_daily_sales', 1.0)))

    # Apply deltas
    if delta_cost is not None:
        cost = cost + float(delta_cost)
    if delta_demand is not None:
        demand_proxy = max(0.0, demand_proxy + float(delta_demand))

    # Build a simple linear demand estimate: Q = a - bP
    # Choose b using a heuristic: b = max(1e-6, demand_proxy / max(1.0, features.get('avg_price_30d', 1.0)))
    avg_price = float(features.get('avg_price_30d', features.get('avg_price', 1.0)))
    b = max(1e-6, demand_proxy / max(1.0, avg_price))
    a = demand_proxy + b * avg_price

    demand_params = {'a': float(a), 'b': float(b)}

    p_eq = compute_equilibrium_price(demand_params, cost)
    result = {
        'product_id': int(product_id),
        'as_of': str(as_of),
        'cost': cost,
        'demand_proxy': demand_proxy,
        'demand_params': demand_params,
        'equilibrium_price': p_eq
    }

    # Enforce constraints (price >= cost)
    result['equilibrium_price'] = enforce_constraints(result['equilibrium_price'], cost)

    return result
