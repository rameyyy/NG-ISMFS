import json
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable

import pandas as pd
from django.conf import settings


CACHE_SCHEMA_VERSION = "v1"
_CACHE_LOCK = threading.Lock()
_PARQUET_AVAILABLE = True
_PARQUET_IMPORT_ERROR = None

try:
    # Validate that at least one parquet engine is available.
    pd.io.parquet.get_engine("auto")
except Exception as exc:
    _PARQUET_AVAILABLE = False
    _PARQUET_IMPORT_ERROR = str(exc)

_CACHE_COLUMNS = [
    "cache_key",
    "cache_type",
    "schema_version",
    "week_start",
    "display_date",
    "lat",
    "lon",
    "source_signature",
    "payload_json",
    "updated_at_utc",
]

_ENDPOINT_TO_PARQUET = {
    "nc": "nc_endpoint_cache.parquet",
    "mean": "mean_endpoint_cache.parquet",
}

_ENDPOINT_SOURCE_PATHS = {
    "nc": [
        "Nc_data/CAM6_SM_0_5m_0_45_leadday_1999_2021_organize_Ens_mean_normalized.nc",
        "ERA5/ERA5_SM_0_5m_0_45_leadday_1999_2021_organize_normalized.nc",
        "Best_Model",
    ],
    "mean": [
        "Nc_data/CAM6_SM_0_5m_0_45_leadday_1999_2021_organize_Ens_mean_normalized.nc",
        "ERA5/ERA5_SM_0_5m_0_45_leadday_1999_2021_organize_normalized.nc",
        "Best_Model",
    ],
}


def get_or_compute_cached_json(
    endpoint: str,
    request,
    compute_fn: Callable[[], str],
    cache_file_override: str | None = None,
) -> str:
    if endpoint not in _ENDPOINT_TO_PARQUET:
        return compute_fn()

    try:
        body_unicode = request.body.decode("utf-8")
        body = json.loads(body_unicode)
    except Exception:
        return compute_fn()

    cache_key, week_start, display_date, lat, lon = _build_cache_identity(endpoint, body)
    source_signature = _build_source_signature(_ENDPOINT_SOURCE_PATHS[endpoint])
    cache_file = _cache_file_for_endpoint(endpoint, cache_file_override=cache_file_override)

    with _CACHE_LOCK:
        cached_payload = _read_cache_hit(
            cache_file=cache_file,
            cache_key=cache_key,
            source_signature=source_signature,
            request_week_start=week_start,
            request_lat=lat,
            request_lon=lon,
        )
        if cached_payload is not None:
            print(f"[CACHE HIT] endpoint={endpoint} key={cache_key} file={cache_file.name}")
            return cached_payload

    payload_json = compute_fn()

    with _CACHE_LOCK:
        _upsert_cache_row(
            cache_file=cache_file,
            cache_key=cache_key,
            endpoint=endpoint,
            week_start=week_start,
            display_date=display_date,
            lat=lat,
            lon=lon,
            source_signature=source_signature,
            payload_json=payload_json,
        )
    return payload_json


def _cache_dir() -> Path:
    path = Path(settings.BASE_DIR) / "cache"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _cache_file_for_endpoint(endpoint: str, cache_file_override: str | None = None) -> Path:
    if cache_file_override:
        file_name = cache_file_override
    else:
        file_name = _ENDPOINT_TO_PARQUET[endpoint]

    if _PARQUET_AVAILABLE:
        return _cache_dir() / file_name
    return _cache_dir() / file_name.replace(".parquet", ".pkl")


def _build_cache_identity(endpoint: str, body: dict):
    lat = _safe_float(body.get("lat"), 0.0)
    lon = _safe_float(body.get("lon"), 0.0)
    display_date = str(body.get("Display_Date", "1999-01-04"))
    week_start = _week_start_for_display_date(display_date)
    cache_key = f"{endpoint}|{week_start}|{lat:.4f}|{lon:.4f}"
    return cache_key, week_start, display_date, lat, lon


def _week_start_for_display_date(display_date: str) -> str:
    try:
        input_date = pd.to_datetime(display_date).to_pydatetime()
    except Exception:
        input_date = datetime(1999, 1, 4)
    start_date = datetime(1999, 1, 4)
    week_number = (input_date - start_date).days // 7
    monday_date = start_date + timedelta(days=week_number * 7)
    return monday_date.strftime("%Y-%m-%d")


def _safe_float(value, default: float) -> float:
    try:
        return float(value)
    except Exception:
        return default


def _build_source_signature(relative_paths: list[str]) -> str:
    parts = []
    for rel in relative_paths:
        abs_path = Path(settings.BASE_DIR) / rel
        if not abs_path.exists():
            parts.append(f"{rel}:missing")
            continue
        stat = abs_path.stat()
        parts.append(f"{rel}:{stat.st_mtime_ns}:{stat.st_size}")
    return "|".join(parts)


