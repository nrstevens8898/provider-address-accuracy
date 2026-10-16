# Provider Data Quality: Manhattan Psychiatrists

**Of 919 Manhattan psychiatrists listed in both NPPES and Medicare, 73% have a different building in each source.**
Most mismatches come from Medicare listing the group a doctor bills through, not where they see patients; a hand-check of 15 showed the cause predicts which source is right.
**[Read the memo →](memo.md)** for findings, fixes and an accuracy target. Every number is sourced in [memo_factpack.md](memo_factpack.md).

> The `data/` folder isn't included; run the scripts in order to regenerate it. The hand-check results contain real names and stay private.

## The question

When someone looks up a psychiatrist in Manhattan, is the practice address correct? There are two official government sources for doctors' addresses, and they don't always agree:

- **NPPES** (National Plan and Provider Enumeration System): the national registry where every U.S. healthcare provider gets an ID number, called an **NPI**. Providers enter and update their own information, and nobody forces them to keep it current.
- **Medicare's clinician file**: the list of clinicians enrolled in Medicare. Medicare requires providers to re-confirm their information periodically.

This project measures what share of Manhattan psychiatrists have a different practice address in NPPES than in Medicare, why, and which differences matter most. The full framing is in `framing.md`.

## Where things stand

| Step | Status |
|---|---|
| 1. Set up tools and database | Done |
| 2. Pull psychiatrists from NPPES | Done |
| 3. Pull the same providers from Medicare | Done |
| 4. Compare addresses | Done |
| 5. Explain why addresses differ | Done |
| 6. Hand-check a sample | Done |
| 7. Write the memo | Not started |

## Key numbers so far

| | Count |
|---|---|
| Providers pulled from NPPES (unique) | 4,332 |
| **Manhattan psychiatrists (our population)** | **2,819** |
| Of those, found in Medicare | 942 (33.4%) |
| Of those, missing from Medicare | 1,877 (66.6%) |
| Found in Medicare but with no Manhattan address there | 345 |
| Found in Medicare but can't be compared (unreadable address) | 23 |
| **Of the 919 comparable: Match** | **243 (26.4%)** |
| Of the 919 comparable: Minor (same building, different suite) | 10 (1.1%) |
| Of the 919 comparable: Major (different building) | 666 (72.5%) |

## Step 1: Set up tools and database

**What it does:** installs Python tools (pandas for tables of data, Jupyter for notebooks) in a private project folder, `.venv`, and creates an empty database file.

**What it produces:** `.venv/`, `requirements.txt` (the list of installed tools), and `provider_data.db`, a SQLite database that lives in a single file.

## Step 2: Pull psychiatrists from NPPES

**What it does:** downloads every provider from the NPPES website whose practice location is in a Manhattan ZIP code (10001–10299) and whose specialty mentions psychiatry, then narrows that to true Manhattan psychiatrists.

**Why by ZIP code:** the NPPES website returns at most 1,200 results per search, sorted alphabetically. A single search would only have reached names starting with A through about D, so we searched each ZIP code separately and combined the results.

**What was dropped, and why:**

| Dropped | Count | Why |
|---|---|---|
| Main office outside Manhattan | 641 | They list a Manhattan office only as a secondary location. Their main address is elsewhere (often another state), so comparing it to Medicare wouldn't answer a Manhattan question. 513 of them are psychiatrists, many apparently working for telehealth or multi-state groups. |
| Not a psychiatrist | 828 | The website's "Psychiatry" search also matches neurologists (psychiatry and neurology share one category) and people who list psychiatry only as a second specialty. |
| Borderline | 44 | Specialties a psychiatrist *or* a neurologist can hold (e.g. sleep medicine), trainees, nurse practitioners, or no specialty listed. Dropped for a clean definition; they're about 1.4% and wouldn't change results. |

**What it produces:**
- `data/raw/`: the website's original responses, saved untouched
- `data/population_npis.csv`: the 2,819 psychiatrists we study. This list is fixed for the rest of the project.
- `data/dropped_providers.csv`: everyone dropped, with the reason
- `data/nppes.csv` and database table **`nppes`**: one row per psychiatrist, with name, credential, specialty, main practice address, phone, the date their NPI was issued, and the date their record was last updated
- `data/nppes_secondary_locations.csv` and table **`nppes_secondary_locations`**: 696 extra practice locations for 407 of the psychiatrists, kept in case we need them later

