import joblib
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, mean_absolute_error, mean_absolute_percentage_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import os
import json

from apps.ml.models import ModelRegistry, FeatureSet, ForecastResult, ModelExplainability
from apps.ml.services.feature_engineering import FeatureEngineeringService
from apps.ml.services.prediction_adapter import predict_with_economic_checks


class LinearRegressionModelService:
    """
    Service for training Linear Regression models with comprehensive metrics.
    """

    def __init__(self, feature_set: FeatureSet):
        self.feature_set = feature_set
        self.model = None
        self.scaler = StandardScaler()
        self.feature_names = None
        self.model_file_path = None

    def train_model(self) -> ModelRegistry:
        """
        Train Linear Regression model and register it in ModelRegistry.
        Returns the registered model instance.
        """
        # Load training data
        X, y = self._load_training_data()
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, shuffle=False
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train model
        self.model = LinearRegression()
        self.model.fit(X_train_scaled, y_train)
        
        # Evaluate model
        train_metrics = self._calculate_metrics(X_train_scaled, y_train, 'train')
        test_metrics = self._calculate_metrics(X_test_scaled, y_test, 'test')
        
        # Calculate feature importance (coefficients)
        feature_importance = dict(zip(self.feature_names, self.model.coef_))
        
        # Create model registry entry
        model_registry = ModelRegistry.objects.create(
            name=f"LinearRegression_{self.feature_set.dataset.name}",
            description=f"Linear Regression model trained on {self.feature_set.dataset.name}",
            algorithm="LinearRegression",
            version="1.0.0",
            status=ModelRegistry.Status.CANDIDATE,
            hyperparameters={
                'fit_intercept': True,
                'normalize': False,
                'random_state': 42
            },
            metrics={
                'train_metrics': train_metrics,
                'test_metrics': test_metrics,
                'feature_importance': feature_importance
            },
            feature_set=self.feature_set,
            created_by_id=1  # Default to first user, should be passed as parameter
        )
        
        # Save model file
        self._save_model_file(model_registry)
        
        # Generate explainability analysis
        self._generate_explainability(model_registry, X_test_scaled, y_test)
        
        return model_registry

    def _load_training_data(self) -> Tuple[np.ndarray, np.ndarray]:
        """Load training data from feature set."""
        rows = self.feature_set.dataset.rows.all()
        
        if not rows.exists():
            raise ValueError("No training data found in feature set")
        
        # Convert to DataFrame
        data_list = [row.data for row in rows]
        df = pd.DataFrame(data_list)
        
        # Get feature names (exclude target)
        self.feature_names = [col for col in df.columns if col != 'sales_target']
        
        # Prepare features and target
        X = df[self.feature_names].values
        y = df['sales_target'].values
        
        return X, y

    def _calculate_metrics(self, X: np.ndarray, y_true: np.ndarray, dataset_type: str) -> Dict:
        """Calculate comprehensive metrics for the model."""
        y_pred = self.model.predict(X)
        
        # Basic metrics
        mse = mean_squared_error(y_true, y_pred)
        rmse = np.sqrt(mse)
        mae = mean_absolute_error(y_true, y_pred)
        mape = mean_absolute_percentage_error(y_true, y_pred) * 100  # Convert to percentage
        r2 = r2_score(y_true, y_pred)
        
        # Additional metrics
        n = len(y_true)
        k = X.shape[1]  # Number of features
        
        # Adjusted R²
        adj_r2 = 1 - (1 - r2) * (n - 1) / (n - k - 1)
        
        # Mean Absolute Scaled Error (MASE) - simplified version
        naive_forecast_error = np.mean(np.abs(np.diff(y_true)))
        mase = mae / naive_forecast_error if naive_forecast_error > 0 else np.inf
        
        return {
            'dataset_type': dataset_type,
            'mse': float(mse),
            'rmse': float(rmse),
            'mae': float(mae),
            'mape': float(mape),
            'r2': float(r2),
            'adjusted_r2': float(adj_r2),
            'mase': float(mase),
            'n_samples': int(n),
            'n_features': int(k)
        }

    def _save_model_file(self, model_registry: ModelRegistry):
        """Save trained model to file system."""
        # Create models directory if it doesn't exist
        models_dir = 'media/ml_models'
        os.makedirs(models_dir, exist_ok=True)
        
        # Generate filename
        filename = f"linear_regression_{model_registry.id}.joblib"
        self.model_file_path = os.path.join(models_dir, filename)
        
        # Save model and scaler
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'feature_names': self.feature_names,
            'created_at': datetime.now().isoformat()
        }
        
        joblib.dump(model_data, self.model_file_path)
        
        # Update model registry with file path
        model_registry.model_file = self.model_file_path
        model_registry.save()

    def _generate_explainability(self, model_registry: ModelRegistry, X_test: np.ndarray, y_test: np.ndarray):
        """Generate econometric explainability analysis."""
        # This will be enhanced in Phase 4 with statsmodels
        # For now, create basic explainability entry
        
        explainability = ModelExplainability.objects.create(
            model=model_registry,
            coefficients=dict(zip(self.feature_names, self.model.coef_)),
            r_squared=float(r2_score(y_test, self.model.predict(X_test))),
            feature_importance=dict(zip(self.feature_names, np.abs(self.model.coef_)))
        )
        
        return explainability

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Make predictions using the trained model."""
        if self.model is None:
            raise ValueError("Model not trained yet. Call train_model() first.")
        
        X_scaled = self.scaler.transform(X)
        return self.model.predict(X_scaled)

    def predict_with_checks_from_dict(self, feature_dict: dict) -> dict:
        """Predict from a feature-name->value mapping and apply economic checks.

        Returns the adapter result which includes 'raw_prediction',
        'adjusted_prediction', and 'elasticity' when available.
        """
        if self.model is None:
            raise ValueError("Model not loaded or trained")

        return predict_with_economic_checks(self, feature_dict)

    def predict_with_checks_from_array(self, X: np.ndarray) -> dict:
        """Predict from a feature array (1 x n) using the model's feature_names.

        This convenience method converts the array to a feature dict and
        delegates to `predict_with_checks_from_dict`.
        """
        if self.feature_names is None:
            raise ValueError("Feature names are not set on the model service")

        if X.ndim == 1:
            X = X.reshape(1, -1)

        feature_dict = {name: float(X[0, idx]) for idx, name in enumerate(self.feature_names) if idx < X.shape[1]}
        return self.predict_with_checks_from_dict(feature_dict)

    def load_model(self, model_registry: ModelRegistry):
        """Load a saved model from file."""
        if not model_registry.model_file or not os.path.exists(model_registry.model_file):
            raise ValueError("Model file not found")
        
        model_data = joblib.load(model_registry.model_file)
        self.model = model_data['model']
        self.scaler = model_data['scaler']
        self.feature_names = model_data['feature_names']

    @staticmethod
    def promote_model(model_registry: ModelRegistry) -> bool:
        """
        Promote a model to ACTIVE status.
        Returns True if promotion successful.
        """
        if model_registry.status != ModelRegistry.Status.CANDIDATE:
            return False
        
        # Check if model meets quality thresholds
        metrics = model_registry.metrics
        test_metrics = metrics.get('test_metrics', {})
        
        # Example quality thresholds
        min_r2 = 0.7
        max_mape = 20.0  # 20%
        
        if (test_metrics.get('r2', 0) >= min_r2 and 
            test_metrics.get('mape', float('inf')) <= max_mape):
            
            model_registry.status = ModelRegistry.Status.ACTIVE
            model_registry.save()
            return True
        
        return False