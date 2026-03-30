import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from decimal import Decimal

from apps.ml.models import Dataset, FeatureSet, MLDataset, MLDatasetRow
from apps.forecasts.models import Forecast
from apps.sales.models import Sale as Sales
from apps.indicators.models import Indicator
from apps.policies.models import Policy
from apps.sectors.models import Sector


class FeatureEngineeringService:
    """
    Service for generating ML features from datasets.
    Implements the 10 required features for Linear Regression forecasting.
    """

    def __init__(self, dataset: Dataset):
        self.dataset = dataset
        self.definition = dataset.definition
        self.df = None

    def generate_features(self) -> FeatureSet:
        """
        Generate feature set from dataset with all required features.
        Returns FeatureSet with feature specifications.
        """
        # Load raw data
        self._load_data()
        
        # Generate all features
        self._generate_time_features()
        self._generate_lag_features()
        self._generate_rolling_features()
        self._generate_policy_features()
        self._generate_sector_features()
        self._generate_interaction_features()
        self._generate_target_variable()
        
        # Create feature set
        feature_spec = {
            'features': self._get_feature_list(),
            'target': 'sales_target',
            'date_column': 'date',
            'generated_at': datetime.now().isoformat(),
            'data_shape': self.df.shape,
            'feature_count': len(self._get_feature_list())
        }
        
        feature_set = FeatureSet.objects.create(
            dataset=self.dataset,
            name=f"{self.dataset.name}_features",
            description=f"Generated features for {self.dataset.name}",
            spec=feature_spec
        )
        
        # Save feature rows
        self._save_feature_rows(feature_set)
        
        return feature_set

    def _load_data(self):
        """Load and merge all data sources into a single DataFrame."""
        # Get date range from definition
        start_date = self.definition.get('start_date')
        end_date = self.definition.get('end_date')
        
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        # Load sales data
        sales_qs = Sales.objects.all()
        if start_date:
            sales_qs = sales_qs.filter(date__gte=start_date)
        if end_date:
            sales_qs = sales_qs.filter(date__lte=end_date)
            
        sales_data = list(sales_qs.values('date', 'value', 'sector_id'))
        self.df = pd.DataFrame(sales_data)
        
        if self.df.empty:
            raise ValueError("No sales data found for the specified date range")
        
        # Convert date to datetime
        self.df['date'] = pd.to_datetime(self.df['date'])
        self.df['value'] = self.df['value'].astype(float)
        
        # Sort by date
        self.df = self.df.sort_values('date').reset_index(drop=True)
        
        # Add sector information
        if 'sector_ids' in self.definition:
            sector_ids = self.definition['sector_ids']
            self.df = self.df[self.df['sector_id'].isin(sector_ids)]
        
        # Create monthly aggregation if needed
        self.df = self.df.groupby(['date', 'sector_id'])['value'].sum().reset_index()
        
        # Create complete date range
        date_range = pd.date_range(start=self.df['date'].min(), 
                                 end=self.df['date'].max(), 
                                 freq='M')
        
        # Create sector list
        sectors = self.df['sector_id'].unique()
        
        # Create complete grid
        date_sector_grid = []
        for date in date_range:
            for sector in sectors:
                date_sector_grid.append({'date': date, 'sector_id': sector})
        
        grid_df = pd.DataFrame(date_sector_grid)
        
        # Merge with actual data
        self.df = grid_df.merge(self.df, on=['date', 'sector_id'], how='left')
        self.df['value'] = self.df['value'].fillna(0)
        
        # Sort by date and sector
        self.df = self.df.sort_values(['sector_id', 'date']).reset_index(drop=True)

    def _generate_time_features(self):
        """Generate time-based features."""
        self.df['year'] = self.df['date'].dt.year
        self.df['month'] = self.df['date'].dt.month
        self.df['quarter'] = self.df['date'].dt.quarter
        self.df['month_sin'] = np.sin(2 * np.pi * self.df['month'] / 12)
        self.df['month_cos'] = np.cos(2 * np.pi * self.df['month'] / 12)

    def _generate_lag_features(self):
        """Generate lag features (1, 3, 6, 12 months)."""
        for lag in [1, 3, 6, 12]:
            self.df[f'sales_lag_{lag}'] = self.df.groupby('sector_id')['value'].shift(lag)

    def _generate_rolling_features(self):
        """Generate rolling average features."""
        for window in [3, 6, 12]:
            self.df[f'sales_rolling_mean_{window}'] = (
                self.df.groupby('sector_id')['value']
                .rolling(window=window, min_periods=1)
                .mean()
                .reset_index(0, drop=True)
            )
            
            self.df[f'sales_rolling_std_{window}'] = (
                self.df.groupby('sector_id')['value']
                .rolling(window=window, min_periods=1)
                .std()
                .reset_index(0, drop=True)
            )
            
            # Rolling coefficient of variation
            self.df[f'sales_cv_{window}'] = (
                self.df[f'sales_rolling_std_{window}'] / 
                self.df[f'sales_rolling_mean_{window}']
            ).fillna(0)

    def _generate_policy_features(self):
        """Generate policy impact features."""
        if 'policy_ids' not in self.definition:
            return
            
        policy_ids = self.definition['policy_ids']
        policies = Policy.objects.filter(id__in=policy_ids)
        
        for policy in policies:
            policy_start = policy.start_date
            policy_end = policy.end_date if policy.end_date else datetime.max.date()
            
            # Binary indicator for policy active
            self.df[f'policy_{policy.id}_active'] = (
                (self.df['date'].dt.date >= policy_start) & 
                (self.df['date'].dt.date <= policy_end)
            ).astype(int)
            
            # Policy duration (months since start)
            self.df[f'policy_{policy.id}_duration'] = (
                (self.df['date'].dt.to_period('M').astype(int) - 
                 pd.Period(policy_start, freq='M').astype(int))
            ).clip(lower=0)

    def _generate_sector_features(self):
        """Generate sector-specific features."""
        sectors = Sector.objects.all()
        sector_map = {s.id: s.name for s in sectors}
        
        # Sector dummy variables
        for sector_id in self.df['sector_id'].unique():
            self.df[f'sector_{sector_id}'] = (self.df['sector_id'] == sector_id).astype(int)
        
        # Sector growth rate (year-over-year)
        self.df['sector_growth_yoy'] = (
            self.df.groupby('sector_id')['value']
            .pct_change(periods=12)
            .fillna(0)
        )

    def _generate_interaction_features(self):
        """Generate interaction features."""
        # Time * Policy interactions
        if 'policy_ids' in self.definition:
            for policy_id in self.definition['policy_ids']:
                if f'policy_{policy_id}_active' in self.df.columns:
                    self.df[f'time_policy_{policy_id}'] = (
                        self.df['date'].dt.to_period('M').astype(int) * 
                        self.df[f'policy_{policy_id}_active']
                    )

    def _generate_target_variable(self):
        """Generate target variable (1-month ahead sales)."""
        self.df['sales_target'] = self.df.groupby('sector_id')['value'].shift(-1)
        
        # Remove rows with NaN targets (last observation for each sector)
        self.df = self.df.dropna(subset=['sales_target'])


