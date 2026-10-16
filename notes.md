# Notes for the Memo

## 1. The NPPES "Psychiatry" search returns many non-psychiatrists
The API's "Psychiatry" search returned 828 non-psychiatrists out of 3,691 Manhattan-based results (22%; 19% of all 4,332 pulled), because it matches the shared Psychiatry & Neurology group and secondary specialties. Most were neurologists (628 general neurology alone).

## 2. 15% of psychiatrists with a Manhattan office are based elsewhere, many likely telehealth or multi-state groups
513 psychiatrists list a Manhattan practice location only as a secondary location, with their main address elsewhere: 15.4% of the 3,332 psychiatrists with any Manhattan practice location (2,819 Manhattan-based + 513). Including non-psychiatrists, the count is 641 of 4,332 pulled providers (top main-address states: NY outside Manhattan 93, CA 81, FL 61, TX 54, NJ 53). All were excluded from the population (decision #5).
- 283 of the 641 (44%) list practice locations in 3+ states; among the 513 psychiatrists, 262 (51%). Max: 12 states, 17 secondary locations.
- Main addresses cluster: 129 of the 641 share a main address with 4+ others. Top clusters: 101 N Monroe St, Tallahassee FL (28, entered with and without "Ste 800"); 3223 S Loop 289, Lubbock TX (25, same issue); 100 Pine St, San Francisco CA (15); 1 W Winter St, Delaware OH (13); 1301 Riverplace Blvd, Jacksonville FL (10).
- Pattern is consistent with telehealth companies or multi-state groups registering a corporate address as the main location, but NPPES doesn't record the employer, so this is not confirmed. Not every cluster is telehealth (e.g. 300 Pasteur Dr, Stanford CA is an academic hospital).
- Memo implication: a patient searching NPPES for a Manhattan psychiatrist could land on a provider whose Manhattan "location" may be nominal. Worth a hand-check of a few if time allows.

## 3. Prediction before pulling Medicare (recorded 2026-09-27, before any results)
Share of the 2,819 NPPES psychiatrists expected to appear in the Medicare clinician file:
- My prediction: 50%.
- Claude's prediction: 50–65% (about 1,400–1,850), reasoning that psychiatry has one of the highest Medicare opt-out rates and Manhattan has many cash-only practices; trainees, retired/moved providers, and stale NPPES records also won't be in Medicare.

## 4. Only a third of Manhattan psychiatrists in NPPES appear in Medicare's clinician file
942 of 2,819 (33.4%) were found in the Medicare Doctors and Clinicians file (release 2026-09-10); 1,877 (66.6%) are missing. Both predictions were too high (mine: 50%; Claude's: 50–65%).
- Verified not a query bug: 25 randomly chosen "missing" NPIs re-queried one at a time; none were found.
- Why is still unknown. Candidate explanations to test: Medicare opt-out (common in psychiatry and Manhattan cash-pay practice), trainees, retired/moved providers, stale NPPES records.
- Memo implication: the mismatch rate will be based on only a third of the population; the missing number is itself a headline.
- My 50% prediction assumed a much larger share of Manhattan psychiatrists take Medicare. The data suggests only about a third (33%) do. Wording for the memo: 33% are *listed in Medicare's clinician file*, which isn't exactly the same as "accept Medicare". Some listed providers may not take new Medicare patients, and the 2,819 include trainees, retired providers and stale NPPES records, so the share among actively practicing psychiatrists could differ.

## 5. Among those found, 37% have no Manhattan address in Medicare at all
Of the 942 found: 508 list only Manhattan addresses, 89 list Manhattan plus elsewhere, and 345 (37%) list no Manhattan address. These are likely Major mismatches, pending address matching.
- Most have one Medicare address (649 of 942), but a few have many. Two outliers, Provider P (63 addresses, 13 states) and Provider Q (58 addresses, 15 states), are flagged as telehealth in Medicare, echoing finding #2. Under the "match any Medicare address" rule, these providers get many chances to match.

## 6. Of the 919 comparable providers, 72.5% list a different building in NPPES than in Medicare
Tiers (Step 4, `address_comparison` table), matching the NPPES main address against any Medicare address. Of the 942 found in Medicare, 23 can't be compared and are excluded from the rate (decision #19): 11 NPPES addresses have no street number (cross streets like "First Ave at 16th St", or just "Wards Island"), and 12 providers' only Medicare addresses are a bare PO box or blank.
- Match: 243 (26.4%); Minor (same building, different suite): 10 (1.1%); Major (different building): 666 (72.5%).
- Of the 666 Major: 337 have no Manhattan address in Medicare at all; 329 have a Manhattan address in Medicare, but a different building (see #8 for where).
- Measured against all 2,819 psychiatrists, only 243 (8.6%) have an NPPES address confirmed by Medicare.
- Both predictions and the hypothesis are about *why*; that's the next step (staleness via `last_updated`, multiple locations via `n_medicare_addresses`).

## 7. Most matches only match after cleanup
156 of 243 matches (64%) had different raw text, e.g. "109 W 27TH ST RM 5S" vs "109 W 27TH ST / 5S", "253 SOUTH ST" vs "253 S ST". Medicare also has a formatting quirk: floor 11 is stored as "FL" at the end of line 1 plus "SUITE 11" on line 2. Memo implication: any directory that compares addresses as plain text will hugely overstate mismatches.
- Suites could be compared for only 127 of the 253 same-building providers: 83 have no suite in either source, and 43 have a suite in only one source (13 of them because Medicare suppressed line 2).
- One Minor (Provider R, 525 E 68th St "# 140" vs Medicare "Box 171 / Suite 1228") is probably a hospital mailbox number, not a suite. Check in the hand-checked sample.

## 8. Robustness checks on the tiers (2026-10-05)
**Suite sensitivity.** If "suite in only one source" counts as Minor instead of Match, 43 providers move: Match 200 (21.8%), Minor 53 (5.8%), Major 666 (72.5%). The Major rate doesn't change, so the headline is not sensitive to this rule; only the Match/Minor split is.

**NPPES secondary locations.** 156 of the 666 Majors list secondary practice locations in NPPES. For 48 of them, a secondary location matches a Medicare address (46 Match, 2 Minor); 108 still don't match; 510 have no secondary location. If secondary locations counted, Major would fall from 666 to 618 (72.5% to 67.2%). Main tiers unchanged (decision #21).
- 37 of the 48 are Majors whose Medicare addresses are all outside Manhattan: Medicare lists their *other* practice, which NPPES also knows about but not as the main address. This is direct evidence for the multiple-locations explanation, to weigh in the next step.

**Where the Majors are.** Of the 666 Majors:

| Where Medicare puts them | Majors | Share |
|---|---|---|
| Same campus (same block, or a known hospital campus) | 51 | 7.7% |
| Elsewhere in Manhattan | 278 | 41.7% |
| Outside Manhattan | 337 | 50.6% |

- Same campus breakdown: Columbia/NYP Washington Heights 25, Mount Sinai East Harlem 17, same block 8 (7 of them hospital campuses such as 530 vs 550 1st Ave; one, 333 vs 320 Central Park W, is neighboring buildings), Weill Cornell 1. For these, a patient would at least end up at the right medical center.
- 40 of the 278 "elsewhere in Manhattan" are NYU psychiatrists whose Medicare address is "New York University, 111 Broadway" (53 of our psychiatrists are listed there in total). That's a downtown administrative address, not a clinic, so here Medicare is the source with the non-clinical address.
- Memo implication: about 9 in 10 Majors are a genuinely different place (another neighborhood or another state), not a near miss.

## 9. Why addresses differ: mostly because Medicare lists the group a psychiatrist bills through, not staleness (Step 5)
Neither hypothesis in framing.md held up as stated (`analyze_causes.py`, table `cause_analysis`).

**Staleness (my expected main cause): not supported for NPPES.** Records not updated in 10+ years have the *lowest* Major rate (64.0%, vs 73.4% for < 2 yrs, 76.8% for 2-5, 80.2% for 5-10). The clearest test is solo providers (no Medicare group, so Medicare's address comes from the provider): not updated in 5+ years → 38.8% Major; updated in the last 5 years → 67.7% (p = 0.00002). Likely reading: providers who haven't moved have no reason to update and both sources still agree; a recent NPPES update often means a move, and Medicare may be the source that lags. Which source is right is for the hand-check.
- Pure NPPES staleness is real but small: all 19 providers whose NPPES record was never updated after their NPI was issued are Major, but that's 2.9% of Majors.

**Multiple locations: weak as measured.** More Medicare addresses goes with slightly *fewer* Majors (73.6% for 1 address, 64.7% for 6+), partly because "match any address" gives them more chances to match. Having NPPES secondary locations makes no difference (73.2% vs 72.2%). But secondary locations do explain 48 Majors directly (#8).

**Group address: the strongest signal.** Major rate is 51.6% for providers with no Medicare group, 87.2% in groups under 100, 76.7% in groups of 100+ (group vs none, p < 0.000000000001). Majors are mostly listed under large hospital/university groups (Icahn/Mount Sinai, NYU, Columbia, Weill Cornell, Northwell, Physician Affiliate Group of NY, Montefiore) or the multi-state "MCCD" psychiatry groups (FL, NJ, CA, NY entities; the Tallahassee address cluster in #2). Medicare lists a provider at the practice sites of the group they bill Medicare through, which may not be their main practice. Both sources can be "right" at once.

**Causes ranked** (each Major assigned to its first matching cause, decision #24):

| Cause | Majors | % of Majors |
|---|---|---|
| Medicare lists a group site outside Manhattan | 245 | 36.8% |
| Medicare lists a group site elsewhere in Manhattan (incl. NYU's 111 Broadway admin address) | 207 | 31.1% |
| Solo provider, different address (likely a move; which source is current unknown) | 98 | 14.7% |
| Wrong building, same medical center | 49 | 7.4% |
| Medicare lists the provider's other NPPES-listed practice | 48 | 7.2% |
| NPPES never updated since NPI issued | 19 | 2.9% |

- About two-thirds (68%) of Majors trace to group billing addresses. Memo implication: comparing NPPES to Medicare mostly measures "where you bill Medicare" vs "where you say you practice", not errors. A directory fix would weight the individual's own listing (NPPES, or Medicare when solo) over group-level Medicare addresses, and treat group addresses as "affiliated sites".
- Caveat: these are patterns, not verified errors. The hand-checked sample should cover each cause.
- **Correction after the hand-check (#11):** "not staleness" is too strong. In the sample, 3 of 5 cases where Medicare was right are providers who moved away from Manhattan while NPPES still lists the old address. Two of them (Providers C and I) updated their NPPES record in Jul–Aug 2026 without changing the address. So `last_updated` doesn't measure whether the *address* is current, and this test can't rule NPPES staleness out.

## 10. Some "psychiatrists" are nurse practitioners using the psychiatrist specialty code
Found while drawing the hand-check sample: Provider L has credential PMHNP (psychiatric nurse practitioner) but lists the physician specialty code 2084P0800X (Psychiatry) in NPPES, so the specialty filter kept her. 7 providers in the 2,819 have a nurse-type credential. Not removed, since the population is fixed (decision #8). Memo implication: NPPES specialty codes are self-reported and not always checked against credentials.

## 11. Hand-check: neither source is reliably right; the cause predicts which one is (Step 6)
15 Majors checked by hand against provider, practice and hospital websites (`data/handcheck_results.csv`, tallied by `tally_handcheck.py`).

| Correct source | Count |
|---|---|
| Medicare | 5 |
| NPPES | 4 |
| Neither | 3 |
| Unclear | 3 |

By cause:

| Cause | Checked | Result |
|---|---|---|
| d. Group site outside Manhattan | 3 | Medicare 2, Neither 1 |
| e. Group site elsewhere in Manhattan | 3 | NPPES 3 |
| f. Solo, different address | 3 | Medicare 2, NPPES 1 |
| a. Medicare lists their other NPPES office | 2 | Unclear 2 |
| b. NPPES never updated | 2 | Medicare 1, Neither 1 |
| c. Same medical center | 2 | Unclear 1, Neither 1 |

Patterns:
- **Group site in Manhattan (e): NPPES right 3 of 3.** Medicare listed the group's site, not where the psychiatrist works. Both Physician Affiliate Group of NY doctors are listed at 506 Lenox Ave (Harlem Hospital), but one works at Metropolitan Hospital and one at 360 W 34th St.
- **Moves away from Manhattan: NPPES is the stale one.** 3 of the 5 Medicare-right cases moved: Provider A to Poughkeepsie, Provider C to Pittsburgh, Provider I to Cambridge, MA. NPPES still shows Manhattan, even though Providers C and I updated their NPPES records in Jul–Aug 2026. Revises finding #9: NPPES staleness is real, but `last_updated` can't detect it.
- **Telehealth makes "correct address" ill-defined.** 5 of 15 practice mainly or partly remotely: Providers J and K through a telehealth company, Provider B remotely from Florida, Provider O virtually for Florida patients, and Provider L possibly abroad. Providers J and K are both billed under "MCCD FL Psychiatry Services" and listed at 109 W 27th St, and both have profiles on the same telehealth company's website. That suggests a link between the MCCD groups, that address and the company, but it is 2 cases and not confirmed.
- **When Medicare was right, sometimes only one of its addresses was** (Provider C: 1 of 6; Provider M: 1 of 3). Under "match any" that counts as Medicare right, but a directory showing all of them would still mislead.
- **Same-campus cases (c)** were both Mount Sinai faculty whose clinical practice is unclear or virtual. Neither the campus building nor the alternative was clearly where they see patients.
- Caveats: 15 cases (2–3 per cause) is directional, not a precise accuracy rate. Some evidence is weaker (US News listing, LinkedIn).

Memo implications:
- Don't pick one source as the truth. NPPES is better for hospital-employed psychiatrists that Medicare lists at a group site. Medicare is better for providers who moved away.
- Flag telehealth-only providers separately; a street address may not apply to them.
