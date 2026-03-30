from typing import Dict
from django.db.models import Sum, Avg
from apps.sales.models import Sale
from apps.forecasts.models import Forecast
# add more

class DashboardService:
    @staticmethod
    def get_executive_data():
        # Aggregate national sales, forecasts summary, cost pressure, policy impacts
        total_revenue = Sale.objects.aggregate(Sum('revenue'))['revenue__sum'] or 0
        avg_forecast_accuracy = Forecast.objects.aggregate(Avg('accuracy'))['accuracy__avg'] or 0
        return {
            'total_revenue': total_revenue,
            'forecast_accuracy': avg_forecast_accuracy,
            # more KPIs
        }

    @staticmethod
    def get_analyst_data():
        # Detailed sector breakdowns, recent forecasts, indicators
        return {}

    @staticmethod
    def get_audit_data():
        # Audit logs summary, data quality scores
        return {}

    @staticmethod
    def get_data_feeder_data():
        # Pending uploads, validation errors
        return {}

