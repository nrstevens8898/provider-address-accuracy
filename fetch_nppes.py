"""Pull every psychiatrist with a practice location in a Manhattan ZIP (10001-10299)
from the NPPES NPI Registry API, saving each raw response untouched."""
import json
import ssl
import time
import urllib.parse
import urllib.request
from pathlib import Path

import certifi

BASE_URL = "https://npiregistry.cms.hhs.gov/api/"
PARAMS = {
    "version": "2.1",
    "taxonomy_description": "Psychiatry",
    "state": "NY",
    "enumeration_type": "NPI-1",       # individual providers only
    "address_purpose": "LOCATION",     # match practice addresses, not mailing
    "limit": 200,                      # API maximum per request
}
MAX_SKIP = 1000                        # API won't skip past this
OUT_DIR = Path("data/raw/by_zip")
SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())


def fetch(params, retries=3):
    url = BASE_URL + "?" + urllib.parse.urlencode(params)
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=30, context=SSL_CONTEXT) as resp:
                return resp.read()
        except Exception as e:
            print(f"  retry {attempt + 1} after error: {e}")
            time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"Failed after {retries} tries: {url}")


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    flagged = []
    for zip_code in range(10001, 10300):
        zip_code = str(zip_code)
        for skip in range(0, MAX_SKIP + 1, 200):
            raw = fetch({**PARAMS, "postal_code": zip_code, "skip": skip})
            (OUT_DIR / f"zip_{zip_code}_skip{skip:04d}.json").write_bytes(raw)
            n = len(json.loads(raw).get("results", []))
            if n:
                print(f"{zip_code} skip={skip}: {n}")
            time.sleep(0.25)
            if n < 200:
                break
            if skip == MAX_SKIP:
                flagged.append(zip_code)
    print("ZIPs that hit the API ceiling (may be incomplete):", flagged or "none")


if __name__ == "__main__":
    main()
