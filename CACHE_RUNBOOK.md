# Cache Runbook (2018 to Dataset End, 4 Shards)

This runbook builds cache only for the modern slice:
- Start: `2018-01-01`
- End: `2021-12-27` (last Monday week-start in your dataset window ending 2021-12-31)

Run all commands from repo root:
- `D:\2026\spring26\senior-design\Nc_Map_Final\Nc_Map_Graph_Correct\Nc_Map`

## 1) NC Endpoint (`/getNcData/`) in 4 shards

Open 4 terminals and run one command per terminal:

Terminal A:
```powershell
.\Back_end\venvi\Scripts\python.exe .\Back_end\manage.py build_parquet_cache --endpoint nc --shard-count 4 --shard-index 0 --start-date 2018-01-01 --end-date 2021-12-27
```

Terminal B:
```powershell
.\Back_end\venvi\Scripts\python.exe .\Back_end\manage.py build_parquet_cache --endpoint nc --shard-count 4 --shard-index 1 --start-date 2018-01-01 --end-date 2021-12-27
```

Terminal C:
```powershell
.\Back_end\venvi\Scripts\python.exe .\Back_end\manage.py build_parquet_cache --endpoint nc --shard-count 4 --shard-index 2 --start-date 2018-01-01 --end-date 2021-12-27
```

Terminal D:
```powershell
.\Back_end\venvi\Scripts\python.exe .\Back_end\manage.py build_parquet_cache --endpoint nc --shard-count 4 --shard-index 3 --start-date 2018-01-01 --end-date 2021-12-27
```

After all 4 finish:

```powershell
.\Back_end\venvi\Scripts\python.exe .\Back_end\manage.py merge_parquet_cache --endpoint nc
```

### Quick Validation Window (15 weekly dates)

Use this before full runs to verify everything end-to-end fast.

Window:
- Start: `2020-01-06`
- End: `2020-04-13`
- Weekly starts in this window: 15

Example single-shard smoke command (5-way shard test):

```powershell
.\Back_end\venvi\Scripts\python.exe .\Back_end\manage.py build_parquet_cache --endpoint nc --shard-count 5 --shard-index 4 --start-date 2020-01-06 --end-date 2020-04-13
```

Expected rows for this shard:
- `15 dates * 17 points / 5 shards = 51 rows`

After smoke run, merge so API can read it:

```powershell
.\Back_end\venvi\Scripts\python.exe .\Back_end\manage.py merge_parquet_cache --endpoint nc
```

Important:
- API reads merged main cache (`nc_endpoint_cache.parquet`), not shard files directly.

## 2) Mean Endpoint (`/getMeanData/`) in 4 shards

Repeat with `mean`:

Terminal A:
```powershell
.\Back_end\venvi\Scripts\python.exe .\Back_end\manage.py build_parquet_cache --endpoint mean --shard-count 4 --shard-index 0 --start-date 2018-01-01 --end-date 2021-12-27
```

Terminal B:
```powershell
.\Back_end\venvi\Scripts\python.exe .\Back_end\manage.py build_parquet_cache --endpoint mean --shard-count 4 --shard-index 1 --start-date 2018-01-01 --end-date 2021-12-27
```

Terminal C:
```powershell
.\Back_end\venvi\Scripts\python.exe .\Back_end\manage.py build_parquet_cache --endpoint mean --shard-count 4 --shard-index 2 --start-date 2018-01-01 --end-date 2021-12-27
```

Terminal D:
```powershell
.\Back_end\venvi\Scripts\python.exe .\Back_end\manage.py build_parquet_cache --endpoint mean --shard-count 4 --shard-index 3 --start-date 2018-01-01 --end-date 2021-12-27
```

After all 4 finish:

```powershell
.\Back_end\venvi\Scripts\python.exe .\Back_end\manage.py merge_parquet_cache --endpoint mean
```

## Resume Later

- If a shard fails, rerun only that shard command.
- Merging is idempotent for current dedupe logic; you can re-run merge safely.

## Where Cache Files Live

- Folder: `Back_end/cache/`
- Shards: `nc_endpoint_cache.shard-<i>-of-4.parquet` and `mean_endpoint_cache.shard-<i>-of-4.parquet`
- Merged output: `nc_endpoint_cache.parquet`, `mean_endpoint_cache.parquet`
