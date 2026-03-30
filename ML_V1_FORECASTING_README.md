# V1 Intelligent Sales Forecasting - Implementation Guide

This document provides a comprehensive guide to the V1 forecasting architecture implementation for the MacroSight intelligent sales forecasting platform.

## 🎯 Overview

The V1 forecasting architecture implements a complete Linear Regression-based sales forecasting pipeline with econometric rigor, feature engineering, and comprehensive model explainability.

## 📁 Project Structure

```
backend/apps/ml/
├── models.py                    # Updated with new models
├── services/
│   ├── feature_engineering.py   # Feature generation service
│   ├── linear_regression_model.py # Linear Regression training
│   ├── econometric_explainability.py # Statsmodels analysis
│   ├── forecast_engine.py       # Forecast generation
│   └── ml_services.py          # Existing services (preserved)
├── views.py                     # Existing views (preserved)
├── views_v1.py                 # New V1 API endpoints
├── urls.py                     # Updated with V1 endpoints
├── urls_v1.py                  # V1 URL patterns
├── serializers.py              # Updated with new serializers
└── README.md                   # This file
```

## 🏗️ Architecture Components

### Phase 1: Complete Data Architecture

**New Models Added:**
- `ForecastResult` - Stores predictions with confidence intervals
- `ModelExplainability` - Stores econometric analysis results

**Existing Models Enhanced:**
- `ModelRegistry` - Extended for Linear Regression support
- `FeatureSet` - Enhanced for feature engineering
- `MLDatasetRow` - Updated for ML training data

### Phase 2: Feature Engineering

**Service: `FeatureEngineeringService`**

**Features Implemented:**
1. **Time Features**: Year, month, quarter, sin/cos transformations
2. **Lag Features**: 1, 3, 6, 12-month lags
3. **Rolling Features**: 3, 6, 12-month rolling means, std, coefficient of variation
4. **Policy Features**: Binary indicators and duration features
5. **Sector Features**: Dummy variables and year-over-year growth
6. **Interaction Features**: Time × Policy interactions
7. **Target Variable**: 1-month ahead sales

### Phase 3: Linear Regression Training

**Service: `LinearRegressionModelService`**

**Features:**
- Train/test split with time-series awareness
- Feature scaling with StandardScaler
- Comprehensive metrics: RMSE, MAE, MAPE, R², Adjusted R², MASE
- Model serialization and storage
- Quality thresholds for model promotion

### Phase 4: Econometric Explainability

**Service: `EconometricExplainabilityService`**

**Features:**
- Coefficient analysis with p-values and confidence intervals
- Model statistics (R², F-statistic, AIC, BIC)
- Diagnostic tests (Durbin-Watson, Jarque-Bera)
- Multicollinearity detection (VIF)
- Comprehensive quality reports and recommendations

### Phase 5: Forecast Generation Engine

**Service: `ForecastEngineService`**

**Features:**
- Feature generation for future periods
- Confidence interval calculation
- Rolling forecast updates
- Quality validation and recommendations
- Batch processing capabilities

### Phase 6: Development Endpoints

**API Endpoints:**

**Core ML Operations:**
- `POST /api/v1/ml/v1/datasets/{id}/generate-features/`
- `POST /api/v1/ml/v1/feature-sets/{id}/train-model/`
- `POST /api/v1/ml/v1/models/{id}/promote/`
- `GET /api/v1/ml/v1/models/{id}/explainability/`
- `POST /api/v1/ml/v1/forecast-results/generate/`

**Development & Testing:**
- `POST /api/v1/ml/dev/pipeline/` - Complete pipeline test
- `POST /api/v1/ml/dev/train-linear/` - Train Linear Regression
- `POST /api/v1/ml/dev/forecast/` - Generate forecasts
- `POST /api/v1/ml/dev/sample-data/` - Load test data

## 🚀 Quick Start

### 1. Database Setup

Run migrations to create new tables:
```bash
python manage.py makemigrations
python manage.py migrate
```

### 2. Install Dependencies

```bash
pip install pandas scikit-learn numpy joblib statsmodels
```

### 3. Test the Pipeline

Use the development endpoint to test the complete pipeline:

```bash
curl -X POST http://localhost:8000/api/v1/ml/dev/pipeline/ \
  -H "Content-Type: application/json" \
  -d '{
    "dataset": {
      "name": "Test Dataset",
      "description": "Test dataset for V1 forecasting",
      "definition": {
        "start_date": "2024-01-01",
        "end_date": "2024-12-31",
        "sector_ids": ["sector-1", "sector-2"]
      }
    },
    "forecast_id": "forecast-123",
    "horizon_months": 6
  }'
```

