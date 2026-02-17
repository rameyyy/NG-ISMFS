import json
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Iterable

import pandas as pd
from django.conf import settings

from .models import MeanData_class, NcData
from .request_cache import get_or_compute_cached_json


DEFAULT_START_DATE = date(1999, 1, 4)
DEFAULT_END_DATE = date(2021, 12, 27)


@dataclass
class _MockRequest:
    body: bytes


def run_precompute(
    endpoint: str,
    points_csv: str | None,
    start_date: str | None,
    end_date: str | None,
    shard_count: int = 1,
    shard_index: int = 0,
) -> dict:
    if shard_count < 1:
        raise ValueError("shard_count must be >= 1")
    if shard_index < 0 or shard_index >= shard_count:
        raise ValueError("shard_index must be in [0, shard_count)")

    points = _load_points(points_csv)
    start_dt = _parse_date(start_date, DEFAULT_START_DATE)
    end_dt = _parse_date(end_date, DEFAULT_END_DATE)

    cache_file_override = _cache_file_name_for_shard(endpoint, shard_count, shard_index)
    total = 0
    global_index = 0
    for week_start in _iter_week_starts(start_dt, end_dt):
        display_date = week_start.isoformat()
        for lat, lon in points:
            if global_index % shard_count == shard_index:
                _run_single(
                    endpoint=endpoint,
                    display_date=display_date,
                    lat=lat,
                    lon=lon,
                    cache_file_override=cache_file_override,
                )
                total += 1
            global_index += 1
    return {
        "endpoint": endpoint,
        "rows_processed": total,
        "points_count": len(points),
        "shard_count": shard_count,
        "shard_index": shard_index,
        "cache_file": cache_file_override,
    }


def _run_single(
    endpoint: str,
    display_date: str,
    lat: float,
    lon: float,
    cache_file_override: str | None = None,
):
    payload = {
        "Model": 1,
        "lat": lat,
        "lon": lon,
        "soilLevel": "",
        "DayCount": "",
        "SiteName": "Precompute",
        "Display_Date": display_date,
        "Display_End_Date": (datetime.fromisoformat(display_date) + timedelta(days=46)).date().isoformat(),
        "YearCount": "",
    }
    request = _MockRequest(body=json.dumps(payload).encode("utf-8"))

    if endpoint == "nc":
        get_or_compute_cached_json(
            endpoint="nc",
            request=request,
            compute_fn=lambda: NcData().nc_read_fun(request),
            cache_file_override=cache_file_override,
        )
    elif endpoint == "mean":
        get_or_compute_cached_json(
            endpoint="mean",
            request=request,
            compute_fn=lambda: MeanData_class().MeanData_read_fun(request),
            cache_file_override=cache_file_override,
        )
    else:
        raise ValueError(f"Unsupported endpoint: {endpoint}")


def _load_points(points_csv: str | None) -> list[tuple[float, float]]:
    if points_csv:
        csv_path = Path(points_csv)
        if not csv_path.is_absolute():
            csv_path = Path(settings.BASE_DIR) / csv_path
        df = pd.read_csv(csv_path)
        if "lat" not in df.columns or "lon" not in df.columns:
            raise ValueError("points CSV must have 'lat' and 'lon' columns")
        return [(float(row["lat"]), float(row["lon"])) for _, row in df.iterrows()]

    # Default to known NEON points that this app already supports in frontend mapping.
    return [
        (45.762, -122.33),   # ABBY
        (39.060, -78.072),   # BLAN
        (33.401, -97.180),   # CLBJ
        (32.950, -87.393),   # TALL
        (47.128, -99.241),   # WOOD
        (45.820, -121.952),  # WREF
        (37.108, -119.732),  # SJER
        (40.180, -112.000),  # ONAQ
        (31.910, -110.840),  # SRER
        (40.055, -105.582),  # NIWO
        (40.815, -104.744),  # CPER
        (39.100, -96.560),   # KONZ
        (46.233, -89.537),   # UNDE
        (35.964, -84.282),   # ORNL
        (29.690, -81.993),   # OSBS
        (38.892, -78.140),   # SCBI
        (42.537, -72.172),   # HARV
    ]


def _iter_week_starts(start_dt: date, end_dt: date) -> Iterable[date]:
    cursor = start_dt
    while cursor <= end_dt:
        yield cursor
        cursor = cursor + timedelta(days=7)


def _parse_date(date_str: str | None, default: date) -> date:
    if not date_str:
        return default
    return datetime.fromisoformat(date_str).date()


def _cache_file_name_for_shard(endpoint: str, shard_count: int, shard_index: int) -> str:
    base_name = f"{endpoint}_endpoint_cache.parquet"
    if shard_count == 1:
        return base_name
    return f"{endpoint}_endpoint_cache.shard-{shard_index}-of-{shard_count}.parquet"
