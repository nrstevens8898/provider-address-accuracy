"""Step 3: combine the raw Medicare responses into data/medicare.csv (every row, every
column) and load it into the SQLite table `medicare`. All columns are stored as text."""
import glob
import json
import sqlite3

import pandas as pd

rows = []
for path in sorted(glob.glob("data/raw/medicare/batch_*.json")):
    with open(path) as f:
        rows += json.load(f)["results"]

df = pd.DataFrame(rows).astype(str)
df.to_csv("data/medicare.csv", index=False)

with sqlite3.connect("provider_data.db") as conn:
    df.to_sql("medicare", conn, if_exists="replace", index=False)
print(f"loaded {len(df)} rows into medicare")
