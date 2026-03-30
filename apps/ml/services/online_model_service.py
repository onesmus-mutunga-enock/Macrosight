"""Online learning model service using an incremental estimator.

This service wraps sklearn.linear_model.SGDRegressor to provide a
`partial_fit` style online update while keeping persistence compatible
with the project's storage layout.
"""
import os
import joblib
from typing import Optional
import numpy as np

from sklearn.linear_model import SGDRegressor
from sklearn.preprocessing import StandardScaler

from apps.ml.models import ModelRegistry, FeatureSet


class OnlineModelService:
    def __init__(self, feature_set: FeatureSet, model_registry: Optional[ModelRegistry] = None):
        self.feature_set = feature_set
        self.model_registry = model_registry
        self.model = SGDRegressor(max_iter=1, tol=None, warm_start=True)
        self.scaler = StandardScaler()
        self.feature_names = None
        self.model_file_path = None

    def initialize_from_feature_set(self):
        # load feature names from feature_set spec or sample row
        if hasattr(self.feature_set, 'spec') and self.feature_set.spec:
            self.feature_names = self.feature_set.spec.get('features', [])
        else:
            # try to infer from dataset rows
            rows = self.feature_set.dataset.rows.all()
            if rows.exists():
                sample = rows.first().data
                self.feature_names = [k for k in sample.keys() if k != 'sales_target']

    def partial_fit(self, X: np.ndarray, y: np.ndarray):
        """Perform an incremental update using incoming data batch X,y (1xm or nxm)."""
        if self.feature_names is None:
            self.initialize_from_feature_set()

        # Fit scaler incrementally by computing mean/std on this batch (approx)
        self.scaler.partial_fit(X)
        Xs = self.scaler.transform(X)

        # SGDRegressor supports partial_fit; ensure 1D y
        y1 = y.ravel()
        try:
            self.model.partial_fit(Xs, y1)
        except Exception:
            # fallback to fit when partial not possible
            self.model.fit(Xs, y1)

    def predict(self, X: np.ndarray) -> np.ndarray:
        Xs = self.scaler.transform(X)
        return self.model.predict(Xs)

    def save(self, model_registry: ModelRegistry):
        models_dir = 'media/ml_models'
        os.makedirs(models_dir, exist_ok=True)
        filename = f"online_sgd_{model_registry.id}.joblib"
        path = os.path.join(models_dir, filename)
        joblib.dump({'model': self.model, 'scaler': self.scaler, 'feature_names': self.feature_names}, path)
        model_registry.model_file = path
        model_registry.save()

    def load(self, model_registry: ModelRegistry):
        if not model_registry.model_file or not os.path.exists(model_registry.model_file):
            raise ValueError('Model file not found')
        data = joblib.load(model_registry.model_file)
        self.model = data['model']
        self.scaler = data['scaler']
        self.feature_names = data.get('feature_names')
        self.model_registry = model_registry
