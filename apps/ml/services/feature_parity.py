"""Utilities to compare training FeatureSet features with runtime build_features output.

Helps detect mismatches between training and scoring feature contracts.
"""
from typing import Dict, List, Tuple


def compare_feature_parity(feature_set_features: List[str], runtime_feature_dict: Dict[str, any]) -> Dict[str, List[str]]:
    """Return keys present/missing/discrepant between training and runtime.

    Returns dict: { 'missing_in_runtime': [...], 'extra_in_runtime': [...], 'common': [...] }
    """
    runtime_keys = set(runtime_feature_dict.keys())
    train_keys = set(feature_set_features)

    missing = list(train_keys - runtime_keys)
    extra = list(runtime_keys - train_keys)
    common = list(train_keys & runtime_keys)

    return {'missing_in_runtime': missing, 'extra_in_runtime': extra, 'common': common}
