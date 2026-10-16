"""Step 5: why do NPPES and Medicare addresses differ?

Tests the two hypotheses in framing.md section 4 on the 919 comparable providers (Match,
Minor or Major in `address_comparison`):
  staleness          - Majors should cluster among old NPPES `last_updated` dates
  multiple locations - Majors should cluster among providers with several addresses
and a third explanation the data pointed to:
  group address      - Medicare lists the address of the group a provider bills through

Then assigns each Major one most likely cause, first matching rule wins (decision #24).

Outputs: data/cause_analysis.csv and the SQLite table `cause_analysis`."""
import math
import sqlite3

import pandas as pd

DATA_DATE = pd.Timestamp("2026-08-18")   # Medicare file "data as of" date (decision #12)

CAUSES = [
    "a. Medicare lists the provider's other NPPES practice",
    "b. NPPES never updated since NPI issued",
    "c. Wrong building, same medical center",
    "d. Medicare lists a group site outside Manhattan",
    "e. Medicare lists a group site elsewhere in Manhattan",
    "f. Solo provider, different address",
]


def update_bucket(years):
    if years < 2:
        return "1: < 2 yrs"
    if years < 5:
        return "2: 2-5 yrs"
    if years < 10:
        return "3: 5-10 yrs"
    return "4: 10+ yrs"


def group_bucket(size):
    if size == 0:
        return "1: no group"
    return "2: group < 100" if size < 100 else "3: group 100+"


def address_bucket(n):
    return "1" if n == 1 else "2" if n == 2 else "3-5" if n <= 5 else "6+"


def primary_cause(r):
    if r.tier != "Major":
        return None
    if r.secondary_tier in ("Match", "Minor"):
        return CAUSES[0]
    if r.never_updated:
        return CAUSES[1]
    if r.major_location == "Same campus":
        return CAUSES[2]
    if r.group_size > 0:
        return CAUSES[3] if r.major_location == "Outside Manhattan" else CAUSES[4]
    return CAUSES[5]


def rate_table(df, col):
    t = df.groupby(col).agg(providers=("is_major", "size"), majors=("is_major", "sum"))
    t["major_pct"] = (100 * t.majors / t.providers).round(1)
    return t


def two_proportion_p(x1, n1, x2, n2):
    """Two-sided p-value for 'these two rates are the same' (normal approximation)."""
    p = (x1 + x2) / (n1 + n2)
    z = (x1 / n1 - x2 / n2) / math.sqrt(p * (1 - p) * (1 / n1 + 1 / n2))
    return math.erfc(abs(z) / math.sqrt(2))


def main():
    with sqlite3.connect("provider_data.db") as conn:
        df = pd.read_sql("""
            SELECT a.npi, a.tier, a.n_medicare_addresses, a.secondary_tier, a.major_location,
                   n.last_updated, n.enumeration_date,
                   COALESCE((SELECT MAX(CAST(m.num_org_mem AS INTEGER)) FROM medicare m
                             WHERE m.npi = a.npi), 0) AS group_size,
                   (SELECT COUNT(*) FROM nppes_secondary_locations s
                    WHERE s.npi = a.npi) AS n_secondary_locations
            FROM address_comparison a JOIN nppes n ON n.npi = a.npi
            WHERE a.tier IN ('Match', 'Minor', 'Major')""", conn)

    df["is_major"] = df.tier == "Major"
    df["years_since_update"] = (DATA_DATE - pd.to_datetime(df.last_updated)).dt.days / 365.25
    df["since_update"] = df.years_since_update.map(update_bucket)
    df["never_updated"] = df.last_updated == df.enumeration_date
    df["group"] = df.group_size.map(group_bucket)
    df["medicare_addresses"] = df.n_medicare_addresses.map(address_bucket)
    df["has_secondary"] = df.n_secondary_locations > 0
    df["primary_cause"] = df.apply(primary_cause, axis=1)

    print("== Staleness: Major rate by years since NPPES last update")
    print(rate_table(df, "since_update").to_string())
    print("\n== Multiple locations: Major rate by number of Medicare addresses")
    print(rate_table(df, "medicare_addresses").to_string())
    print("\n== Multiple locations: Major rate by whether NPPES lists secondary locations")
    print(rate_table(df, "has_secondary").to_string())
    print("\n== Group address: Major rate by size of the Medicare group")
    print(rate_table(df, "group").to_string())
    print("\n== Group size x staleness (5-year split)")
    df["updated_5y"] = df.years_since_update.map(lambda y: "1: < 5 yrs" if y < 5 else "2: 5+ yrs")
    print(rate_table(df, ["group", "updated_5y"]).to_string())

    solo = df[df.group == "1: no group"]
    recent, old = solo[solo.updated_5y == "1: < 5 yrs"], solo[solo.updated_5y == "2: 5+ yrs"]
    print(f"\nSolo, updated < 5 yrs vs 5+ yrs: p = "
          f"{two_proportion_p(recent.is_major.sum(), len(recent), old.is_major.sum(), len(old)):.6f}")
    grouped = df[df.group != "1: no group"]
    print(f"In a group vs no group: p = "
          f"{two_proportion_p(grouped.is_major.sum(), len(grouped), solo.is_major.sum(), len(solo)):.2e}")

    print("\n== Most likely cause of each Major (first matching rule wins)")
    causes = df.primary_cause.value_counts().reindex(CAUSES)
    print(pd.DataFrame({"majors": causes,
                        "pct_of_majors": (100 * causes / df.is_major.sum()).round(1)}).to_string())

    out = df.drop(columns=["is_major", "updated_5y"])
    out.to_csv("data/cause_analysis.csv", index=False)
    with sqlite3.connect("provider_data.db") as conn:
        out.to_sql("cause_analysis", conn, if_exists="replace", index=False)


if __name__ == "__main__":
    main()
