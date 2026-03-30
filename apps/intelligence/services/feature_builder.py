"""
Centralized cross-app feature builder for economic intelligence.
Orchestrates features from products, sales, costs for ML pipeline.
Compatible with existing linear regression.
"""
from typing import Dict, Any, Union, Optional
from datetime import date
from .product_features import get_product_features
from .sales_features import get_sales_features
from .cost_features import get_cost_features
# Placeholder for external (indicators etc.)
def get_external_features(sector_id: int, date: date) -> Dict[str, float]:
    """
    Placeholder for external macro features (inflation, etc.).
    Integrate with apps.indicators.
    """
    features = {'inflation_proxy': 0.02, 'gdp_growth_proxy': 0.03}

    # Try to enrich with indicators app
    try:
        from apps.indicators.services import get_indicator_features as _ind_feats
        feats = _ind_feats(sector_id=sector_id, date=date)
        if isinstance(feats, dict):
            features.update(feats)
    except Exception:
        pass

    # Try to enrich with externalindicator app
    try:
        from apps.externalindicator.services import get_external_indicator_features as _ext_feats
        feats = _ext_feats(sector_id=sector_id, date=date)
        if isinstance(feats, dict):
            features.update(feats)
    except Exception:
        pass

    # Try to include policy proxies
    try:
        from apps.policies.services import get_policy_features as _pol_feats
        feats = _pol_feats(sector_id=sector_id, date=date)
        if isinstance(feats, dict):
            features.update(feats)
    except Exception:
        pass

    return features


def build_features(
    product_id: Optional[Union[int, str]] = None,
    date: Optional[date] = None,
    sector_id: Optional[int] = None
) -> Dict[str, float]:
    """Centralized feature builder that merges cross-app features.

    Returns a flat dict of features deterministic by key names. Does not
    change existing persistence or training formats; it simply aggregates
    product, sales, cost and external features into one mapping.
    """
    if date is None:
        date = date.today()

    if product_id is None and sector_id is None:
        raise ValueError('Either product_id or sector_id must be provided')

    # Product features
    product_features = {}
    try:
        product_features = get_product_features(product_id) if product_id is not None else {}
    except Exception:
        product_features = {}

    # Determine sector: prefer explicit sector_id, else try product attributes
    resolved_sector = sector_id
    if resolved_sector is None and product_id is not None:
        try:
            # product_features may include a category/sector id
            resolved_sector = int(product_features.get('category_id', 0)) or None
        except Exception:
            resolved_sector = None

    # If product-level marginal cost helper exists, add current_cost
    try:
        from apps.costs.services.cost_helpers import get_product_marginal_cost
        if product_id is not None:
            mc = get_product_marginal_cost(product_id, date)
            if mc:
                cost_features.setdefault('current_cost', mc)
    except Exception:
        pass

    # Sales features
    try:
        sales_features = get_sales_features(product_id=product_id, sector_id=resolved_sector, as_of=date)
    except Exception:
        sales_features = {}

    # Cost features
    try:
        if resolved_sector is not None:
            cost_features = get_cost_features(resolved_sector, date)
        else:
            cost_features = {}
    except Exception:
        cost_features = {}

    # External features (macro proxies)
    try:
        external_features = get_external_features(resolved_sector or 0, date)
    except Exception:
        external_features = {}

    # Merge deterministically: sorted by key name
    merged = {}
    for source in (product_features, sales_features, cost_features, external_features):
        for k, v in source.items():
            merged[k] = v

    return merged
