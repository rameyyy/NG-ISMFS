# Cache Performance: Hit vs Miss

This document shows the difference between cache hits and cache misses in the Django backend.

## What is a Cache Hit?

A **cache hit** means the forecast data was found in the Parquet cache file and returned immediately without recomputing.

A **cache miss** means the data wasn't cached, so the model had to:
1. Load NetCDF files from disk
2. Run model predictions
3. Process and format the results
4. Save to cache for next time

## Console Output Examples

### Cache Hit (Fast)

```
[CACHE HIT] endpoint=nc key=nc|2020-01-06|45.7620|-122.3300 file=nc_endpoint_cache.parquet
[26/Feb/2026 17:30:15] "POST /getNcData/ HTTP/1.1" 200 5708
```

**Characteristics:**
- Shows `[CACHE HIT]` message
- Includes cache key and filename
- Response code: 200 (success)
- Response size: ~5-6KB JSON

### Cache Miss (Slow)

```
2026-02-26 17:30:45.123456: I tensorflow/core/util/port.cc:113] oneDNN custom operations are on...
[26/Feb/2026 17:31:02] "POST /getNcData/ HTTP/1.1" 200 5708
```

**Characteristics:**
- **No** `[CACHE HIT]` message
- Shows TensorFlow loading messages
- Takes 10-20 seconds to respond
- Same response size once complete

## Performance Comparison

### NC Endpoint (`/getNcData/`)

| Scenario | Response Time | Console Output | Notes |
|----------|--------------|----------------|-------|
| **Cache Hit** | 50-200ms | `[CACHE HIT]` message | Reads Parquet file |
| **Cache Miss** | 10-20 seconds | TensorFlow messages | Loads NetCDF + runs model |
| **First Request** | 15-25 seconds | Model loading + TF init | Loads models into memory |

### Mean Endpoint (`/getMeanData/`)

| Scenario | Response Time | Console Output | Notes |
|----------|--------------|----------------|-------|
| **Cache Hit** | 30-100ms | `[CACHE HIT]` message | Reads Parquet file |
| **Cache Miss** | 8-15 seconds | TensorFlow messages | Loads data + computes stats |

## How to Test Cache Performance

### 1. Test Cache Hit

**Prerequisites:** Cache must be built first
```powershell
.\Back_end\venvi\Scripts\python.exe .\Back_end\manage.py build_parquet_cache --endpoint nc --start-date 2020-01-06 --end-date 2020-01-13
```

**Test:**
1. Start backend: `cd Back_end && .\venvi\Scripts\python.exe .\manage.py runserver`
2. Open frontend: http://localhost:4200
3. Click on a cached location (e.g., ABBY: lat=45.762, lon=-122.33)
4. Select date: 2020-01-06
5. Check backend console for `[CACHE HIT]` message

**Expected:** Response in <200ms

### 2. Test Cache Miss

**Test:**
1. Click on a location that's NOT cached
2. Select a date that's NOT cached
3. Watch backend console - no `[CACHE HIT]` message
4. Wait 10-20 seconds for response

**Expected:** Response in 10-20 seconds, then cached for next time

### 3. Test Nearest-Point Fallback

The cache has a "nearest point" fallback feature. If you click slightly off from a cached coordinate, it will use the nearest cached point (within 2 degrees).

**Test:**
1. Build cache for ABBY: lat=45.762, lon=-122.33
2. Click nearby: lat=45.8, lon=-122.4 (within 2 degrees)
3. Should still get a cache hit with the ABBY data

**Expected:** `[CACHE HIT]` message with nearest cached point

## Timing Breakdown (Cache Miss)

For a typical uncached request to `/getNcData/`:

| Step | Time | Description |
|------|------|-------------|
| **Load NetCDF files** | 2-3s | Open CAM6 and ERA5 datasets |
| **Load TensorFlow models** | 3-5s | First request only |
| **Extract data** | 1-2s | Select lat/lon/date slice |
| **Run model predictions** | 3-5s | Execute trained model |
| **Format response** | 0.5-1s | Convert to JSON |
| **Save to cache** | 0.2-0.5s | Write Parquet row |
| **Total** | **10-20s** | First request |
| **Subsequent uncached** | **5-10s** | Models already loaded |

## Cache File Statistics

Current cache files (as of last merge):

```
Back_end/cache/nc_endpoint_cache.parquet      758 KB
Back_end/cache/mean_endpoint_cache.parquet     12 KB
```

## How to Monitor Cache Usage

### Real-time Console Monitoring

Watch for `[CACHE HIT]` messages:
```powershell
# Backend terminal will show:
[CACHE HIT] endpoint=nc key=nc|2020-01-06|45.7620|-122.3300 file=nc_endpoint_cache.parquet
```

### Check Cache Coverage

To see what's in the cache:

```powershell
.\Back_end\venvi\Scripts\python.exe -c "
import pandas as pd
df = pd.read_parquet('Back_end/cache/nc_endpoint_cache.parquet')
print(f'Total entries: {len(df)}')
print(f'Date range: {df[\"week_start\"].min()} to {df[\"week_start\"].max()}')
print(f'Unique locations: {df[[\"lat\",\"lon\"]].drop_duplicates().shape[0]}')
print(f'Unique weeks: {df[\"week_start\"].nunique()}')
"
```

## Performance Tips

1. **Pre-build cache** for frequently accessed dates (2018-2021)
2. **Use sharding** for parallel cache building (4x faster)
3. **Monitor hits** during user testing to identify gaps
4. **Cache is optional** - app works without it, just slower

## Troubleshooting

### Not Seeing Cache Hits

**Problem:** No `[CACHE HIT]` messages even though cache exists

**Checklist:**
1. Cache file exists? `ls Back_end/cache/*.parquet`
2. Running from Back_end directory? `cd Back_end`
3. Cache key matches request? Check lat/lon/date exactly
4. Source files unchanged? Cache invalidates if data files modified

### Slow Even With Cache

**Problem:** Cache hit still takes seconds

**Possible causes:**
1. Large Parquet file (>100MB) - consider sharding by date range
2. Network latency (if cache on network drive)
3. Antivirus scanning cache files
4. First request after server start (Parquet engine loading)

## Summary

✅ **Cache Hit:** 50-200ms response, `[CACHE HIT]` in console
❌ **Cache Miss:** 10-20s response, no message, TensorFlow logs
🎯 **Goal:** Pre-build cache for 2018-2021 to serve all user requests from cache
