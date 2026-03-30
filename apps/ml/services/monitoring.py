"""Simple monitoring utilities for model prediction drift and data quality.

These helpers are lightweight and intended as a starting point for
integration with real monitoring/alerting infrastructure.
"""
from typing import Iterable
import numpy as np


def basic_prediction_drift_score(recent_predictions: Iterable[float], recent_actuals: Iterable[float]) -> float:
    """Return a simple drift score: normalized absolute mean error.

    Score near 0 => no drift; larger values indicate drift.
    """
    preds = np.array(list(recent_predictions), dtype=float)
    acts = np.array(list(recent_actuals), dtype=float)
    if preds.size == 0 or acts.size == 0:
        return 0.0
    mae = float(np.mean(np.abs(preds - acts)))
    denom = float(np.mean(np.abs(acts))) or 1.0
    return mae / denom
