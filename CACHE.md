# Cache

The app uses Parquet files to cache forecast responses so the model doesn't have to re-run for every request.

**Cache hits return in ~50–200ms. Cache misses take 10–20 seconds (model has to run).**

Cache files live in `Back_end/cache/`:
- `nc_endpoint_cache.parquet` — covers `/getNcData/`
- `mean_endpoint_cache.parquet` — covers `/getMeanData/`

The cache is keyed by `endpoint | week_start | lat | lon`. If you click slightly off a cached coordinate it falls back to the nearest cached point within 2 degrees.

## Reading Console Output

Cache hit:
```
[CACHE HIT] endpoint=nc key=nc|2020-01-06|45.7620|-122.3300 file=nc_endpoint_cache.parquet
```

Cache miss (no `[CACHE HIT]` line, TensorFlow logs appear, slow response):
```
2026-02-26 17:30:45.123456: I tensorflow/core/util/port.cc:113] oneDNN custom operations are on...
```

## Rebuilding or Extending the Cache

The full dataset runs 1999–2021. If you need to rebuild or fill gaps, run from repo root:

**Single endpoint, full range (slow, sequential):**
```powershell
.\Back_end\venvi\Scripts\python.exe .\Back_end\manage.py build_parquet_cache --endpoint nc
.\Back_end\venvi\Scripts\python.exe .\Back_end\manage.py build_parquet_cache --endpoint mean
```

**Parallel (4 terminals, much faster):**
```powershell
# Terminal 1
.\Back_end\venvi\Scripts\python.exe .\Back_end\manage.py build_parquet_cache --endpoint nc --shard-count 4 --shard-index 0
# Terminal 2
.\Back_end\venvi\Scripts\python.exe .\Back_end\manage.py build_parquet_cache --endpoint nc --shard-count 4 --shard-index 1
# Terminal 3
.\Back_end\venvi\Scripts\python.exe .\Back_end\manage.py build_parquet_cache --endpoint nc --shard-count 4 --shard-index 2
# Terminal 4
.\Back_end\venvi\Scripts\python.exe .\Back_end\manage.py build_parquet_cache --endpoint nc --shard-count 4 --shard-index 3
```

After all shards finish, merge:
```powershell
.\Back_end\venvi\Scripts\python.exe .\Back_end\manage.py merge_parquet_cache --endpoint nc
.\Back_end\venvi\Scripts\python.exe .\Back_end\manage.py merge_parquet_cache --endpoint mean
```

If a shard fails, rerun only that shard. Merging is safe to re-run.

## Checking Cache Coverage

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

## Resign Cache (`resign_cache.py`)

`Back_end/resign_cache.py` re-signs or re-indexes the merged cache file. Run it after a full rebuild if cache reads seem stale or keys aren't matching:

```powershell
.\Back_end\venvi\Scripts\python.exe .\Back_end\resign_cache.py
```

## Troubleshooting

**No cache hits even though the file exists:**
1. Check the file is there: `ls Back_end/cache/*.parquet`
2. Make sure backend is running from `Back_end/` directory
3. Verify the lat/lon/date you're requesting falls within the cached range

**Cache hit is still slow:**
- First request after server start always has overhead (Parquet engine initializing)
- Subsequent hits should be fast