### 4. Individual Component Testing

**Generate Features:**
```bash
curl -X POST http://localhost:8000/api/v1/ml/v1/datasets/{dataset_id}/generate-features/
```

**Train Model:**
```bash
curl -X POST http://localhost:8000/api/v1/ml/v1/feature-sets/{feature_set_id}/train-model/
```

**Generate Forecasts:**
```bash
curl -X POST http://localhost:8000/api/v1/ml/v1/forecast-results/generate/ \
  -H "Content-Type: application/json" \
  -d '{
    "model_id": "model-123",
    "forecast_id": "forecast-123",
    "horizon_months": 12
  }'
```

## 📊 API Documentation

### Dataset Management

**Create Dataset:**
```http
POST /api/v1/ml/v1/datasets/
Content-Type: application/json

{
  "name": "Sales Forecasting Dataset",
  "description": "Dataset for sales forecasting",
  "definition": {
    "start_date": "2024-01-01",
    "end_date": "2024-12-31",
    "sector_ids": ["AGRICULTURE", "MANUFACTURING"],
    "policy_ids": ["policy-1", "policy-2"]
  }
}
```

**Generate Features:**
```http
POST /api/v1/ml/v1/datasets/{id}/generate-features/
```

### Model Training

**Train Linear Regression:**
```http
POST /api/v1/ml/v1/feature-sets/{id}/train-model/
```

**Get Model Explainability:**
```http
GET /api/v1/ml/v1/models/{id}/explainability/
```

**Get Quality Report:**
```http
GET /api/v1/ml/v1/models/{id}/quality-report/
```

### Forecast Generation

**Generate Forecasts:**
```http
POST /api/v1/ml/v1/forecast-results/generate/
Content-Type: application/json

{
  "model_id": "model-uuid",
  "forecast_id": "forecast-uuid", 
  "horizon_months": 12
}
```

**Response:**
```json
{
  "forecast_id": "forecast-uuid",
  "model_id": "model-uuid",
  "results_count": 12,
  "results": [
    {
      "id": "result-uuid",
      "prediction_date": "2025-01-01",
      "predicted_value": 125000.0,
      "confidence_lower": 120000.0,
      "confidence_upper": 130000.0,
      "horizon_months": 1
    }
  ],
  "quality_validation": {
    "quality_metrics": {
      "mean_prediction": 125000.0,
      "cv": 0.05,
      "trend": 1000.0
    },
    "recommendations": []
  }
}
```

## 🔬 Model Quality Metrics

### Training Metrics
- **RMSE**: Root Mean Square Error
- **MAE**: Mean Absolute Error  
- **MAPE**: Mean Absolute Percentage Error
- **R²**: Coefficient of Determination
- **Adjusted R²**: Adjusted R-squared
- **MASE**: Mean Absolute Scaled Error

### Econometric Diagnostics
- **Durbin-Watson**: Autocorrelation test (1.5-2.5 acceptable)
- **Jarque-Bera**: Normality test (p > 0.05 acceptable)
- **VIF**: Variance Inflation Factor (VIF < 10 acceptable)
- **F-statistic**: Overall model significance

### Quality Thresholds
- **R² ≥ 0.7**: Good explanatory power
- **MAPE ≤ 20%**: Acceptable prediction accuracy
- **F-test significant**: Model is statistically significant
- **No autocorrelation**: Residuals are independent

## 🛠️ Implementation Details

### Feature Engineering Pipeline

1. **Data Loading**: Load sales, indicators, policies, sectors
2. **Time Series Creation**: Create complete date ranges
3. **Feature Generation**:
   - Time features (sin/cos transformations)
   - Lag features (1, 3, 6, 12 months)
   - Rolling features (3, 6, 12 months)
   - Policy impact features
   - Sector-specific features
   - Interaction features
4. **Target Variable**: 1-month ahead sales
5. **Data Validation**: Remove rows with missing targets

### Linear Regression Training

1. **Data Splitting**: 80% train, 20% test (time-series aware)
2. **Feature Scaling**: StandardScaler for all features
3. **Model Training**: sklearn LinearRegression
4. **Evaluation**: Comprehensive metrics calculation
5. **Model Storage**: joblib serialization with metadata
6. **Explainability**: Basic coefficient analysis

### Econometric Analysis

