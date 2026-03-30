import requests
from typing import Dict, Any, Optional
from .models import ExternalSource, ExternalIndicator, ExternalIndicatorValue
from django.utils import timezone
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def fetch_world_bank_indicator(source: ExternalSource, indicator_code: str, country_code: str = "KEN", start: Optional[int] = None, end: Optional[int] = None) -> Dict[str, Any]:
    """Fetch time series from World Bank API for a given indicator and country.

    This is a minimal example; callers should handle paging and errors as needed.
    """
    base = source.base_url or "http://api.worldbank.org/v2"
    params = {"format": "json", "per_page": 1000}
    if start:
        params["date"] = f"{start}:{end or ''}"
    url = f"{base}/country/{country_code}/indicator/{indicator_code}"
    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


def ingest_world_bank_indicator(source_name: str, indicator_code: str, country_code: str = "KEN") -> int:
    """High-level ingest: ensure source/indicator exist and save values.

    Returns number of values saved.
    """
    source, _ = ExternalSource.objects.get_or_create(name=source_name, defaults={"base_url": "http://api.worldbank.org/v2"})
    indicator, _ = ExternalIndicator.objects.get_or_create(source=source, code=indicator_code)

    payload = fetch_world_bank_indicator(source=source, indicator_code=indicator_code, country_code=country_code)
    saved = 0
    # World Bank returns [metadata, data]
    if isinstance(payload, list) and len(payload) >= 2:
        for item in payload[1]:
            date = item.get("date")
            value = item.get("value")
            raw = item
            if date is None:
                continue
            # save or update
            obj, created = ExternalIndicatorValue.objects.update_or_create(
                indicator=indicator,
                date=date,
                defaults={"value": value, "raw_payload": raw, "retrieved_at": timezone.now()},
            )
            if created:
                saved += 1
    return saved


