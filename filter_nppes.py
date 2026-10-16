"""Part 2: from the raw ZIP pull, keep providers whose main practice address is in
Manhattan and whose primary specialty is psychiatry. Raw files are only read."""
import csv
import glob
import json
from collections import Counter

MANHATTAN_ZIPS = ("10001", "10299")

# The 6 psychiatry categories we keep (decision #6)
PSYCHIATRY = {
    "2084P0800X": "Psychiatry",
    "2084P0804X": "Child & Adolescent Psychiatry",
    "2084P0805X": "Geriatric Psychiatry",
    "2084P0802X": "Addiction Psychiatry",
    "2084P0015X": "Psychosomatic Medicine",
    "2084F0202X": "Forensic Psychiatry",
}
# Borderline: could be psychiatry or not; dropped (decision #6)
BORDERLINE = {
    "2084P2900X": "shared subspecialty (Pain Medicine)",
    "2084S0012X": "shared subspecialty (Sleep Medicine)",
    "2084H0002X": "shared subspecialty (Hospice and Palliative Medicine)",
    "2084B0040X": "shared subspecialty (Behavioral Neurology & Neuropsychiatry)",
    "2084A0401X": "shared subspecialty (Addiction Medicine)",
    "390200000X": "student in training program",
    "363LP0808X": "psychiatric nurse practitioner",
}
# The API left these descriptions blank; filled in from the official code list (decision #7)
MISSING_DESCRIPTIONS = {
    "2084P0805X": "Psychiatry & Neurology, Geriatric Psychiatry",
    "2084N0600X": "Psychiatry & Neurology, Clinical Neurophysiology",
    "208VP0000X": "Pain Medicine, Pain Medicine",
}


def load_providers():
    by_npi = {}
    for path in sorted(glob.glob("data/raw/by_zip/*.json")):
        with open(path) as f:
            for rec in json.load(f).get("results", []):
                by_npi[rec["number"]] = rec
    return by_npi


def main_location(rec):
    return next(a for a in rec["addresses"] if a["address_purpose"] == "LOCATION")


def primary_taxonomy(rec):
    return next((t for t in rec["taxonomies"] if t.get("primary")), None)


def main():
    providers = load_providers()
    kept, dropped = [], []
    outside_manhattan = 0
    for npi, rec in providers.items():
        zip5 = main_location(rec)["postal_code"][:5]
        tax = primary_taxonomy(rec)
        code = tax["code"] if tax else ""
        desc = (tax.get("desc") or MISSING_DESCRIPTIONS.get(code, "")) if tax else ""
        if not MANHATTAN_ZIPS[0] <= zip5 <= MANHATTAN_ZIPS[1]:
            outside_manhattan += 1
            dropped.append({"npi": npi, "primary_taxonomy_code": code,
                            "primary_taxonomy": desc, "reason": "main address outside Manhattan"})
            continue
        if code in PSYCHIATRY:
            kept.append({"npi": npi, "primary_taxonomy_code": code, "primary_taxonomy": desc})
        else:
            if not tax:
                reason = "borderline: no primary specialty marked"
            elif code in BORDERLINE:
                reason = "borderline: " + BORDERLINE[code]
            else:
                reason = "not psychiatry"
            dropped.append({"npi": npi, "primary_taxonomy_code": code,
                            "primary_taxonomy": desc, "reason": reason})

    for path, rows in [("data/population_npis.csv", kept), ("data/dropped_providers.csv", dropped)]:
        with open(path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(sorted(rows, key=lambda r: r["npi"]))

    print("unique providers pulled:", len(providers))
    print("Manhattan-based:", len(providers) - outside_manhattan)
    print("kept (psychiatry):", len(kept))
    for reason, n in Counter(r["reason"].split(":")[0] for r in dropped).most_common():
        print(f"dropped, {reason}:", n)


if __name__ == "__main__":
    main()