## Step 3: Pull the same providers from Medicare

**What it does:** looks up each of the 2,819 psychiatrists in Medicare's clinician file by their NPI, and keeps every address Medicare lists for them, including ones outside Manhattan.

**Which data:** the CMS Doctors and Clinicians National Downloadable File, released 2026-09-10 (data as of 2026-08-18). Rather than download the whole 840 MB national file, we asked CMS's website for just our 2,819 NPIs, which returns the same rows.

**What we found:**
- Only **942 (33.4%)** are in Medicare's file. We predicted about 50%. To make sure this wasn't a bug, 25 of the "missing" providers were looked up again one at a time, and none were found.
- Most found providers have one Medicare address, but a few have dozens. Two telehealth psychiatrists list addresses in 13 and 15 states.
- 345 of the 942 have no Manhattan address in Medicare at all.

**Nothing was dropped in this step.** Providers not found in Medicare stay in the population and will be reported as "missing."

**What it produces:**
- `data/raw/medicare/`: CMS's original responses, saved untouched
- `data/medicare.csv` and database table **`medicare`**: 1,634 rows, one per provider, medical group and address combination

## Step 4: Compare addresses

**What it does:** for each of the 942 psychiatrists found in both sources, checks whether the NPPES main practice address is the same place as any of their Medicare addresses, and sorts them into a tier.

**How addresses are compared:** the same address is often written differently ("RM 5S" vs "SUITE 5S", "FIRST AVENUE" vs "1ST AVE", the suite on the first line vs the second line). So each address is cleaned up and split into two parts:
- the **building**: house number and street, e.g. `109 W 27TH ST`
- the **unit**: the suite, room or floor, e.g. `5S` or `FL12`

| Tier | Meaning | Count | Share of the 919 comparable |
|---|---|---|---|
| Match | Same building, and the same suite (or only one source lists a suite) | 243 | 26.4% |
| Minor | Same building, different suite | 10 | 1.1% |
| Major | No Medicare address is in the same building | 666 | 72.5% |
| Can't compare | NPPES address has no street number (e.g. "First Ave at 16th St"), or Medicare lists only a PO box | 23 | not in the rate |
| Missing | Not in Medicare (reported separately) | 1,877 | not in the rate |

**Why the cleanup matters:** 156 of the 243 Matches (64%) had different raw text. A plain text comparison would have called them mismatches.

**Checks on the result** (none of these change the tiers above):
- **If a suite listed in only one source counted as Minor** instead of Match, 43 providers would move from Match to Minor (Match 21.8%, Minor 5.8%). The Major rate stays 72.5%, so the headline doesn't depend on this rule.
- **Secondary locations:** for 48 of the 666 Majors, one of their *other* NPPES practice locations matches Medicare. Counting those would bring Major down to 67.2%. Most of the 48 are providers whose Medicare addresses are all outside Manhattan: Medicare is listing their other office.
- **Where the Majors are:**

| Where Medicare puts them | Majors | Share |
|---|---|---|
| Same hospital campus or same block (e.g. 1 Gustave Levy Pl vs 1425 Madison Ave, both Mount Sinai) | 51 | 7.7% |
| Elsewhere in Manhattan | 278 | 41.7% |
| Outside Manhattan | 337 | 50.6% |

  So about 9 in 10 Majors are a genuinely different place, not a near miss. 40 of the "elsewhere in Manhattan" group are NYU psychiatrists listed in Medicare at "New York University, 111 Broadway", an administrative address rather than a clinic.

