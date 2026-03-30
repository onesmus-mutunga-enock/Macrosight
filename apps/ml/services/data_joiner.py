from datetime import date
from typing import Optional

from django.db.models import Sum, F

from apps.costs.models import InputCost, InputCostValue
from apps.indicators.models import Indicator, IndicatorValue
from apps.policies.models import PolicyParameter, PolicyParameterValue
from apps.sales.models import Sale
from apps.sectors.models import Sector


def get_daily_sales(sector: Sector, day: date) -> dict:
    """
    Aggregate sales for a given sector and day.
    Returns total units_sold, total revenue, and average price.
    """
    qs = Sale.objects.filter(sector=sector, date=day)
    aggregated = qs.aggregate(
        total_units=Sum("units_sold"),
        total_revenue=Sum("revenue"),
    )
    total_units = aggregated["total_units"] or 0
    total_revenue = aggregated["total_revenue"] or 0
    avg_price: Optional[float] = None
    if total_units:
        avg_price = float(total_revenue) / float(total_units)

    return {
        "sales": float(total_units) if total_units is not None else None,
        "price": avg_price,
    }


def get_indicator_value(indicator: Indicator, day: date) -> Optional[float]:
    """
    Return the indicator value for a given date, if present.
    """
    try:
        record = IndicatorValue.objects.get(indicator=indicator, date=day)
        return float(record.value)
    except IndicatorValue.DoesNotExist:
        return None


def get_policy_parameter_value(
    parameter: PolicyParameter, financial_year: str
) -> Optional[float]:
    """
    Return the policy parameter value for the given financial year, if present.
    """
    try:
        record = PolicyParameterValue.objects.get(
            parameter=parameter, financial_year=financial_year
        )
        return float(record.value)
    except PolicyParameterValue.DoesNotExist:
        return None


def get_input_cost_value(cost: InputCost, day: date) -> Optional[float]:
    """
    Return the input cost value for a given date, if present.
    """
    try:
        record = InputCostValue.objects.get(cost=cost, date=day)
        return float(record.value)
    except InputCostValue.DoesNotExist:
        return None

