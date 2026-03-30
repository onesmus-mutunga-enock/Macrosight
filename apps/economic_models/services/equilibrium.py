"""Equilibrium computations for demand and supply.

Provides a small, well-documented helper to compute an equilibrium
price given simple linear demand and a cost-based supply proxy.
"""
from typing import Dict


def compute_equilibrium_price(demand_params: Dict[str, float], cost: float, supply_slope: float = 1.0) -> float:
    """Compute a simple equilibrium price.

    Demand curve: Q = a - b * P
    Supply proxy: Q_s = supply_slope * (P - cost)  for P > cost, else Q_s = 0

    Solve a - bP = supply_slope*(P - cost)

    Args:
        demand_params: {'a': float, 'b': float}
        cost: marginal cost proxy (float)
        supply_slope: slope of supply proxy (default 1.0)

    Returns:
        Equilibrium price (float), at least cost (price >= cost)
    """
    a = float(demand_params.get('a', 0.0))
    b = float(demand_params.get('b', 1.0))

    # Avoid divide by zero
    denom = b + supply_slope
    if denom == 0:
        # Degenerate case: fall back to price = cost
        return float(cost)

    p_eq = (a + supply_slope * cost) / denom

    # Enforce price >= cost
    if p_eq < cost:
        p_eq = float(cost)

    return float(p_eq)