def _read_cache_hit(
    cache_file: Path,
    cache_key: str,
    source_signature: str,
    request_week_start: str,
    request_lat: float,
    request_lon: float,
):
    if not cache_file.exists():
        return None
    try:
        cache_df = _read_cache_df(cache_file)
    except Exception:
        return None

    if cache_df.empty:
        return None

    cache_hit = cache_df[
        (cache_df["cache_key"] == cache_key)
        & (cache_df["source_signature"] == source_signature)
        & (cache_df["schema_version"] == CACHE_SCHEMA_VERSION)
    ]
    if cache_hit.empty:
        # Fallback lookup: same week + compatible source, pick nearest cached lat/lon.
        # This allows cache reuse when user click coordinates differ slightly from
        # precomputed point coordinates.
        try:
            candidate_df = cache_df[
                (cache_df["source_signature"] == source_signature)
                & (cache_df["schema_version"] == CACHE_SCHEMA_VERSION)
                & (cache_df["week_start"] == request_week_start)
            ].copy()
            if candidate_df.empty:
                return None

            candidate_df["dist_sq"] = (
                (candidate_df["lat"].astype(float) - float(request_lat)) ** 2
                + (candidate_df["lon"].astype(float) - float(request_lon)) ** 2
            )
            nearest_row = candidate_df.sort_values(by="dist_sq").iloc[0]

            # Guardrail to avoid selecting very far cached coordinates.
            if float(nearest_row["dist_sq"]) > 4.0:  # distance > 2 degrees
                return None

            return nearest_row["payload_json"]
        except Exception:
            return None
    return cache_hit.iloc[-1]["payload_json"]


def _upsert_cache_row(
    cache_file: Path,
    cache_key: str,
    endpoint: str,
    week_start: str,
    display_date: str,
    lat: float,
    lon: float,
    source_signature: str,
    payload_json: str,
):
    if cache_file.exists():
        try:
            cache_df = _read_cache_df(cache_file)
        except Exception:
            cache_df = pd.DataFrame(columns=_CACHE_COLUMNS)
    else:
        cache_df = pd.DataFrame(columns=_CACHE_COLUMNS)

    cache_df = cache_df[cache_df["cache_key"] != cache_key] if not cache_df.empty else cache_df

    new_row = pd.DataFrame(
        [
            {
                "cache_key": cache_key,
                "cache_type": endpoint,
                "schema_version": CACHE_SCHEMA_VERSION,
                "week_start": week_start,
                "display_date": display_date,
                "lat": lat,
                "lon": lon,
                "source_signature": source_signature,
                "payload_json": payload_json,
                "updated_at_utc": datetime.utcnow().isoformat(),
            }
        ]
    )
    cache_df = pd.concat([cache_df, new_row], ignore_index=True)
    _write_cache_df(cache_df, cache_file)


def _read_cache_df(cache_file: Path) -> pd.DataFrame:
    if cache_file.suffix == ".parquet":
        return pd.read_parquet(cache_file)
    return pd.read_pickle(cache_file)


def _write_cache_df(cache_df: pd.DataFrame, cache_file: Path):
    if cache_file.suffix == ".parquet":
        cache_df.to_parquet(cache_file, index=False)
    else:
        cache_df.to_pickle(cache_file)


def merge_cache_shards(endpoint: str) -> tuple[int, int]:
    """
    Merge files like `nc_endpoint_cache.shard-*.parquet` into `nc_endpoint_cache.parquet`.
    Returns (shard_file_count, merged_row_count).
    """
    if endpoint not in _ENDPOINT_TO_PARQUET:
        raise ValueError(f"Unsupported endpoint: {endpoint}")

    cache_root = _cache_dir()
    main_name = _ENDPOINT_TO_PARQUET[endpoint]
    if not _PARQUET_AVAILABLE:
        main_name = main_name.replace(".parquet", ".pkl")

    shard_glob = main_name.replace(".parquet", ".shard-*.parquet").replace(".pkl", ".shard-*.pkl")
    shard_files = sorted(cache_root.glob(shard_glob))
    if not shard_files:
        return 0, 0

    frames = []
    for shard in shard_files:
        try:
            frames.append(_read_cache_df(shard))
        except Exception:
            continue

    if not frames:
        return len(shard_files), 0

    merged = pd.concat(frames, ignore_index=True)
    merged = merged.sort_values(by=["cache_key", "updated_at_utc"]).drop_duplicates(
        subset=["cache_key", "source_signature", "schema_version"], keep="last"
    )
    main_file = cache_root / main_name
    _write_cache_df(merged, main_file)
    return len(shard_files), len(merged)