def fetch_generic_api(url: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    resp = requests.get(url, params=params or {}, timeout=30)
    resp.raise_for_status()
    return resp.json()


def ingest_central_bank_rates(source_name: str, rates_endpoint: str, mapping: Dict[str, str] = None) -> int:
    """Ingest exchange rates or macro series from a central bank's API.

    mapping is an optional dict to map provider keys to our model fields.
    This function expects the endpoint to return JSON with date/value pairs.
    """
    source, _ = ExternalSource.objects.get_or_create(name=source_name, defaults={"base_url": rates_endpoint})
    payload = fetch_generic_api(rates_endpoint)
    saved = 0

    # Very generic handling: look for time series in common locations
    timeseries = None
    if isinstance(payload, dict):
        # common patterns
        for candidate in ("rates", "data", "series", "observations", "results"):
            if candidate in payload:
                timeseries = payload[candidate]
                break
        # if none matched, maybe payload itself is the series
        if timeseries is None:
            timeseries = payload

    if not timeseries:
        logger.warning("No timeseries found for central bank endpoint %s", rates_endpoint)
        return 0

    # create a single indicator representing this endpoint
    indicator, _ = ExternalIndicator.objects.get_or_create(source=source, code=rates_endpoint)

    # timeseries may be dict(date->value) or list of records
    if isinstance(timeseries, dict):
        items = timeseries.items()
    elif isinstance(timeseries, list):
        items = []
        for rec in timeseries:
            # try to extract date and value
            date = rec.get("date") or rec.get("obsDate") or rec.get("d")
            value = rec.get("value") or rec.get("rate") or rec.get("v")
            if date is None:
                continue
            items.append((date, value))
    else:
        items = []

    for date, value in items:
        try:
            # normalize date
            if isinstance(date, str):
                # try common formats
                try:
                    dt = datetime.fromisoformat(date)
                    date_obj = dt.date()
                except Exception:
                    # fallback: if only year-month
                    parts = date.split("-")
                    date_obj = datetime(int(parts[0]), int(parts[1]) if len(parts) > 1 else 1, 1).date()
            else:
                date_obj = date

            obj, created = ExternalIndicatorValue.objects.update_or_create(
                indicator=indicator,
                date=date_obj,
                defaults={"value": value, "raw_payload": {"source_item": date, "value": value}, "retrieved_at": timezone.now()},
            )
            if created:
                saved += 1
        except Exception:
            logger.exception("Failed to save central bank item: %s", date)

    return saved


def ingest_alpha_vantage_series(source_name: str, symbol: str, api_key: str, function: str = "TIME_SERIES_DAILY_ADJUSTED") -> int:
    """Ingest equity/time series from Alpha Vantage (requires API key).

    Minimal example; users should supply an API key in env or settings.
    """
    base = "https://www.alphavantage.co/query"
    params = {"function": function, "symbol": symbol, "apikey": api_key, "outputsize": "compact"}
    payload = fetch_generic_api(base, params=params)
    # Alpha Vantage nests series under a named key
    timeseries = None
    for k in payload.keys():
        if "Time Series" in k or "Time Series" in k:
            timeseries = payload[k]
            break
    if timeseries is None:
        # try common key
        timeseries = payload.get("Time Series (Daily)") or payload.get("time_series")

    source, _ = ExternalSource.objects.get_or_create(name=source_name, defaults={"base_url": base})
    indicator, _ = ExternalIndicator.objects.get_or_create(source=source, code=f"ALPHA:{symbol}")
    saved = 0
    if isinstance(timeseries, dict):
        for date, vals in timeseries.items():
            try:
                value = vals.get("4. close") or vals.get("close")
                obj, created = ExternalIndicatorValue.objects.update_or_create(
                    indicator=indicator,
                    date=date,
                    defaults={"value": value, "raw_payload": vals, "retrieved_at": timezone.now()},
                )
                if created:
                    saved += 1
            except Exception:
                logger.exception("AlphaVantage save error for %s %s", symbol, date)
    return saved


def ingest_government_open_data(source_name: str, endpoint: str, date_key: str = "date", value_key: str = "value") -> int:
    """Generic ingestion for government open data APIs that return lists of records."""
    source, _ = ExternalSource.objects.get_or_create(name=source_name, defaults={"base_url": endpoint})
    payload = fetch_generic_api(endpoint)
    saved = 0
    indicator, _ = ExternalIndicator.objects.get_or_create(source=source, code=endpoint)
    records = payload if isinstance(payload, list) else payload.get("data") or payload.get("results") or []
    for rec in records:
        try:
            date = rec.get(date_key)
            value = rec.get(value_key)
            if not date:
                continue
            obj, created = ExternalIndicatorValue.objects.update_or_create(
                indicator=indicator,
                date=date,
                defaults={"value": value, "raw_payload": rec, "retrieved_at": timezone.now()},
            )
            if created:
                saved += 1
        except Exception:
            logger.exception("Gov data save error for %s", endpoint)
    return saved


def map_external_to_internal(source_name: str, external_code: str, version_label: str = None) -> int:
    """Map external indicator values into internal `Indicator` and create an `IndicatorVersion`.

    Returns number of IndicatorValue rows created.
    """
    from .models import ProviderMapping
    from apps.indicators.models import Indicator, IndicatorVersion, IndicatorValue

    try:
        source = ExternalSource.objects.get(name=source_name)
    except ExternalSource.DoesNotExist:
        logger.warning("Source %s not found for mapping", source_name)
        return 0

    try:
        mapping = ProviderMapping.objects.get(source=source, external_code=external_code, is_active=True)
    except ProviderMapping.DoesNotExist:
        logger.warning("No active mapping for %s:%s", source_name, external_code)
        return 0

    # Ensure target indicator exists
    if mapping.target_indicator:
        indicator = mapping.target_indicator
    else:
        # mapping not linked to an internal indicator; skip until mapping is configured
        logger.warning("Mapping %s:%s has no target_indicator configured; skipping.", source_name, external_code)
        return 0

    # create an IndicatorVersion
    version_label = version_label or f"ingest-{source.name}-{datetime.utcnow().isoformat()}"
    iv = IndicatorVersion.objects.create(indicator=indicator, version_label=version_label, source=source_name, payload_metadata={})

    # find external indicator
    try:
        ext_ind = ExternalIndicator.objects.get(source=source, code=external_code)
    except ExternalIndicator.DoesNotExist:
        logger.warning("ExternalIndicator %s not found", external_code)
        return 0

    saved = 0
    for val in ext_ind.values.all():
        try:
            # convert value to float where possible
            v = val.value
            date = val.date
            if v is None:
                continue
            obj, created = IndicatorValue.objects.update_or_create(
                indicator=indicator,
                date=date,
                defaults={"value": float(v), "version": iv.version_label},
            )
            if created:
                saved += 1
        except Exception:
            logger.exception("Failed mapping value %s for %s", val, external_code)

    # estimate quality score
    try:
        iv.quality_score = 1.0 if saved > 0 else 0.0
        iv.payload_metadata = {"mapped_rows": saved}
        iv.save()
    except Exception:
        logger.exception("Failed updating IndicatorVersion %s", iv)

    return saved


def get_external_indicator_features(sector_id: int, date=None) -> dict:
    """Return proxy features from external indicators for a sector.

    Lightweight adapter used by intelligence.feature_builder; returns
    empty dict if no external indicators mapped to the sector.
    """
    try:
        # attempt to find ExternalIndicatorValues mapped into internal indicators
        from apps.externalindicator.models import ExternalIndicatorValue
        vals = ExternalIndicatorValue.objects.all().order_by('-date')[:30]
        if not vals:
            return {}
        latest = vals[0].value
        return {'ext_indicator_latest': float(latest)}
    except Exception:
        return {}
