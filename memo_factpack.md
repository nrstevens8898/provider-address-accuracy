# Memo Fact Pack: Manhattan Psychiatrists, NPPES vs Medicare Addresses

Every number that might go in the memo, with where it comes from. Providers are anonymized as Provider A, B, C… (the private key is `data/provider_key.csv`; don't share it).

**Source key**
- **Tables** are in `provider_data.db` (same data as the CSVs in `data/`).
- **Scripts:** `filter_nppes.py` (Step 2), `fetch_medicare.py` / `load_medicare.py` (Step 3), `compare_addresses.py` (Step 4), `analyze_causes.py` (Step 5), `draw_handcheck_sample.py` / `tally_handcheck.py` (Step 6).
- **Notes #** = finding number in `notes.md`. **Decision #** = row in `decisions.md`.

**Data versions**
- NPPES: pulled from the NPPES API on 2026-09-27.
- Medicare: CMS Doctors and Clinicians National Downloadable File (dataset `mj5m-pzi6`), released 2026-09-10, data as of 2026-08-18 (decision #12).

---

## 1. Population funnel

| Step | Count | Source |
|---|---|---|
| Unique providers pulled from NPPES (Manhattan practice ZIP 10001–10299, specialty search "Psychiatry") | 4,332 | `filter_nppes.py`; notes #1 |
| Dropped: main practice address outside Manhattan (Manhattan only a secondary location) | 641 | `data/dropped_providers.csv` (reason = main address outside Manhattan); decision #5 |
| Manhattan-based providers | 3,691 | decision #5 |
| Dropped: not a psychiatrist (mostly neurologists; 628 general neurology) | 828 | `data/dropped_providers.csv`; notes #1; decision #6 |
| Dropped: borderline (shared subspecialties, trainees, 2 nurse practitioners, no specialty) | 44 | `data/dropped_providers.csv`; decision #6 |
| **Study population: Manhattan psychiatrists** | **2,819** | `data/population_npis.csv`; table `nppes`; decision #8 |

Context numbers:

| Fact | Number | Source |
|---|---|---|
| Non-psychiatrists among Manhattan-based search results | 828 of 3,691 (22%) | notes #1 |
| Psychiatrists with any Manhattan practice location whose main address is elsewhere | 513 of 3,332 (15.4%) | notes #2 |
| …of those, practice locations in 3+ states | 262 of 513 (51%) | notes #2 |
| Largest shared main-address cluster among the 641 (Tallahassee, FL) | 28 providers | notes #2 |
| Psychiatrists in the population with extra NPPES practice locations | 407 (696 locations) | table `nppes_secondary_locations`; README Step 2 |
| Population members with a nurse-type credential (e.g. Provider L, PMHNP) using a psychiatrist specialty code | 7 | table `nppes`; notes #10 |

## 2. Medicare coverage

| Fact | Number | Source |
|---|---|---|
| Population found in Medicare's clinician file | 942 of 2,819 (33.4%) | table `medicare`; notes #4 |
| Not found ("Missing") | 1,877 (66.6%) | table `address_comparison` (tier = Missing); notes #4 |
| Predictions before pulling: mine / Claude's | 50% / 50–65% | notes #3 |
| "Missing" NPIs re-queried one at a time to rule out a bug | 25 checked, 0 found | notes #4 |
| Medicare rows (provider × group × address) | 1,634 | table `medicare`; README Step 3 |
| Found providers with exactly one Medicare address | 649 of 942 | notes #5 |
| Found providers with only Manhattan / Manhattan + elsewhere / no Manhattan address in Medicare | 508 / 89 / 345 | notes #5 |
| Most addresses for one provider (telehealth outliers) | Provider P: 63 addresses in 13 states; Provider Q: 58 in 15 | notes #5 |
| Medicare rows where CMS suppressed address line 2 (suite hidden) | 102 | table `medicare` (`ln_2_sprs` = Y); decision #14 |

Wording: 33.4% are *listed in Medicare's clinician file*, not necessarily *accepting Medicare* (notes #4).

## 3. Tier breakdown

Rule: Match if the NPPES main address matches **any** Medicare address (framing.md section 3).

### Headline tiers (decision #19)

| Tier | Providers | % of 919 comparable | Source |
|---|---|---|---|
| Match (same building; same suite, or suite in only one source) | 243 | 26.4% | table `address_comparison`; notes #6 |
| Minor (same building, different suite) | 10 | 1.1% | same |
| Major (different building) | 666 | 72.5% | same |
| **Comparable total** | **919** | 100% | |
| Can't compare (excluded from rate) | 23 | — | `cant_compare_reason` column; decision #19 |
| …NPPES address has no street number (e.g. "First Ave at 16th St") | 11 | — | same |
| …Medicare has only a PO box or blank | 12 | — | same |
| Missing from Medicare (excluded from rate) | 1,877 | — | notes #4 |

| Fact | Number | Source |
|---|---|---|
| Population with an NPPES address confirmed by Medicare | 243 of 2,819 (8.6%) | notes #6 |
| Matches that only match after address cleanup (raw text differed) | 156 of 243 (64%) | `compare_addresses.py`; notes #7; decision #13 |
| Same-building providers whose suites could be compared | 127 of 253 | notes #7 |
| …no suite in either source / suite in only one source | 83 / 43 | notes #7 |

### Suite sensitivity check (decision #20)
If "suite in only one source" counts as Minor instead of Match:

| Tier | Headline | Strict suite rule | Source |
|---|---|---|---|
| Match | 243 (26.4%) | 200 (21.8%) | column `tier_strict_suite`; notes #8 |
| Minor | 10 (1.1%) | 53 (5.8%) | same |
| Major | 666 (72.5%) | 666 (72.5%) | same |

The Major rate is unaffected; only 43 providers move from Match to Minor.

### Secondary-location check (decision #21; main tiers unchanged)

| Fact | Number | Source |
|---|---|---|
| Majors with any NPPES secondary location | 156 of 666 | column `secondary_tier`; notes #8 |
| …a secondary location matches Medicare | 48 (46 Match, 2 Minor) | same |
| Major rate if secondary locations counted | 618 of 919 (67.2%) | notes #8 |
| Of the 48, Medicare addresses all outside Manhattan | 37 | notes #8 |

### Where the Majors are (decision #22)

| Location of Medicare address | Majors | % of 666 | Source |
|---|---|---|---|
| Same campus (same block, or known hospital campus) | 51 | 7.7% | column `major_location`; notes #8 |
| Elsewhere in Manhattan | 278 | 41.7% | same |
| Outside Manhattan | 337 | 50.6% | same |

Same-campus detail: Columbia/NYP Washington Heights 25, Mount Sinai East Harlem 17, same block 8, Weill Cornell 1 (column `same_campus_reason`; notes #8). Of the 278 elsewhere in Manhattan, 40 are listed in Medicare at "New York University, 111 Broadway", an administrative address (53 population members in total are listed there; notes #8).

## 4. Causes

All rates are on the 919 comparable providers; source `analyze_causes.py`, table `cause_analysis`, notes #9.

### Hypothesis tests

**Staleness: Major rate by years since NPPES `last_updated`** (to 2026-08-18)

| Since last update | Providers | Major % |
|---|---|---|
| < 2 years | 354 | 73.4% |
| 2–5 years | 207 | 76.8% |
| 5–10 years | 111 | 80.2% |
| 10+ years | 247 | 64.0% |

| Fact | Number | Source |
|---|---|---|
| Solo providers, NPPES updated < 5 yrs vs 5+ yrs | 67.7% vs 38.8% Major (p = 0.00002) | notes #9 |
| NPPES never updated since NPI issued | 19 providers, all Major | notes #9 |
| Hand-checked movers whose NPPES was updated in Jul–Aug 2026 without fixing the address | 2 (Providers C and I) | notes #9 correction, #11; decision #27 |

**Multiple locations**

| Measure | Major % | Source |
|---|---|---|
| 1 / 2 / 3–5 / 6+ Medicare addresses | 73.6% / 71.3% / 68.6% / 64.7% (643 / 157 / 102 / 17 providers) | notes #9 |
| NPPES secondary locations: none vs some | 72.2% vs 73.2% | notes #9 |

**Group address** (size of the Medicare group the provider bills through, `num_org_mem`)

| Group | Providers | Major % | Source |
|---|---|---|---|
| No group | 217 | 51.6% | notes #9 |
| Group < 100 | 148 | 87.2% | same |
| Group 100+ | 554 | 76.7% | same |
| Group vs none | | p < 1e-12 | same |

### Ranked causes of the 666 Majors (first matching rule wins, decision #24)

| Rank | Cause | Majors | % of Majors |
|---|---|---|---|
| 1 | Medicare lists a group site outside Manhattan | 245 | 36.8% |
| 2 | Medicare lists a group site elsewhere in Manhattan | 207 | 31.1% |
| 3 | Solo provider, different address | 98 | 14.7% |
| 4 | Wrong building, same medical center | 49 | 7.4% |
| 5 | Medicare lists the provider's other NPPES-listed practice | 48 | 7.2% |
| 6 | NPPES never updated since NPI issued | 19 | 2.9% |

Group addresses (ranks 1 + 2): 452 of 666 (67.9%). Including the group members that earlier rules claimed first, 554 of 666 (83.2%) bill through a group (table `cause_analysis`, `group_size > 0`). (This 554 is Majors in a group of any size; it's a coincidence that it equals the 554 providers in groups of 100+ above.)

Organizations behind most Majors: Icahn/Mount Sinai, NYU, Columbia, Weill Cornell, Northwell (North Shore-LIJ), Physician Affiliate Group of NY, Montefiore, and multi-state "MCCD" psychiatry groups (notes #9).

## 5. Hand-check results

15 Majors, random sample with seed 42, 2–3 per cause (`draw_handcheck_sample.py`; decision #25). Checked by hand against provider, practice and hospital websites (`data/handcheck_results.csv`; `tally_handcheck.py`; notes #11).

| Correct source | Count |
|---|---|
| Medicare | 5 |
| NPPES | 4 |
| Neither | 3 |
| Unclear | 3 |

| Cause | Checked | NPPES | Medicare | Neither | Unclear |
|---|---|---|---|---|---|
| Group site outside Manhattan | 3 | 0 | 2 | 1 | 0 |
| Group site elsewhere in Manhattan | 3 | 3 | 0 | 0 | 0 |
| Solo, different address | 3 | 1 | 2 | 0 | 0 |
| Medicare lists their other NPPES office | 2 | 0 | 0 | 0 | 2 |
| NPPES never updated | 2 | 0 | 1 | 1 | 0 |
| Same medical center | 2 | 0 | 0 | 1 | 1 |

| Pattern | Number | Providers |
|---|---|---|
| Group site in Manhattan: NPPES right | 3 of 3 | D, E, F |
| Medicare-right cases where the provider moved away from Manhattan | 3 of 5 | A (Poughkeepsie), C (Pittsburgh), I (Cambridge, MA) |
| Practice mainly or partly by telehealth | 5 of 15 | B, J, K, L, O |
| Medicare right, but only one of several Medicare addresses | 2 | C (1 of 6), M (1 of 3) |
| Same-campus cases where clinical practice location was unclear or virtual | 2 of 2 | N, O |

On MCCD: Providers J and K are both billed under "MCCD FL Psychiatry Services" and listed at 109 W 27th St, and both have profiles on the same telehealth company's website. That suggests a link, but it is 2 cases and **not confirmed**; don't state who operates the MCCD groups.

## 6. Limitations

| Limitation | Detail | Source |
|---|---|---|
| Hand-check is small | n = 15, 2–3 per cause; shows patterns, not a precise accuracy rate per source or cause. Not weighted by cause size. | notes #11; decision #25 |
| Cause ranking depends on rule order | Each Major gets the first matching cause (a → f). Ranked this way, group addresses explain 67.9%; 83.2% of Majors bill through a group, but 102 of them were assigned to earlier rules (47 to "other NPPES office", 43 to "same medical center", 12 to "never updated"). Attributions are patterns, not proof. | decision #24; table `cause_analysis` |
| "Missing" is one direction only | We checked NPPES psychiatrists against Medicare, not Medicare-listed Manhattan psychiatrists against NPPES. "Missing" means not in Medicare's file (opt-out, never enrolled, trainee, retired, stale NPPES record), not necessarily an error. The 33.4% is "listed", not "accepts Medicare". | notes #4; framing.md section 2 |
| Evidence quality varies | Hand-check sources range from hospital and practice profiles to a US News listing (Provider H) and LinkedIn (Provider L). Websites can be out of date too. One reviewer, no second check. | `data/handcheck_results.csv` |
| Staleness can't be measured directly | NPPES `last_updated` changes when any field changes, so it doesn't show whether the address is current (Providers C and I). Medicare has no address date. | notes #9 correction; decision #27 |
| Telehealth | For telehealth-heavy providers (5 of 15 in the sample), a "correct" street address may not exist. | notes #11 |
| Address-matching rules are judgment calls | Cleanup rules, "match any Medicare address", any two Manhattan ZIPs allowed for the same street address, hand-written campus address lists. 11 + 12 addresses can't be parsed. | decisions #13–19, #22 |
| Only the NPPES main address is used for the headline | Secondary locations would lower Major from 72.5% to 67.2%. | decisions #10, #21 |
| Population definition | Fixed 2,819 based on NPPES specialty codes; includes 7 nurse-type credentials; drops 641 providers based outside Manhattan. | decisions #5, #6, #8; notes #10 |
| Snapshot in time | Medicare data as of 2026-08-18; NPPES pulled 2026-09-27. | decision #12 |
