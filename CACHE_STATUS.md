# Cache Status

Use this file to track what has been precomputed and merged.

## Current Shared Shard Plan

- Endpoint run mode: `--shard-count 4`
- Date window: `2018-01-01` to `2021-12-27`

Shard index assignments:
- `shard-index 0` -> terminal A
- `shard-index 1` -> terminal B
- `shard-index 2` -> terminal C
- `shard-index 3` -> terminal D

## Smoke Test Dates (15 weekly starts)

These are the 15 dates from the quick validation run:

1. 2020-01-06
2. 2020-01-13
3. 2020-01-20
4. 2020-01-27
5. 2020-02-03
6. 2020-02-10
7. 2020-02-17
8. 2020-02-24
9. 2020-03-02
10. 2020-03-09
11. 2020-03-16
12. 2020-03-23
13. 2020-03-30
14. 2020-04-06
15. 2020-04-13

## Progress Checklist

NC endpoint (`getNcData`):
- [ ] shard 0 complete
- [ ] shard 1 complete
- [ ] shard 2 complete
- [ ] shard 3 complete
- [ ] merge complete (`merge_parquet_cache --endpoint nc`)

Mean endpoint (`getMeanData`):
- [ ] shard 0 complete
- [ ] shard 1 complete
- [ ] shard 2 complete
- [ ] shard 3 complete
- [ ] merge complete (`merge_parquet_cache --endpoint mean`)

## Notes

- Shard files are in `Back_end/cache/`:
  - `nc_endpoint_cache.shard-<i>-of-4.parquet`
  - `mean_endpoint_cache.shard-<i>-of-4.parquet`
- Final merged files:
  - `Back_end/cache/nc_endpoint_cache.parquet`
  - `Back_end/cache/mean_endpoint_cache.parquet`
