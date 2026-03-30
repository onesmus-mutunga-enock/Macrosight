"""Service for training/predicting price models (parallel to sales models).

Non-invasive helper: mirrors LinearRegressionModelService but focused on
`price_target` so the system can train/predict product price separately.
"""
import joblib
import numpy as np
from datetime import datetime
from typing import Dict, Tuple
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler

from apps.ml.models import ModelRegistry, FeatureSet


class PriceModelService:
    def __init__(self, feature_set: FeatureSet):
        self.feature_set = feature_set
        self.model = None
        self.scaler = StandardScaler()
        self.feature_names = None

    def _load_training_data(self) -> Tuple[np.ndarray, np.ndarray]:
        rows = self.feature_set.dataset.rows.all()
        if not rows.exists():
            raise ValueError('No training data found')
        data = [r.data for r in rows]
        import pandas as pd
        df = pd.DataFrame(data)
        self.feature_names = [c for c in df.columns if c != 'price_target']
        X = df[self.feature_names].values
        y = df['price_target'].values
        return X, y

    def train_model(self) -> ModelRegistry:
        X, y = self._load_training_data()
        Xs = self.scaler.fit_transform(X)
        self.model = LinearRegression()
        self.model.fit(Xs, y)

        feature_importance = dict(zip(self.feature_names, self.model.coef_))

        model_registry = ModelRegistry.objects.create(
            name=f"PriceModel_{self.feature_set.dataset.name}",
            description=f"Price model for {self.feature_set.dataset.name}",
            algorithm='LinearRegression',
            version='1.0.0',
            status=ModelRegistry.Status.CANDIDATE,
            hyperparameters={},
            metrics={'feature_importance': feature_importance},
            feature_set=self.feature_set,
            created_by_id=1,
        )

        # save model file
        models_dir = 'media/ml_models'
        import os
        os.makedirs(models_dir, exist_ok=True)
        filename = f"price_model_{model_registry.id}.joblib"
        path = os.path.join(models_dir, filename)
        joblib.dump({'model': self.model, 'scaler': self.scaler, 'feature_names': self.feature_names, 'created_at': datetime.now().isoformat()}, path)
        model_registry.model_file = path
        model_registry.save()

        return model_registry

    def load_model(self, model_registry: ModelRegistry):
        if not model_registry.model_file:
            raise ValueError('Model file missing')
        data = joblib.load(model_registry.model_file)
        self.model = data['model']
        self.scaler = data['scaler']
        self.feature_names = data.get('feature_names')

    def predict(self, X: np.ndarray) -> np.ndarray:
        if self.model is None:
            raise ValueError('Model not loaded')
        Xs = self.scaler.transform(X)
        return self.model.predict(Xs)
