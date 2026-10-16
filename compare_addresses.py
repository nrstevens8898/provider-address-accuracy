"""Step 4: compare each psychiatrist's NPPES main practice address to their Medicare
addresses and assign a tier (framing.md section 3):

  Match   - same building, and the same unit (or no unit to compare)
  Minor   - same building, different unit (suite/room/floor)
  Major   - no Medicare address is in the same building
  Can't compare - the NPPES address has no street number, or every Medicare address is a
            bare PO box or blank; excluded from the mismatch rate
  Missing - provider not in Medicare's file

Each address is split into a "building" (house number + cleaned street name) and a "unit"
(cleaned suite/room/floor). The best tier across all of a provider's Medicare addresses is
kept, since a patient reaching any real location still finds them.

Extra columns for checks that don't change the main tier:
  tier_strict_suite   - tier if a suite listed in only one source counts as Minor
  secondary_tier      - for Majors: best tier using NPPES secondary locations instead
  major_location      - for Majors: Same campus / Elsewhere in Manhattan / Outside Manhattan

Outputs: data/address_comparison.csv and the SQLite table `address_comparison`."""
import re
import sqlite3

import pandas as pd

# Words that start a unit: everything from here to the end of the line is the unit.
UNIT_WORDS = {"STE", "SUITE", "SUIT", "RM", "ROOM", "APT", "APARTMENT", "UNIT", "#", "FL",
              "FLR", "FLOOR", "PH", "PENTHOUSE", "BSMT", "BASEMENT", "LBBY", "LOBBY", "DEPT",
              "BOX", "MAILBOX", "BLDG", "OFC", "OFFICE", "LEVEL"}
# Units that are mailboxes, not places a patient can go: ignored when comparing.
MAIL_WORDS = {"BOX", "MAILBOX"}

ABBREVIATIONS = {
    "EAST": "E", "WEST": "W", "NORTH": "N", "SOUTH": "S",
    "STREET": "ST", "STR": "ST", "AVENUE": "AVE", "AV": "AVE", "PLACE": "PL",
    "DRIVE": "DR", "ROAD": "RD", "BOULEVARD": "BLVD", "PARKWAY": "PKWY", "LANE": "LN",
    "SQUARE": "SQ", "TERRACE": "TER", "PLAZA": "PLZ", "CIRCLE": "CIR", "COURT": "CT",
    "HIGHWAY": "HWY", "CENTER": "CTR", "MOUNT": "MT", "SAINT": "ST", "FORT": "FT",
}
ORDINALS = {"FIRST": "1ST", "SECOND": "2ND", "THIRD": "3RD", "FOURTH": "4TH", "FIFTH": "5TH",
            "SIXTH": "6TH", "SEVENTH": "7TH", "EIGHTH": "8TH", "NINTH": "9TH", "TENTH": "10TH",
            "ELEVENTH": "11TH", "TWELFTH": "12TH"}
HOUSE_WORDS = {w: str(i) for i, w in enumerate(
    "ONE TWO THREE FOUR FIVE SIX SEVEN EIGHT NINE TEN ELEVEN TWELVE".split(), 1)}
HOUSE_WORDS.update({"TWENTY": "20", "THIRTY": "30", "FORTY": "40", "FIFTY": "50",
                    "SIXTY": "60", "SEVENTY": "70", "EIGHTY": "80", "NINETY": "90"})
STREET_SUFFIXES = {"ST", "AVE", "PL", "DR", "RD", "BLVD", "PKWY", "LN", "SQ", "TER", "PLZ",
                   "CIR", "CT", "HWY", "WAY", "BROADWAY", "BOWERY", "SLIP", "ROW"}
