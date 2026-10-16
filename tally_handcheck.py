"""Step 6: tally the hand-checked sample (data/handcheck_results.csv, exported from Numbers):
which source was right, overall and by assigned cause."""
import pandas as pd

SOURCES = ["NPPES", "Medicare", "Both", "Neither", "Unclear"]

df = pd.read_csv("data/handcheck_results.csv", dtype=str)
df["correct_source"] = df.correct_source.str.strip()

print("== Which source was right (all 15)")
overall = df.correct_source.value_counts().reindex(SOURCES, fill_value=0)
print(overall[overall > 0].to_string())

print("\n== By assigned cause")
by_cause = pd.crosstab(df.assigned_cause, df.correct_source, margins=True, margins_name="Total")
print(by_cause[[s for s in SOURCES if s in by_cause] + ["Total"]].to_string())
