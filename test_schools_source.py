import os

import pandas as pd
from dotenv import load_dotenv

load_dotenv()

from dashboard.services.school_source import load_schools, refresh_schools


status = refresh_schools(force=True)

print("STATUS")
print("  rows:", status.rows)
print("  source:", status.source)
print("  sha256:", status.sha256[:12])
print("  updated:", status.updated)
print("  parquet:", status.parquet_path)

df = load_schools()

print("\nDATAFRAME")
print("  shape:", df.shape)
print("  columns:", df.columns.tolist())

print("\nESCOLAS")
cols = [
    c
    for c in [
        "school_code",
        "school_name",
        "latitude",
        "longitude",
        "coordinate_status",
    ]
    if c in df.columns
]
print(df[cols].to_string(index=False))
