from datetime import date, timedelta
from typing import Optional

from django.db import transaction
from django.http import HttpRequest

from apps.audit.services import log_audit_event
from apps.indicators.models import Indicator
from apps.policies.models import PolicyParameter
from apps.sectors.models import Sector
from apps.system.models import DataSnapshot

from ..models import MLDataset, MLDatasetRow
from .data_joiner import (
    get_daily_sales,
    get_indicator_value,
    get_input_cost_value,
    get_policy_parameter_value,
)
from apps.costs.models import InputCost


@transaction.atomic
def build_ml_dataset(
    *,
    snapshot: DataSnapshot,
    sector: Sector,
    start_date: date,
    end_date: date,
    created_by,
    request: Optional[HttpRequest] = None,
    inflation_indicator: Optional[Indicator] = None,
    fuel_cost_input: Optional[InputCost] = None,
    tax_parameter: Optional[PolicyParameter] = None,
) -> MLDataset:
    """
    Build an ML-ready dataset by joining:
    - sales
    - macro indicators
    - policy parameters
    - input costs

    This function is intentionally generic and does not implement any ML logic.
    """
    dataset = MLDataset.objects.create(
        snapshot=snapshot,
        sector=sector,
        start_date=start_date,
        end_date=end_date,
        created_by=created_by,
    )

    current = start_date
    while current <= end_date:
        sales_info = get_daily_sales(sector=sector, day=current)
        inflation_value = (
            get_indicator_value(inflation_indicator, current)
            if inflation_indicator
            else None
        )
        fuel_cost_value = (
            get_input_cost_value(fuel_cost_input, current)
            if fuel_cost_input
            else None
        )
        tax_rate_value = (
            get_policy_parameter_value(
                tax_parameter, financial_year=str(current.year)
            )
            if tax_parameter
            else None
        )

        MLDatasetRow.objects.create(
            dataset=dataset,
            date=current,
            sales=sales_info.get("sales"),
            price=sales_info.get("price"),
            inflation=inflation_value,
            fuel_cost=fuel_cost_value,
            tax_rate=tax_rate_value,
            other_features={},
        )
        current += timedelta(days=1)

    log_audit_event(
        actor=created_by,
        action="ml.dataset.materialized",
        entity_type="MLDataset",
        entity_id=dataset.pk,
        request=request,
        metadata={
            "snapshot_id": str(snapshot.pk),
            "sector_code": sector.code,
            "start_date": str(start_date),
            "end_date": str(end_date),
        },
    )

    return dataset

