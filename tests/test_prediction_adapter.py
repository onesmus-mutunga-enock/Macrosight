import types
import numpy as np

from apps.ml.services.prediction_adapter import predict_with_economic_checks


class DummyModel:
    def __init__(self, coefs):
        self.coef_ = np.array(coefs)

    def predict(self, X):
        # simple linear predict using coef_ (no intercept)
        return np.array([float(np.dot(X[0], self.coef_))])


class IdentityScaler:
    def transform(self, X):
        return X


def test_predict_with_economic_checks():
    # model_service stub
    model_service = types.SimpleNamespace()
    model_service.model = DummyModel([0.5, -0.2])
    model_service.scaler = IdentityScaler()
    model_service.feature_names = ['f1', 'f2']
    model_service.feature_set = None

    feature_dict = {'f1': 10, 'f2': 5, 'current_cost': 1}

    out = predict_with_economic_checks(model_service, feature_dict)
    assert 'raw_prediction' in out
    assert 'adjusted_prediction' in out
    assert 'elasticity' in out
    assert 'feature_coefficients' in out