# Manhattan streets with more than one common name, applied after abbreviating.
STREET_ALIASES = {
    "AVE OF THE AMERICAS": "6TH AVE", "AVE OF AMERICAS": "6TH AVE",
    "CENTRAL W PARK": "CENTRAL PARK W", "CENTRAL PARK WEST": "CENTRAL PARK W",
    "CENTRAL S PARK": "CENTRAL PARK S", "CENTRAL PARK SOUTH": "CENTRAL PARK S",
    "GUSTAV LEVY": "GUSTAVE LEVY",
    # Harlem avenues with two official names ('MALCOLM X' loses its 'X' as an initial).
    "MALCOLM BLVD": "LENOX AVE", "ADAM CLAYTON POWELL JR BLVD": "7TH AVE",
    "ADAM CLAYTON POWELL BLVD": "7TH AVE", "FREDERICK DOUGLASS BLVD": "8TH AVE",
}
DIRECTIONS = {"N", "S", "E", "W"}
# Hospital campuses: buildings (as cleaned by this script) that are part of one site, so a
# provider at one and listed at another is on the same campus. Only addresses seen in our data.
CAMPUSES = {
    "Mount Sinai (East Harlem)": {"1 GUSTAVE LEVY PL", "1425 MADISON AVE", "1428 MADISON AVE",
                                  "1450 MADISON AVE", "1468 MADISON AVE", "1470 MADISON AVE",
                                  "5 E 98TH ST", "19 E 98TH ST", "17 E 102ND ST",
                                  "1176 5TH AVE", "1184 5TH AVE"},
    "Columbia / NYP (Washington Heights)": {"622 W 168TH ST", "630 W 168TH ST", "650 W 168TH ST",
                                            "710 W 168TH ST", "722 W 168TH ST", "1051 RIVERSIDE DR",
                                            "161 FT WASHINGTON AVE", "177 FT WASHINGTON AVE",
                                            "180 FT WASHINGTON AVE", "60 HAVEN AVE",
                                            "3959 BROADWAY", "635 W 165TH ST"},
    "NYU Langone / Bellevue (Kips Bay)": {"530 1ST AVE", "550 1ST AVE", "560 1ST AVE",
                                          "462 1ST AVE", "400 E 34TH ST", "435 E 30TH ST"},
    "Weill Cornell / NYP (Upper East Side)": {"525 E 68TH ST", "1300 YORK AVE", "1305 YORK AVE",
                                              "520 E 70TH ST", "413 E 69TH ST", "402 E 67TH ST"},
    "Mount Sinai Beth Israel (Stuyvesant Sq)": {"10 NATHAN PERLMAN PL", "10 NATHAN PERLMAN ST",
                                                "281 1ST AVE", "317 E 17TH ST"},
    "Mount Sinai Morningside": {"1111 AMSTERDAM AVE", "1090 AMSTERDAM AVE", "411 W 114TH ST",
                                "440 W 114TH ST"},
    "Lenox Hill": {"100 E 77TH ST", "111 E 77TH ST", "130 E 77TH ST"},
}


def ordinal(n):
    n = int(n)
    suffix = "TH" if 10 <= n % 100 <= 20 else {1: "ST", 2: "ND", 3: "RD"}.get(n % 10, "TH")
    return f"{n}{suffix}"


def tokens(text):
    text = (text or "").upper().replace("'", "").replace("#", " # ")
    text = re.sub(r"[^A-Z0-9# -]", " ", text).replace(" - ", " ")
    text = re.sub(r"\b([NSEW])(\d+(ST|ND|RD|TH))\b", r"\1 \2", text)   # 'E68TH' -> 'E 68TH'
    text = re.sub(r"\b(\d+)([NSEW]) (?=\d)", r"\1 \2 ", text)           # '145W 86TH' -> '145 W 86TH'
    text = re.sub(r"\b(\d+) ?-\d+\b", r"\1", text)                      # '441 -451' -> '441'
    return text.replace("-", " ").split()


def starts_with_number(toks):
    """A house number: plain digits (maybe one letter, '350A'), not an ordinal like '1ST'."""
    return bool(toks) and (re.fullmatch(r"\d+[A-Z]?", toks[0]) is not None or toks[0] in HOUSE_WORDS)


def drop_prefix(toks):
    """'NYU LANGONE HOSPITAL 550 FIRST AVE' -> '550 FIRST AVE': start at the first
    all-digit token that is followed by a word."""
    for i, t in enumerate(toks):
        if t.isdigit() and i + 1 < len(toks) and toks[i + 1][0].isalpha():
            return toks[i:]
    return toks


def split_unit(toks):
    """Split a street line into (street tokens, unit tokens) at the first unit word.
    Also catches '12TH FLOOR' / 'SECOND FLOOR', where the floor number comes first."""
    for i, t in enumerate(toks):
        if i > 0 and t in UNIT_WORDS:
            if t in {"FL", "FLR", "FLOOR"} and i >= 1 and re.fullmatch(r"\d+(ST|ND|RD|TH)|[A-Z]+", toks[i - 1]) \
                    and (toks[i - 1][0].isdigit() or toks[i - 1] in ORDINALS):
                return toks[:i - 1], toks[i - 1:]
            return toks[:i], toks[i:]
    return toks, []


def looks_like_unit(toks):
    """Is a whole line 2 a unit (e.g. 'SUITE 5S', '5S', '12TH FLOOR', 'L6-20')?
    Lines like 'BERNSTEIN BUILDING' or 'NORTH GENERAL HOSPITAL' are not."""
    if not toks:
        return False
    if any(t in UNIT_WORDS for t in toks):
        return True
    return len(toks) <= 2 and len("".join(toks)) <= 5 and any(c.isdigit() for c in "".join(toks))


def unit_part(toks):
    """The unit portion of a line 2: from the first unit word (or 'NTH FLOOR') onward,
    so 'HERBERT IRVING PAVILION, SUITE 209' -> 'SUITE 209'."""
    if toks and toks[0] not in UNIT_WORDS:
        _, unit = split_unit(toks)
        if unit:
            return unit
    return toks


