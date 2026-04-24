"""
resign_cache.py — Rewrite the source_signature column in both parquet cache files
to match the local file stats on this machine.

Run from the Back_end/ directory:
    python resign_cache.py

Or from the repo root:
    python Back_end/resign_cache.py
"""

import sys
from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------------
# Locate Back_end/ regardless of where the script is invoked from
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent   # always Back_end/
CACHE_DIR = SCRIPT_DIR / "cache"

SOURCE_PATHS = [
    "Nc_data/CAM6_SM_0_5m_0_45_leadday_1999_2021_organize_Ens_mean_normalized.nc",
    "ERA5/ERA5_SM_0_5m_0_45_leadday_1999_2021_organize_normalized.nc",
    "Best_Model",
]

CACHE_FILES = [
    CACHE_DIR / "nc_endpoint_cache.parquet",
    CACHE_DIR / "mean_endpoint_cache.parquet",
]


def build_local_signature() -> str:
    parts = []
    for rel in SOURCE_PATHS:
        abs_path = SCRIPT_DIR / rel
        if not abs_path.exists():
            parts.append(f"{rel}:missing")
            print(f"  WARNING: {abs_path} not found — will write ':missing' for this entry")
            continue
        stat = abs_path.stat()
        parts.append(f"{rel}:{stat.st_mtime_ns}:{stat.st_size}")
        print(f"  {rel}  mtime_ns={stat.st_mtime_ns}  size={stat.st_size}")
    return "|".join(parts)


def resign_file(parquet_path: Path, new_sig: str) -> int:
    if not parquet_path.exists():
        print(f"  SKIP: {parquet_path} does not exist")
        return 0
    df = pd.read_parquet(parquet_path)
    old_sigs = df["source_signature"].unique()
    print(f"  Old signatures ({len(old_sigs)} unique):")
    for s in old_sigs:
        print(f"    {s[:120]}{'...' if len(s) > 120 else ''}")
    df["source_signature"] = new_sig
    df.to_parquet(parquet_path, index=False)
    print(f"  Wrote {len(df)} rows -> {parquet_path.name}")
    return len(df)


def main():
    print("=== resign_cache.py ===")
    print(f"Back_end dir : {SCRIPT_DIR}")
    print(f"Cache dir    : {CACHE_DIR}")
    print()

    print("Building local source signature...")
    new_sig = build_local_signature()
    print(f"\nNew signature:\n  {new_sig}\n")

    total = 0
    for cache_file in CACHE_FILES:
        print(f"Processing {cache_file.name} ...")
        total += resign_file(cache_file, new_sig)
        print()

    print(f"Done. {total} total rows re-signed across {len(CACHE_FILES)} files.")


if __name__ == "__main__":
    main()
