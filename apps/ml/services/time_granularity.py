"""Helpers to align runtime features with model training frequency.

These are conservative helpers that attempt non-destructive conversions
when a model expects monthly features but runtime features are daily.
"""
from typing import Dict


def align_features_for_frequency(feature_dict: Dict[str, any], frequency: str) -> Dict[str, any]:
    """Return a possibly-adjusted feature dict for target frequency.

    Current implementation is conservative: it does not invent new
    features, but will convert simple daily aggregates into monthly
    proxies when obvious keys exist.
    """
    out = dict(feature_dict)
    if frequency == 'M':
        # If we have recent_sales_30d but model expects monthly_sales_estimate,
        # provide a monthly estimate by using the 30-day total as a proxy.
        if 'recent_sales_30d' in feature_dict and 'monthly_sales_estimate' not in out:
            out['monthly_sales_estimate'] = float(feature_dict.get('recent_sales_30d', 0.0))

    return out
