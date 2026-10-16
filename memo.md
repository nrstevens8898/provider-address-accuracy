# Provider Data Quality Memo: Where do Manhattan psychiatrists actually practice?

*When someone looks up a psychiatrist in Manhattan, can they trust that the doctor actually practices there, at the address listed?*

**Neither NPPES nor Medicare is reliably right about where Manhattan psychiatrists practice. But the reason they disagree predicts which one to trust.**

## What I found

Only about 1 in 3 Manhattan psychiatrists in NPPES appear in Medicare’s clinician file at all. That isn’t an error, since many psychiatrists don’t take Medicare. But of the ones in both, nearly 3 in 4 list a different building in each source. About half of those put the doctor outside Manhattan entirely.

I expected stale data to be the main cause. At first the data said otherwise. Records untouched for 10+ years agreed more often, which makes sense, since a doctor who hasn’t moved has nothing to update. The biggest driver was different. About two-thirds of mismatches come from Medicare listing the site of the group a doctor bills through, not where they see patients.

Then the hand-check changed my view again. Staleness is real. It’s just invisible in the data. The cause of each mismatch predicted which source was right:

- Out of 15 mismatches: Medicare right 5, NPPES right 4, neither 3, unclear 3.
- When Medicare listed a group site elsewhere in Manhattan, NPPES was right 3 of 3.
- 3 of the 5 cases where Medicare was right were doctors who had moved away. 2 of them had updated their NPPES record recently without changing the address, so “last updated” can’t detect a stale address.
- 5 of 15 practice mainly or partly by telehealth, where a street address may not mean much.

## What I’d fix first

1. **Don’t treat Medicare group addresses as practice locations.** When Medicare lists a group site and NPPES lists the doctor’s own address, show NPPES. Keep the group as “affiliated with,” not “practices at.” This covers about 200 mismatches, and NPPES was right 3 of 3 times in the hand-check.
2. **Flag likely movers for verification.** If NPPES says Manhattan and Medicare has no Manhattan address, don’t show the address as confirmed. Check it against a third source: the practice website, booking sites, or a phone call.
3. **Mark telehealth providers as virtual** instead of forcing a street address.

Fix 1 comes first because it’s a simple rule with the clearest evidence. Fix 2 prevents the most harm, but it needs a verification process to work.

## Accuracy target

- **Metric:** % of listed addresses verified as a place the doctor sees patients, or correctly marked virtual.
- **Baseline:** trusting one source gets roughly half right: the 26% where the sources agree, plus about 1 in 3 of the rest. This is rough. It assumes agreeing records are correct and rests on 15 hand-checks.
- **Target:** 70%+ from Fixes 1 and 3, and 90% once verification is running. I’d check these against existing industry benchmarks before committing.
- **How to measure:** hand-check a random 50 providers each month, including records where the sources agree.

## How I did it

I pulled 2,819 psychiatrists with a main practice address in Manhattan from NPPES and matched them to Medicare by NPI. 942 were in Medicare, and 919 had addresses I could compare. After cleaning up formatting differences like “St” vs. “Street,” 26% matched, 1% were the same building with a different suite, and 73% were a different building. I then hand-checked 15 mismatches, sampled across each cause, against practice and hospital websites.

## Limitations

- The hand-check is 15 cases: directional, not a precise rate.
- Manhattan psychiatry only.
- “In Medicare’s file” isn’t the same as “accepts Medicare.”
- Cause ranking depends on the order rules were applied.
