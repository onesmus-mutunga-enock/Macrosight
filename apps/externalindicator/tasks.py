from celery import shared_task
from django.conf import settings
from .services import (
    ingest_world_bank_indicator,
    ingest_central_bank_rates,
    ingest_alpha_vantage_series,
    ingest_government_open_data,
    map_external_to_internal,
)


@shared_task
def task_ingest_world_bank(indicator_code: str, country_code: str = "KEN"):
    # source name can be parameterized; using World Bank label
    return ingest_world_bank_indicator("World Bank", indicator_code, country_code)


@shared_task
def task_ingest_central_bank(source_name: str, endpoint: str):
    return ingest_central_bank_rates(source_name, endpoint)


@shared_task
def task_ingest_alpha_vantage(source_name: str, symbol: str, api_key: str = None):
    # api_key can be provided or read from settings
    key = api_key or getattr(settings, "ALPHAVANTAGE_API_KEY", None)
    if not key:
        raise RuntimeError("AlphaVantage API key not provided")
    return ingest_alpha_vantage_series(source_name, symbol, key)


@shared_task
def task_ingest_gov_open_data(source_name: str, endpoint: str, date_key: str = "date", value_key: str = "value"):
    return ingest_government_open_data(source_name, endpoint, date_key=date_key, value_key=value_key)


@shared_task
def task_map_external_to_internal(source_name: str, external_code: str, version_label: str = None):
    return map_external_to_internal(source_name, external_code, version_label=version_label)
