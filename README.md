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

## Cache

Forecast responses are cached as Parquet files so the model doesn't re-run on repeated requests. See `CACHE.md` for how it works, how to rebuild, and troubleshooting.

## Notes

- Start backend before frontend so API calls succeed.
- Large data/model folders are intentionally gitignored.
- Cache uses week-based keys (Monday start) across the 1999–2021 data range.