def clean_street(toks):
    """House number + street, with words abbreviated the same way in both sources."""
    out = []
    for i, t in enumerate(toks):
        if i == 0:
            t = HOUSE_WORDS.get(t, t)
        else:
            t = ORDINALS.get(t, t)
            t = ABBREVIATIONS.get(t, t)
            if t.isdigit():                      # 'W 27 ST' -> 'W 27TH ST'
                t = ordinal(t)
            if len(t) == 1 and t.isalpha() and t not in DIRECTIONS:
                continue                         # middle initials: 'GUSTAVE L LEVY'
        out.append(t)
    street = " ".join(out)
    for alias, canonical in STREET_ALIASES.items():
        street = street.replace(alias, canonical)
    # Cut anything after the street suffix ('525 E 68TH ST PWC' -> '525 E 68TH ST'),
    # keeping a direction that follows it ('300 CENTRAL PARK W').
    words = street.split()
    for i in range(2, len(words)):
        if words[i] in STREET_SUFFIXES:
            keep = i + 2 if i + 1 < len(words) and words[i + 1] in DIRECTIONS | {"SW", "NW", "SE", "NE"} else i + 1
            return " ".join(words[:keep])
    return street


def clean_unit(toks):
    """Unit as a bare value: 'STE 5S' -> '5S', '12TH FLOOR' -> 'FL12', 'APT 3-A' -> '3A'.
    Mailboxes return '' because they aren't a place."""
    if not toks or toks[0] in MAIL_WORDS:
        return ""
    floor = None
    rest = []
    used = set()                                 # positions holding the floor number
    for i, t in enumerate(toks):
        if t in {"FL", "FLR", "FLOOR"}:
            nxt = toks[i + 1] if i + 1 < len(toks) else ""
            prv = ORDINALS.get(toks[i - 1], toks[i - 1]) if i > 0 else ""
            if re.fullmatch(r"\d+(ST|ND|RD|TH)", prv):      # '3RD FLOOR'
                floor = re.match(r"\d+", prv).group()
                if rest and i - 1 not in used:
                    rest.pop()
            elif re.fullmatch(r"\d+(ST|ND|RD|TH)?", nxt):   # 'FL 8'
                floor = re.match(r"\d+", nxt).group()
                used.add(i + 1)
        elif i in used:
            continue
        elif t in MAIL_WORDS:
            break                                # 'STE 4 BOX 12': drop the mailbox part
        elif t not in UNIT_WORDS:
            rest.append(t)
    suite = re.sub(r"[^A-Z0-9]", "", "".join(rest)).lstrip("0")
    if suite:                                    # '11TH FLOOR SUITE 23' -> '23'
        return suite
    return f"FL{floor}" if floor is not None else ""


def parse(line1, line2):
    """Return (building, unit) for one address. building is None if no street was found."""
    t1, t2 = drop_prefix(tokens(line1)), drop_prefix(tokens(line2))
    if starts_with_number(t1):
        street_line, extra = t1, t2
    elif starts_with_number(t2):                 # 'COLUMBIA UNIV MED CTR' / '5 COLUMBUS CIR'
        street_line, extra = t2, []
    else:
        street_line, extra = t1, t2
    street, unit_toks = split_unit(street_line)
    unit = clean_unit(unit_toks)
    if unit_toks in (["FL"], ["FLR"], ["FLOOR"]) and looks_like_unit(extra):
        # Medicare writes floor 11 as 'FL' at the end of line 1 + 'SUITE 11' on line 2.
        number = clean_unit([t for t in unit_part(extra) if t not in UNIT_WORDS])
        return (clean_street(street) if starts_with_number(street) else None), f"FL{number}"
    if not unit and looks_like_unit(extra):      # suite on line 2 instead of line 1
        unit = clean_unit(unit_part(extra))
    building = clean_street(street) if starts_with_number(street) else None
    return building, unit


def is_manhattan(zip5):
    return zip5.isdigit() and 10001 <= int(zip5) <= 10299


def same_building(n, m):
    if n["building"] is None or n["building"] != m["building"]:
        return False
    # USPS renumbered some Manhattan ZIPs (e.g. 10021 -> 10065), so any two Manhattan
    # ZIPs are accepted; elsewhere the ZIP must match.
    return n["zip5"] == m["zip5"] or (is_manhattan(n["zip5"]) and is_manhattan(m["zip5"]))


def compare(n, m, strict_suite=False):
    """Tier for one NPPES/Medicare address pair, plus whether units were compared.
    strict_suite: a suite listed in only one source counts as Minor (sensitivity check)."""
    if not same_building(n, m):
        return "Major", False
    if n["unit"] and m["unit"]:
        return ("Match" if n["unit"] == m["unit"] else "Minor"), True
    if strict_suite and (n["unit"] or m["unit"] or m.get("ln_2_sprs") == "Y"):
        return "Minor", False
    return "Match", False


