"""Step 3: query the CMS Doctors and Clinicians National Downloadable File for every NPI
in data/population_npis.csv, saving each raw response untouched. All rows for each NPI are
kept, whatever the address (decision #11)."""
import csv
import json
import ssl
import time
import urllib.request
from pathlib import Path

import certifi

DATASET_ID = "mj5m-pzi6"
QUERY_URL = f"https://data.cms.gov/provider-data/api/1/datastore/query/{DATASET_ID}/0"
METADATA_URL = f"https://data.cms.gov/provider-data/api/1/metastore/schemas/dataset/items/{DATASET_ID}"
BATCH_SIZE = 100
PAGE_LIMIT = 1500
OUT_DIR = Path("data/raw/medicare")
SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())


def request(url, body=None, retries=3):
    data = json.dumps(body).encode() if body else None
    headers = {"Content-Type": "application/json"} if body else {}
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, data=data, headers=headers)
            with urllib.request.urlopen(req, timeout=60, context=SSL_CONTEXT) as resp:
                return resp.read()
        except Exception as e:
            print(f"  retry {attempt + 1} after error: {e}")
            time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"Failed after {retries} tries: {url}")


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "dataset_metadata.json").write_bytes(request(METADATA_URL))

    with open("data/population_npis.csv") as f:
        npis = [row["npi"] for row in csv.DictReader(f)]

    total_rows = 0
    for batch_num, start in enumerate(range(0, len(npis), BATCH_SIZE), 1):
        batch = npis[start:start + BATCH_SIZE]
        offset, fetched, expected = 0, 0, None
        while expected is None or fetched < expected:
            body = {
                "conditions": [{"property": "npi", "value": batch, "operator": "in"}],
                "limit": PAGE_LIMIT, "offset": offset,
                "count": True, "results": True, "schema": False,
            }
            raw = request(QUERY_URL, body)
            (OUT_DIR / f"batch_{batch_num:02d}_offset{offset:05d}.json").write_bytes(raw)
            page = json.loads(raw)
            expected = page["count"]
            fetched += len(page["results"])
            offset += PAGE_LIMIT
            time.sleep(0.25)
            if not page["results"]:
                break
        print(f"batch {batch_num}: {len(batch)} NPIs -> {fetched} rows (API count {expected})")
        if fetched != expected:
            print(f"  WARNING: batch {batch_num} fetched {fetched} but API reported {expected}")
        total_rows += fetched
    print("total rows:", total_rows)


if __name__ == "__main__":
    main()
