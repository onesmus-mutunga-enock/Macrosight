"""Train multiple targets (sales and price) from a single FeatureSet.

This service trains a sales model using `LinearRegressionModelService` and,
when `price_target` exists in the dataset, trains a separate price model
using `PriceModelService` to keep responsibilities separated.
"""
from typing import Dict

from apps.ml.services.linear_regression_model import LinearRegressionModelService
from apps.ml.services.price_model_service import PriceModelService


class MultiTargetTrainer:
    def __init__(self, feature_set):
        self.feature_set = feature_set

    def train(self) -> Dict[str, int]:
        results = {}

        # Train sales model (existing flow)
        sales_service = LinearRegressionModelService(self.feature_set)
        sales_registry = sales_service.train_model()
        results['sales_model_id'] = sales_registry.id

        # Check for price target
        # Use dataset rows to detect presence of 'price_target'
        try:
            rows = self.feature_set.dataset.rows.all()
            if rows.exists():
                sample = rows.first().data
                if 'price_target' in sample:
                    price_service = PriceModelService(self.feature_set)
                    price_registry = price_service.train_model()
                    results['price_model_id'] = price_registry.id
        except Exception:
            # skip price model on error
            pass

        return results