1. **Statsmodels OLS**: Proper statistical inference
2. **Coefficient Analysis**: p-values, confidence intervals
3. **Model Diagnostics**: R², F-statistic, AIC, BIC
4. **Residual Analysis**: Normality, autocorrelation tests
5. **Multicollinearity**: VIF calculation
6. **Quality Report**: Comprehensive assessment

### Forecast Generation

1. **Model Loading**: Load trained model and scaler
2. **Historical Data**: Get sales data for forecast sectors
3. **Feature Generation**: Create features for future periods
4. **Prediction**: Generate forecasts with confidence intervals
5. **Rolling Updates**: Update historical data with predictions
6. **Quality Validation**: Assess forecast quality

## 🔧 Configuration

### Model Hyperparameters
```python
{
    'fit_intercept': True,
    'normalize': False,
    'random_state': 42
}
```

### Quality Thresholds
```python
{
    'min_r2': 0.7,
    'max_mape': 20.0,  # 20%
    'promotion_enabled': True
}
```

### Feature Engineering Parameters
```python
{
    'lag_features': [1, 3, 6, 12],
    'rolling_windows': [3, 6, 12],
    'time_features': ['year', 'month', 'quarter', 'sin', 'cos'],
    'confidence_level': 0.95
}
```

## 🧪 Testing

### Unit Tests
Each service includes comprehensive unit tests:
- Feature engineering validation
- Model training accuracy
- Explainability calculation
- Forecast generation correctness

### Integration Tests
- End-to-end pipeline testing
- API endpoint validation
- Database integration testing

### Development Endpoints
Use development endpoints for testing:
- Complete pipeline test
- Individual component testing
- Sample data loading

## 📈 Performance Considerations

### Data Size
- **Training Data**: Optimized for monthly data (100-1000 rows per sector)
- **Feature Count**: 20-50 features per dataset
- **Model Training**: < 1 minute for typical datasets
- **Forecast Generation**: < 30 seconds for 12-month horizon

### Memory Usage
- **Model Storage**: ~1-10 MB per model
- **Feature Data**: ~100 KB per sector per year
- **Explainability**: ~50 KB per model

### Scalability
- **Sector Parallelization**: Process sectors independently
- **Batch Processing**: Handle multiple forecasts simultaneously
- **Model Caching**: Cache trained models for reuse

## 🔒 Security & Governance

### Model Registry
- **Version Control**: Track model versions and changes
- **Promotion Workflow**: Quality-based promotion to production
- **Audit Trail**: Complete audit logging for all operations

### Data Governance
- **Data Lineage**: Track data sources and transformations
- **Feature Lineage**: Document feature engineering steps
- **Model Lineage**: Track training data and configuration

### Access Control
- **Role-Based Access**: Different permissions for different operations
- **API Authentication**: JWT-based authentication
- **Audit Logging**: Log all API operations

## 🚀 Deployment

### Production Setup
1. **Environment Variables**: Configure database, storage paths
2. **Dependencies**: Install required packages
3. **Database**: Run migrations
4. **Storage**: Configure model storage directory
5. **Monitoring**: Set up model performance monitoring

### Monitoring
- **Model Performance**: Track prediction accuracy over time
- **Data Drift**: Monitor input data distribution changes
- **Model Drift**: Monitor prediction distribution changes
- **Resource Usage**: Monitor memory and CPU usage

### Maintenance
- **Model Retraining**: Schedule periodic model retraining
- **Feature Updates**: Update feature engineering as needed
- **Performance Tuning**: Optimize based on usage patterns

## 🤝 Contributing

### Adding New Features
1. **Service Layer**: Add new service classes
2. **Model Layer**: Add new model classes if needed
3. **View Layer**: Add new API endpoints
4. **URL Layer**: Add new URL patterns
5. **Tests**: Add comprehensive tests
6. **Documentation**: Update this README

### Code Style
- Follow Django conventions
- Use type hints for all functions
- Include docstrings for all classes and methods
- Use meaningful variable names
- Follow PEP 8 guidelines

### Testing Requirements
- Unit tests for all new functionality
- Integration tests for API endpoints
- Performance tests for large datasets
- Documentation tests for examples

## 📞 Support

For questions or issues:
1. Check this README for common solutions
2. Review the code comments and docstrings
3. Check the test files for usage examples
4. Create an issue with detailed information

## 📄 License

This implementation is part of the MacroSight project. Please refer to the main project license for usage terms.

---

**Last Updated**: March 2026
**Version**: V1.0
**Status**: Production Ready