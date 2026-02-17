# NG-ISMFS (Next Generation Interactive Soil Moisture Forecasting System)

This repository contains:
- Django backend API (`Back_end`)
- Angular frontend (`Front_end/Frontend_angular`)

## Folder Layout

Expected project layout (important for backend runtime paths):
- `Back_end/Nc_data/`  
  Contains NCAR/CESM NetCDF files, including:  
  `CAM6_SM_0_5m_0_45_leadday_1999_2021_organize_Ens_mean_normalized.nc`
- `Back_end/ERA5/`  
  Contains ERA5 NetCDF files, including:  
  `ERA5_SM_0_5m_0_45_leadday_1999_2021_organize_normalized.nc`
- `Back_end/MEERA_2/`  
  Contains MERRA2 files used by legacy/optional paths.
- `Back_end/Neon_data/`  
  Contains NEON site Excel files.
- `Back_end/Best_Model/`  
  Contains all `.h5` model files (`Whole_US`, `Model_2_13`, `Model_2_27`, `Model_2_45`, etc.).

If those folders/files are missing, backend endpoints will fail with file-not-found errors.

## Backend Setup (Django)

From repo root (`Nc_Map`), install backend dependencies:

```powershell
.\Back_end\venvi\Scripts\python.exe -m pip install -r .\Back_end\requirements.txt
```

Install Parquet support (new cache feature):

```powershell
.\Back_end\venvi\Scripts\python.exe -m pip install pyarrow
```

Run backend:

```powershell
.\Back_end\venvi\Scripts\python.exe .\Back_end\manage.py runserver
```

Backend API base URL used by frontend:
- `http://127.0.0.1:8000/`

## Frontend Setup (Angular)

From repo root:

```powershell
cd .\Front_end\Frontend_angular
npm install
npm start
```

Default frontend dev URL:
- `http://localhost:4200/`

## Optional: Build Forecast Cache (Parquet)

From repo root:

```powershell
.\Back_end\venvi\Scripts\python.exe .\Back_end\manage.py build_parquet_cache --endpoint nc
.\Back_end\venvi\Scripts\python.exe .\Back_end\manage.py build_parquet_cache --endpoint mean
```

Useful for a quick test run:

```powershell
.\Back_end\venvi\Scripts\python.exe .\Back_end\manage.py build_parquet_cache --endpoint nc --start-date 2020-01-06 --end-date 2020-02-24
```

Parallel precompute (safe across multiple terminals):

Terminal 1:
```powershell
.\Back_end\venvi\Scripts\python.exe .\Back_end\manage.py build_parquet_cache --endpoint nc --shard-count 4 --shard-index 0
```

Terminal 2:
```powershell
.\Back_end\venvi\Scripts\python.exe .\Back_end\manage.py build_parquet_cache --endpoint nc --shard-count 4 --shard-index 1
```

Terminal 3:
```powershell
.\Back_end\venvi\Scripts\python.exe .\Back_end\manage.py build_parquet_cache --endpoint nc --shard-count 4 --shard-index 2
```

Terminal 4:
```powershell
.\Back_end\venvi\Scripts\python.exe .\Back_end\manage.py build_parquet_cache --endpoint nc --shard-count 4 --shard-index 3
```

After all shards complete, merge:

```powershell
.\Back_end\venvi\Scripts\python.exe .\Back_end\manage.py merge_parquet_cache --endpoint nc
```

Do the same for `mean` endpoint if needed.

## Verify Cache Is Being Used

When cache is hit, backend prints logs similar to:

```text
[CACHE HIT] endpoint=nc key=nc|2020-01-06|45.8200|-121.9520 file=nc_endpoint_cache.parquet
```

For bar-graph endpoint:

```text
[CACHE HIT] endpoint=mean key=mean|2020-01-06|45.8200|-121.9520 file=mean_endpoint_cache.parquet
```

If you see TensorFlow inference steps immediately for the same request, that request was a cache miss.

## Notes

- Start backend before frontend so API calls succeed.
- Large data/model folders are intentionally gitignored.
- Current cache implementation uses week-based keys (Monday start) between 1999 and 2021 data range.
- For 2018+ parallel cache runs, see `CACHE_RUNBOOK.md`.
- For current cache progress and the 15-date smoke set, see `CACHE_STATUS.md`.
