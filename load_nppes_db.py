"""Part 4: load the flattened NPPES CSVs into SQLite. All columns are stored as text
so ZIPs, NPIs, and phone numbers keep their leading zeros."""
import sqlite3

import pandas as pd

TABLES = {
    "nppes": "data/nppes.csv",
    "nppes_secondary_locations": "data/nppes_secondary_locations.csv",
}

with sqlite3.connect("provider_data.db") as conn:
    for table, path in TABLES.items():
        df = pd.read_csv(path, dtype=str, keep_default_na=False)
        df.to_sql(table, conn, if_exists="replace", index=False)
        print(f"loaded {len(df)} rows into {table}")