**Judgment calls** (details in `decisions.md`, #13–22): a suite listed on only one side counts as a Match; two different Manhattan ZIPs are allowed for the same street address, because the Post Office renumbered some; streets with two official names (Malcolm X Blvd = Lenox Ave) count as the same street; "same campus" uses a written list of hospital campus addresses.

**What it produces:** `data/address_comparison.csv` and database table **`address_comparison`**: one row per psychiatrist (all 2,819) with their tier, the cleaned NPPES building and suite, the closest Medicare building and suite, how many Medicare addresses they have, and the check columns (`tier_strict_suite`, `secondary_tier`, `major_location`).

## Step 5: Explain why addresses differ

**What it does:** tests why 666 of the 919 comparable psychiatrists have a different building in NPPES than in Medicare. It checks the two ideas from `framing.md`, plus a third the data pointed to:

| Idea | If true, mismatches should be more common among… | What we found |
|---|---|---|
| **Staleness:** NPPES isn't kept up to date | providers who haven't updated NPPES in years | **No.** Records untouched for 10+ years mismatch the *least* (64%). Among solo providers, untouched for 5+ years: 39%; updated recently: 68%. A recent update often means a move, so Medicare may be the one lagging. |
| **Multiple locations:** each source lists a different real office | providers with several addresses | **Weakly.** Several addresses doesn't raise the rate, but for 48 providers a second NPPES office matches Medicare. |
| **Group address:** Medicare lists the address of the group a psychiatrist bills Medicare through | providers who bill through a group | **Yes, strongly.** No group: 52%. In a group: 77–87%. |

**Causes, ranked.** Each mismatch is assigned its most likely cause (first rule that fits):

| Cause | Mismatches | Share |
|---|---|---|
| Medicare lists a group site outside Manhattan (e.g. a multi-state telehealth group, a suburban hospital) | 245 | 36.8% |
| Medicare lists a group site elsewhere in Manhattan (e.g. a hospital system, NYU's administrative office) | 207 | 31.1% |
| Solo provider at a different address (probably moved; unknown which source is current) | 98 | 14.7% |
| Wrong building on the same medical campus | 49 | 7.4% |
| Medicare lists the provider's other office, which NPPES also lists | 48 | 7.2% |
| NPPES never updated since the provider got their NPI | 19 | 2.9% |

**What it means:** about two-thirds of mismatches come from Medicare listing the group a psychiatrist bills through, not from anyone forgetting to update. Both sources can be right at once. Which source is actually right for a given provider is the next step (hand-check).

**What it produces:** `analyze_causes.py`, plus `data/cause_analysis.csv` and database table **`cause_analysis`**: one row per comparable psychiatrist with years since NPPES update, group size, address counts, and the assigned cause for each mismatch.

## Step 6: Hand-check a sample

**What it does:** picks 15 mismatches at random to look up by hand (on provider, practice and hospital websites) and decide which source is actually right. The sample covers every cause from Step 5: 3 each from the three biggest causes and 2 each from the other three. It uses a fixed "seed" (42), a setting that makes the random draw come out the same every time.

**What it produces:** `draw_handcheck_sample.py` and `data/handcheck_sample.csv`. Each row has the provider's name, NPI, NPPES address, every Medicare address, Medicare group, and assigned cause, plus three empty columns to fill in: `correct_source`, `evidence_url`, `notes`.

**Results** (filled in by hand in `data/handcheck_results.csv`, counted by `tally_handcheck.py`):

| Which source was right | Count |
|---|---|
| Medicare | 5 |
| NPPES | 4 |
| Neither | 3 |
| Unclear | 3 |

- **Neither source is reliably right.** Which one is right depends on the cause.
- When Medicare listed a **group site elsewhere in Manhattan**, NPPES was right all 3 times: Medicare showed the group's address, not where the doctor works.
- When the provider had **moved away** (to Poughkeepsie, Pittsburgh, Cambridge), Medicare was right and NPPES still showed the old Manhattan address. Two of them had updated their NPPES record recently without fixing the address, so the "last updated" date can't be used to spot stale addresses.
- **5 of 15 practice mainly or partly by telehealth**, so for them a street address may not mean much.
- 15 cases is enough to show patterns, not to give a precise accuracy rate.

## Other files

| File | What's in it |
|---|---|
| `framing.md` | The question, scope, definitions, hypothesis and what success looks like |
| `decisions.md` | Every decision made so far, with a one-line reason |
| `notes.md` | Findings to use in the final memo |
| `memo_factpack.md` | Every number for the memo, each with its source; providers anonymized as Provider A, B, C… |
| `data/provider_key.csv` | Private key linking Provider A, B, C… to real NPIs and names. Don't share. |
| `*.py` | The scripts that do each step, so everything can be rerun |
