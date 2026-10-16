# Problem Framing

## 1. Question
For psychiatrists in Manhattan, what % of providers have a different practice address in NPPES than in Medicare's clinician file, why, and which differences matter most?

## 2. Scope
All psychiatrists with a Manhattan practice ZIP, pulled by ZIP code from NPPES. Individual providers only, filter out organizations. Only count providers who appear on both sources in the mismatch rate, and report how many are missing from Medicare as its own number

## 3. Definition of "wrong"
Use the following tiers:
Match: same address, after cleanup (E/East, St/Street, Fl/Floor, ZIP+4)
Minor: same building, different suite
Major: Different address
Missing: the provider is on one source but not the other
Count it as a match so long as the NPPES address matches any of the Medicare ones, if more than one is listed. The reasoning is that a patient who shows up at any real location of the doctor still finds them.

## 4. Hypothesis
The sources disagree because they're updated in different timelines through different systems. Nobody is forced to update NPPES, but Medicare requires periodic revalidation. If staleness is the cause, mismatches should cluster among providers whose NPPES record hasn't been updated in years. You can check this, since NPPES shows a last-updated date. If multiple locations are the cause, mismatches should cluster among providers with several Medicare addresses. I expect that staleness will be bigger.


## 5. Success
The memo is useful if it allows the head of product to act on it tomorrow, by providing:
the mismatch rate, broken out by tier
the likely causes, ranked by how much they explain
for a hand-checked sample, which source was actually right
what you'd fix first, and the accuracy target you'd set