def best_tier(n, mine, strict_suite=False):
    return min((compare(n, m, strict_suite) for m in mine), key=lambda t: (TIER_RANK[t[0]], not t[1]))


def block(building):
    """'111 E 77TH ST' -> ('E 77TH ST', 1): the street and its hundred block."""
    number, _, street = building.partition(" ")
    return street, int(re.match(r"\d+", number).group()) // 100


def campus_of(building):
    return next((name for name, blds in CAMPUSES.items() if building in blds), None)


def major_location(n, mine):
    """Where a Major's Medicare addresses are relative to their NPPES building."""
    manhattan = [m for m in mine if is_manhattan(m["zip5"]) and m["building"]]
    if not manhattan:
        return "Outside Manhattan", None
    for m in manhattan:
        if block(m["building"]) == block(n["building"]):
            return "Same campus", "Same block"
    campus = campus_of(n["building"])
    if campus and any(campus_of(m["building"]) == campus for m in manhattan):
        return "Same campus", campus
    return "Elsewhere in Manhattan", None


TIER_RANK = {"Match": 0, "Minor": 1, "Major": 2}


def none_if_blank(df):
    """pandas stores a missing building as NaN; turn it back into None."""
    df["building"] = df["building"].astype(object).where(df["building"].notna(), None)


def main():
    with sqlite3.connect("provider_data.db") as conn:
        nppes = pd.read_sql("SELECT * FROM nppes", conn)
        medicare = pd.read_sql("SELECT * FROM medicare", conn)

    nppes[["building", "unit"]] = [parse(a, b) for a, b in zip(nppes.address_1, nppes.address_2)]
    nppes["zip5"] = nppes.zip.str[:5]
    medicare[["building", "unit"]] = [parse(a, b) for a, b in zip(medicare.adr_ln_1, medicare.adr_ln_2)]
    medicare["zip5"] = medicare.zip_code.str[:5]
    none_if_blank(nppes)
    none_if_blank(medicare)
    # The same address can appear on several rows (one per medical group); keep it once.
    med_addresses = medicare.drop_duplicates(["npi", "building", "unit", "zip5", "ln_2_sprs"])
    secondary = pd.read_sql("SELECT * FROM nppes_secondary_locations",
                            sqlite3.connect("provider_data.db"))
    secondary[["building", "unit"]] = [parse(a, b) for a, b in zip(secondary.address_1, secondary.address_2)]
    secondary["zip5"] = secondary.zip.str[:5]
    none_if_blank(secondary)

    rows = []
    for n in nppes.to_dict("records"):
        mine = med_addresses[med_addresses.npi == n["npi"]].to_dict("records")
        out = {"npi": n["npi"], "nppes_building": n["building"], "nppes_unit": n["unit"],
               "nppes_zip5": n["zip5"], "n_medicare_addresses": len(mine)}
        if not mine:
            rows.append({**out, "tier": "Missing"})
            continue
        if n["building"] is None or all(m["building"] is None for m in mine):
            reason = "NPPES has no street number" if n["building"] is None else "Medicare has only a PO box or blank"
            rows.append({**out, "tier": "Can't compare", "cant_compare_reason": reason})
            continue
        best = min(mine, key=lambda m: (TIER_RANK[compare(n, m)[0]], not compare(n, m)[1]))
        tier, unit_compared = compare(n, best)
        extra = {"tier_strict_suite": best_tier(n, mine, strict_suite=True)[0]}
        if tier == "Major":
            secs = [s for s in secondary[secondary.npi == n["npi"]].to_dict("records") if s["building"]]
            extra["n_secondary_locations"] = len(secs)
            extra["secondary_tier"] = min((best_tier(s, mine)[0] for s in secs),
                                          key=TIER_RANK.get, default="No secondary location")
            extra["major_location"], extra["same_campus_reason"] = major_location(n, mine)
        rows.append({
            **out, "tier": tier, "unit_compared": unit_compared, **extra,
            "medicare_unit_suppressed": best["ln_2_sprs"] == "Y",
            "medicare_building": best["building"], "medicare_unit": best["unit"],
            "medicare_zip5": best["zip5"],
            "any_medicare_manhattan": any(is_manhattan(m["zip5"]) for m in mine),
        })

    result = pd.DataFrame(rows)
    result.to_csv("data/address_comparison.csv", index=False)
    with sqlite3.connect("provider_data.db") as conn:
        result.to_sql("address_comparison", conn, if_exists="replace", index=False)
    print(result.tier.value_counts().to_string())


if __name__ == "__main__":
    main()
