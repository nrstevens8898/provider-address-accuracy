"""Step 6: draw a random sample of 15 Majors to hand-check, covering every cause from
analyze_causes.py: 3 from each of the three largest causes, 2 from each of the other three.
A fixed seed means rerunning picks the same providers.

Output: data/handcheck_sample.csv, with empty columns correct_source, evidence_url, notes
to fill in by hand."""
import sqlite3

import pandas as pd

from analyze_causes import CAUSES

SEED = 42
PER_CAUSE = {CAUSES[3]: 3, CAUSES[4]: 3, CAUSES[5]: 3,   # the three largest causes
             CAUSES[0]: 2, CAUSES[1]: 2, CAUSES[2]: 2}


def address(*parts):
    return ", ".join(p for p in parts if p)


def main():
    with sqlite3.connect("provider_data.db") as conn:
        majors = pd.read_sql("""
            SELECT c.npi, c.primary_cause, n.first_name, n.last_name, n.credential,
                   n.address_1, n.address_2, n.city, n.state, n.zip
            FROM cause_analysis c JOIN nppes n ON n.npi = c.npi
            WHERE c.tier = 'Major' ORDER BY c.npi""", conn)
        medicare = pd.read_sql("SELECT * FROM medicare", conn)

    sample = pd.concat(majors[majors.primary_cause == cause].sample(n, random_state=SEED)
                       for cause, n in PER_CAUSE.items())

    rows = []
    for r in sample.itertuples():
        mine = medicare[medicare.npi == r.npi]
        med_addresses = dict.fromkeys(   # distinct, in file order
            address(m.adr_ln_1, m.adr_ln_2, m.citytown, m.state, m.zip_code[:5]) for m in mine.itertuples())
        groups = dict.fromkeys(f for f in mine.facility_name if f) or {"(no group: bills on own)": None}
        rows.append({
            "name": f"{r.first_name} {r.last_name}, {r.credential}".strip(", "),
            "npi": r.npi,
            "nppes_address": address(r.address_1, r.address_2, r.city, r.state, r.zip[:5]),
            "medicare_addresses": " | ".join(med_addresses),
            "medicare_groups": " | ".join(groups),
            "assigned_cause": r.primary_cause,
            "correct_source": "", "evidence_url": "", "notes": "",
        })

    out = pd.DataFrame(rows)
    out.to_csv("data/handcheck_sample.csv", index=False)
    print(out.drop(columns=["correct_source", "evidence_url", "notes"]).to_string())


if __name__ == "__main__":
    main()
