import statsmodels.api as sm
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from decimal import Decimal

from apps.ml.models import ModelRegistry, ModelExplainability, FeatureSet
from apps.ml.services.linear_regression_model import LinearRegressionModelService


class EconometricExplainabilityService:
    """
    Service for generating comprehensive econometric analysis and explainability.
    Uses statsmodels for proper statistical inference and hypothesis testing.
    """

    def __init__(self, model_registry: ModelRegistry):
        self.model_registry = model_registry
        self.feature_set = model_registry.feature_set
        self.results = None

    def generate_explainability(self) -> ModelExplainability:
        """
        Generate comprehensive econometric analysis.
        Returns ModelExplainability instance with all statistical results.
        """
        # Load training data
        X, y, feature_names = self._load_data_for_statsmodels()
        
        # Add constant for intercept
        X_with_const = sm.add_constant(X)
        
        # Fit OLS model
        model = sm.OLS(y, X_with_const)
        self.results = model.fit()
        
        # Generate all explainability metrics
        explainability_data = {
            # Coefficient analysis
            'coefficients': self._get_coefficients(),
            'p_values': self._get_p_values(),
            'confidence_intervals': self._get_confidence_intervals(),
            
            # Model statistics
            'r_squared': float(self.results.rsquared),
            'adjusted_r_squared': float(self.results.rsquared_adj),
            'f_statistic': float(self.results.fvalue),
            'f_p_value': float(self.results.f_pvalue),
            
            # Diagnostic tests
            'durbin_watson': float(self._calculate_durbin_watson()),
            'jarque_bera': float(self._calculate_jarque_bera()),
            'jarque_bera_p_value': float(self._calculate_jarque_bera_p_value()),
            
            # Additional diagnostics
            'condition_number': float(self.results.condition_number),
            'aic': float(self.results.aic),
            'bic': float(self.results.bic),
            
            # Feature importance (absolute coefficients)
            'feature_importance': self._get_feature_importance(),
            
            # Residual analysis
            'residual_stats': self._get_residual_statistics(),
            
            # Multicollinearity diagnostics
            'vif': self._calculate_vif(X),
        }
        
        # Create or update explainability record
        explainability, created = ModelExplainability.objects.update_or_create(
            model=self.model_registry,
            defaults=explainability_data
        )
        
        return explainability

    def _load_data_for_statsmodels(self) -> Tuple[np.ndarray, np.ndarray, List[str]]:
        """Load data in format suitable for statsmodels."""
        rows = self.feature_set.dataset.rows.all()
        
        if not rows.exists():
            raise ValueError("No training data found in feature set")
        
        # Convert to DataFrame
        data_list = [row.data for row in rows]
        df = pd.DataFrame(data_list)
        
        # Get feature names (exclude target)
        feature_names = [col for col in df.columns if col != 'sales_target']
        
        # Prepare features and target
        X = df[feature_names].values
        y = df['sales_target'].values
        
        return X, y, feature_names

    def _get_coefficients(self) -> Dict[str, float]:
        """Get regression coefficients."""
        coef_dict = {}
        
        # Constant (intercept)
        coef_dict['const'] = float(self.results.params[0])
        
        # Feature coefficients
        feature_names = self._get_feature_names()
        for i, feature_name in enumerate(feature_names, 1):
            coef_dict[feature_name] = float(self.results.params[i])
        
        return coef_dict

    def _get_p_values(self) -> Dict[str, float]:
        """Get p-values for hypothesis testing."""
        p_dict = {}
        
        # Constant p-value
        p_dict['const'] = float(self.results.pvalues[0])
        
        # Feature p-values
        feature_names = self._get_feature_names()
        for i, feature_name in enumerate(feature_names, 1):
            p_dict[feature_name] = float(self.results.pvalues[i])
        
        return p_dict

    def _get_confidence_intervals(self) -> Dict[str, List[float]]:
        """Get 95% confidence intervals for coefficients."""
        ci_dict = {}
        
        # Constant CI
        ci_dict['const'] = [float(self.results.conf_int().iloc[0, 0]), 
                          float(self.results.conf_int().iloc[0, 1])]
        
        # Feature CIs
        feature_names = self._get_feature_names()
        for i, feature_name in enumerate(feature_names, 1):
            ci_dict[feature_name] = [
                float(self.results.conf_int().iloc[i, 0]),
                float(self.results.conf_int().iloc[i, 1])
            ]
        
        return ci_dict

    def _get_feature_names(self) -> List[str]:
        """Get feature names from the feature set."""
        # Load one row to get feature names
        sample_row = self.feature_set.dataset.rows.first()
        if not sample_row:
            return []
        
        feature_names = [col for col in sample_row.data.keys() if col != 'sales_target']
        return feature_names

    def _calculate_durbin_watson(self) -> float:
        """Calculate Durbin-Watson statistic for autocorrelation."""
        residuals = self.results.resid
        dw_stat = sm.stats.stattools.durbin_watson(residuals)
        return float(dw_stat)

    def _calculate_jarque_bera(self) -> float:
        """Calculate Jarque-Bera test for normality of residuals."""
        jb_stat, jb_p_value = sm.stats.stattools.jarque_bera(self.results.resid)
        return float(jb_stat)

    def _calculate_jarque_bera_p_value(self) -> float:
        """Get Jarque-Bera p-value."""
        jb_stat, jb_p_value = sm.stats.stattools.jarque_bera(self.results.resid)
        return float(jb_p_value)

    def _get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance based on absolute coefficients."""
        importance_dict = {}
        
        # Skip constant for importance
        feature_names = self._get_feature_names()
        for i, feature_name in enumerate(feature_names, 1):
            importance_dict[feature_name] = abs(float(self.results.params[i]))
        
        return importance_dict

    def _get_residual_statistics(self) -> Dict[str, float]:
        """Get residual statistics for model diagnostics."""
        residuals = self.results.resid
        
        return {
            'mean': float(np.mean(residuals)),
            'std': float(np.std(residuals)),
            'skewness': float(stats.skew(residuals)),
            'kurtosis': float(stats.kurtosis(residuals)),
            'min': float(np.min(residuals)),
            'max': float(np.max(residuals))
        }

    def _calculate_vif(self, X: np.ndarray) -> Dict[str, float]:
        """Calculate Variance Inflation Factor for multicollinearity detection."""
        try:
            from statsmodels.stats.outliers_influence import variance_inflation_factor
            
            vif_dict = {}
            feature_names = self._get_feature_names()
            
            # Add constant for VIF calculation
            X_with_const = sm.add_constant(X)
            
            for i, feature_name in enumerate(feature_names, 1):  # Start from 1 to skip constant
                vif = variance_inflation_factor(X_with_const, i)
                vif_dict[feature_name] = float(vif)
            
            return vif_dict
        except ImportError:
            return {}

    def get_model_summary(self) -> str:
        """Get comprehensive model summary as string."""
        if self.results is None:
            self.generate_explainability()
        
        return str(self.results.summary())

    def get_significant_features(self, alpha: float = 0.05) -> List[str]:
        """Get features that are statistically significant at given alpha level."""
        p_values = self._get_p_values()
        significant_features = []
        
        for feature, p_val in p_values.items():
            if feature != 'const' and p_val < alpha:  # Exclude constant
                significant_features.append(feature)
        
        return significant_features

    def get_model_quality_report(self) -> Dict[str, any]:
        """Generate comprehensive model quality report."""
        if self.results is None:
            self.generate_explainability()
        
        # Load explainability data
        explainability = ModelExplainability.objects.get(model=self.model_registry)
        
        # Quality checks
        quality_checks = {
            'r_squared_acceptable': explainability.r_squared >= 0.7,
            'adjusted_r_squared_acceptable': explainability.adjusted_r_squared >= 0.65,
            'f_test_significant': explainability.f_p_value < 0.05,
            'no_autocorrelation': 1.5 <= explainability.durbin_watson <= 2.5,
            'normal_residuals': explainability.jarque_bera_p_value > 0.05,
            'low_multicollinearity': all(vif < 10 for vif in explainability.vif.values()),
            'significant_features_count': len(self.get_significant_features())
        }
        
        overall_quality = sum(quality_checks.values()) / len(quality_checks)
        
        return {
            'quality_score': overall_quality,
            'quality_checks': quality_checks,
            'model_summary': self.get_model_summary(),
            'significant_features': self.get_significant_features(),
            'recommendations': self._generate_recommendations(quality_checks)
        }

    def _generate_recommendations(self, quality_checks: Dict[str, bool]) -> List[str]:
        """Generate recommendations based on quality check results."""
        recommendations = []
        
        if not quality_checks['r_squared_acceptable']:
            recommendations.append("Consider adding more relevant features or using non-linear models")
        
        if not quality_checks['no_autocorrelation']:
            recommendations.append("Consider using time series models (ARIMA, SARIMA) to handle autocorrelation")
        
        if not quality_checks['normal_residuals']:
            recommendations.append("Check for outliers or consider data transformation")
        
        if not quality_checks['low_multicollinearity']:
            recommendations.append("Remove highly correlated features or use regularization")
        
        if quality_checks['significant_features_count'] == 0:
            recommendations.append("No features are statistically significant - review feature selection")
        
        return recommendations