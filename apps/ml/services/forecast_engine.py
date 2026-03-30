import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from decimal import Decimal
import joblib
import os

from apps.ml.models import ModelRegistry, ForecastResult, FeatureSet
from apps.forecasts.models import Forecast
from apps.sales.models import Sale as Sales
from apps.ml.services.feature_engineering import FeatureEngineeringService
from apps.ml.services.prediction_adapter import predict_with_economic_checks


class ForecastEngineService:
    """
    Service for generating forecasts using trained models.
    Handles prediction generation with confidence intervals.
    """

    def __init__(self, model_registry: ModelRegistry):
        self.model_registry = model_registry
        self.feature_set = model_registry.feature_set
        self.model = None
        self.scaler = None
        self.feature_names = None

    def load_model(self):
        """Load the trained model from file."""
        if not self.model_registry.model_file or not os.path.exists(self.model_registry.model_file):
            raise ValueError("Model file not found")
        
        model_data = joblib.load(self.model_registry.model_file)
        self.model = model_data['model']
        self.scaler = model_data['scaler']
        self.feature_names = model_data['feature_names']

    def generate_forecast(self, forecast: Forecast, horizon_months: int = 12) -> List[ForecastResult]:
        """
        Generate forecasts for a given forecast object.
        Returns list of ForecastResult instances.
        """
        if self.model is None:
            self.load_model()
        
        # Get historical data for feature generation
        historical_data = self._get_historical_data(forecast)
        
        # Generate forecast periods
        forecast_periods = self._generate_forecast_periods(forecast, horizon_months)
        
        # Generate features for each forecast period
        forecast_results = []
        for period in forecast_periods:
            features = self._generate_forecast_features(historical_data, period)
            
            # Make prediction
            prediction = self._make_prediction(features)
            
            # Calculate confidence intervals
            confidence_lower, confidence_upper = self._calculate_confidence_intervals(features)
            
            # Create forecast result
            result = ForecastResult.objects.create(
                forecast=forecast,
                model=self.model_registry,
                predicted_value=Decimal(str(prediction)),
                confidence_lower=Decimal(str(confidence_lower)),
                confidence_upper=Decimal(str(confidence_upper)),
                prediction_date=period,
                horizon_months=(period.year - forecast.start_date.year) * 12 + (period.month - forecast.start_date.month),
                model_metrics=self._get_model_metrics()
            )
            
            forecast_results.append(result)
            
            # Update historical data with prediction for next iteration
            historical_data = self._update_historical_data(historical_data, period, prediction)
        
        return forecast_results

    def _get_historical_data(self, forecast: Forecast) -> pd.DataFrame:
        """Get historical sales data for the forecast."""
        # Get sales data for the sectors in this forecast
        sales_data = Sales.objects.filter(
            date__lte=forecast.start_date,
            sector_id__in=forecast.sectors.values_list('id', flat=True)
        ).values('date', 'value', 'sector_id')
        
        df = pd.DataFrame(list(sales_data))
        if df.empty:
            raise ValueError("No historical data found for forecast")
        
        df['date'] = pd.to_datetime(df['date'])
        df['value'] = df['value'].astype(float)
        
        # Aggregate by month and sector
        df = df.groupby(['date', 'sector_id'])['value'].sum().reset_index()
        
        return df

    def _generate_forecast_periods(self, forecast: Forecast, horizon_months: int) -> List[datetime]:
        """Generate list of forecast periods."""
        periods = []
        current_date = forecast.start_date.replace(day=1)
        
        for i in range(horizon_months):
            forecast_date = current_date + pd.DateOffset(months=i)
            periods.append(forecast_date)
        
        return periods

    def _generate_forecast_features(self, historical_data: pd.DataFrame, forecast_date: datetime) -> np.ndarray:
        """Generate features for a specific forecast date."""
        # Create a copy of historical data
        df = historical_data.copy()
        
        # Add the forecast date with NaN value
        forecast_row = pd.DataFrame({
            'date': [forecast_date],
            'value': [np.nan],
            'sector_id': [historical_data['sector_id'].iloc[0]]  # Use first sector
        })
        
        df = pd.concat([df, forecast_row], ignore_index=True)
        df = df.sort_values(['sector_id', 'date']).reset_index(drop=True)
        
        # Generate features (similar to training)
        df = self._add_time_features(df)
        df = self._add_lag_features(df)
        df = self._add_rolling_features(df)
        df = self._add_sector_features(df, forecast_date)
        
        # Get the row for forecast date
        forecast_row = df[df['date'] == forecast_date].iloc[0]
        
        # Extract feature values in the same order as training
        feature_values = []
        for feature_name in self.feature_names:
            if feature_name in forecast_row:
                value = forecast_row[feature_name]
                feature_values.append(float(value) if pd.notna(value) else 0.0)
            else:
                feature_values.append(0.0)
        
        return np.array(feature_values).reshape(1, -1)

    def _add_time_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add time-based features."""
        df['year'] = df['date'].dt.year
        df['month'] = df['date'].dt.month
        df['quarter'] = df['date'].dt.quarter
        df['month_sin'] = np.sin(2 * np.pi * df['month'] / 12)
        df['month_cos'] = np.cos(2 * np.pi * df['month'] / 12)
        return df

    def _add_lag_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add lag features."""
        for lag in [1, 3, 6, 12]:
            df[f'sales_lag_{lag}'] = df.groupby('sector_id')['value'].shift(lag)
        return df

    def _add_rolling_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add rolling average features."""
        for window in [3, 6, 12]:
            df[f'sales_rolling_mean_{window}'] = (
                df.groupby('sector_id')['value']
                .rolling(window=window, min_periods=1)
                .mean()
                .reset_index(0, drop=True)
            )
            
            df[f'sales_rolling_std_{window}'] = (
                df.groupby('sector_id')['value']
                .rolling(window=window, min_periods=1)
                .std()
                .reset_index(0, drop=True)
            )
        return df

    def _add_sector_features(self, df: pd.DataFrame, forecast_date: datetime) -> pd.DataFrame:
        """Add sector-specific features."""
        # Add sector dummies
        sectors = df['sector_id'].unique()
        for sector_id in sectors:
            df[f'sector_{sector_id}'] = (df['sector_id'] == sector_id).astype(int)
        
        # Add sector growth rate
        df['sector_growth_yoy'] = (
            df.groupby('sector_id')['value']
            .pct_change(periods=12)
            .fillna(0)
        )
        
        return df

    def _make_prediction(self, features: np.ndarray) -> float:
        """Make prediction using the trained model and economic checks.

        Converts the feature vector into a feature dict matching
        `self.feature_names`, builds a minimal proxy for the model
        service and invokes the prediction adapter which applies
        constraints and computes elasticity when possible.
        """
        # Build feature dict in same order as feature_names
        feature_names = self.feature_names or []
        feature_dict = {}
        try:
            for i, name in enumerate(feature_names):
                feature_dict[name] = float(features[0, i])
        except Exception:
            # Fallback: empty mapping
            feature_dict = {}

        # Create a lightweight proxy object compatible with adapter
        class _ModelProxy:
            pass

        proxy = _ModelProxy()
        proxy.model = self.model
        proxy.scaler = self.scaler
        proxy.feature_names = self.feature_names
        proxy.feature_set = self.feature_set

        result = predict_with_economic_checks(proxy, feature_dict)

        # Prefer adjusted_prediction when available
        adjusted = result.get('adjusted_prediction')
        if isinstance(adjusted, dict):
            # If adapter returned a dict (e.g., price/demand map), try to extract a numeric value
            # Prefer 'demand' or 'price' keys falling back to raw_prediction
            for k in ('demand', 'price'):
                if k in adjusted:
                    try:
                        return float(adjusted[k])
                    except Exception:
                        continue
            # fallback
            return float(result.get('raw_prediction', 0.0))

        try:
            return float(adjusted)
        except Exception:
            return float(result.get('raw_prediction', 0.0))

    def _calculate_confidence_intervals(self, features: np.ndarray, confidence_level: float = 0.95) -> Tuple[float, float]:
        """
        Calculate confidence intervals for the prediction.
        Uses the standard error of regression for interval estimation.
        """
        # Get prediction
        prediction = self._make_prediction(features)
        
        # Calculate prediction standard error (simplified approach)
        # In practice, this would use the full covariance matrix
        # For now, we'll use a heuristic based on training RMSE
        
        # Get training RMSE from model metrics
        train_metrics = self.model_registry.metrics.get('train_metrics', {})
        rmse = train_metrics.get('rmse', 1.0)
        
        # Calculate z-score for confidence level
        z_score = self._get_z_score(confidence_level)
        
        # Calculate margin of error
        margin_of_error = z_score * rmse
        
        lower_bound = prediction - margin_of_error
        upper_bound = prediction + margin_of_error
        
        return float(lower_bound), float(upper_bound)

    def _get_z_score(self, confidence_level: float) -> float:
        """Get z-score for given confidence level."""
        # Simplified z-score lookup
        z_scores = {
            0.90: 1.645,
            0.95: 1.96,
            0.99: 2.576
        }
        return z_scores.get(confidence_level, 1.96)

    def _update_historical_data(self, historical_data: pd.DataFrame, forecast_date: datetime, prediction: float) -> pd.DataFrame:
        """Update historical data with new prediction for next iteration."""
        new_row = pd.DataFrame({
            'date': [forecast_date],
            'value': [prediction],
            'sector_id': [historical_data['sector_id'].iloc[0]]
        })
        
        updated_data = pd.concat([historical_data, new_row], ignore_index=True)
        return updated_data.sort_values(['sector_id', 'date']).reset_index(drop=True)

    def _get_model_metrics(self) -> Dict:
        """Get model performance metrics for the forecast result."""
        return {
            'model_name': self.model_registry.name,
            'model_version': self.model_registry.version,
            'algorithm': self.model_registry.algorithm,
            'test_rmse': self.model_registry.metrics.get('test_metrics', {}).get('rmse', 0),
            'test_r2': self.model_registry.metrics.get('test_metrics', {}).get('r2', 0),
            'feature_count': len(self.feature_names)
        }

    @staticmethod
    def batch_generate_forecasts(model_registry: ModelRegistry, forecasts: List[Forecast], horizon_months: int = 12) -> Dict[str, List[ForecastResult]]:
        """
        Generate forecasts for multiple forecast objects.
        Returns dictionary mapping forecast IDs to their results.
        """
        engine = ForecastEngineService(model_registry)
        engine.load_model()
        
        results = {}
        for forecast in forecasts:
            try:
                forecast_results = engine.generate_forecast(forecast, horizon_months)
                results[str(forecast.id)] = forecast_results
            except Exception as e:
                results[str(forecast.id)] = f"Error: {str(e)}"
        
        return results

    def validate_forecast_quality(self, forecast_results: List[ForecastResult]) -> Dict[str, any]:
        """Validate forecast quality and provide recommendations."""
        predictions = [float(result.predicted_value) for result in forecast_results]
        
        # Basic quality checks
        quality_metrics = {
            'mean_prediction': np.mean(predictions),
            'std_prediction': np.std(predictions),
            'cv': np.std(predictions) / np.mean(predictions) if np.mean(predictions) > 0 else 0,
            'trend': self._calculate_trend(predictions),
            'confidence_width_avg': np.mean([
                float(result.confidence_upper) - float(result.confidence_lower) 
                for result in forecast_results
            ])
        }
        
        # Generate recommendations
        recommendations = []
        if quality_metrics['cv'] > 0.5:
            recommendations.append("High coefficient of variation - consider model refinement")
        
        if abs(quality_metrics['trend']) > 0.1:
            recommendations.append("Strong trend detected - verify with domain experts")
        
        if quality_metrics['confidence_width_avg'] > quality_metrics['mean_prediction'] * 0.5:
            recommendations.append("Wide confidence intervals - model uncertainty is high")
        
        return {
            'quality_metrics': quality_metrics,
            'recommendations': recommendations
        }

    def _calculate_trend(self, predictions: List[float]) -> float:
        """Calculate trend in predictions."""
        if len(predictions) < 2:
            return 0.0
        
        x = np.arange(len(predictions))
        y = np.array(predictions)
        
        # Linear regression to get trend
        slope = np.polyfit(x, y, 1)[0]
        return float(slope)