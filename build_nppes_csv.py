"""Part 3: flatten the raw NPPES records for the fixed population (data/population_npis.csv)
into one row per provider, plus a separate file of secondary practice locations."""
import csv

from filter_nppes import MISSING_DESCRIPTIONS, load_providers, main_location, primary_taxonomy

ADDRESS_FIELDS = ["address_1", "address_2", "city", "state", "zip"]


def address(addr):
    return {
        "address_1": addr.get("address_1", ""),
        "address_2": addr.get("address_2", ""),
        "city": addr.get("city", ""),
        "state": addr.get("state", ""),
        "zip": addr.get("postal_code", ""),
    }


def write_csv(path, rows, fieldnames):
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main():
    with open("data/population_npis.csv") as f:
        npis = [row["npi"] for row in csv.DictReader(f)]
    providers = load_providers()

    rows, secondary = [], []
    for npi in npis:
        rec = providers[npi]
        basic = rec["basic"]
        tax = primary_taxonomy(rec)
        loc = main_location(rec)
        rows.append({
            "npi": npi,
            "first_name": basic.get("first_name", ""),
            "middle_name": basic.get("middle_name", ""),
            "last_name": basic.get("last_name", ""),
            "credential": basic.get("credential", ""),
            "primary_taxonomy_code": tax["code"],
            "primary_taxonomy": tax.get("desc") or MISSING_DESCRIPTIONS.get(tax["code"], ""),
            **address(loc),
            "phone": loc.get("telephone_number", ""),
            "enumeration_date": basic.get("enumeration_date", ""),
            "last_updated": basic.get("last_updated", ""),
        })
        for sec in rec.get("practiceLocations", []):
            secondary.append({"npi": npi, **address(sec)})

    write_csv("data/nppes.csv", rows, rows[0].keys())
    write_csv("data/nppes_secondary_locations.csv", secondary, ["npi"] + ADDRESS_FIELDS)
    print("nppes.csv rows:", len(rows))
    print("nppes_secondary_locations.csv rows:", len(secondary))
    print("providers with 1+ secondary location:", len({r["npi"] for r in secondary}))


if __name__ == "__main__":
    main()
