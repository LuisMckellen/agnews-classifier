# inspect_dup_titles.py
from src.load import load_corpus

df = load_corpus()

counts = df["title"].value_counts()
dupes = counts[counts > 1]

print(f"distinct duplicated titles: {len(dupes)}")
print(f"rows involved: {dupes.sum()}")
print("\ncount distribution:")
print(dupes.value_counts().sort_index().head(10))

# Tail = the long thin part, where syndication would live if it exists.
tail = dupes[dupes <= 3].index.to_series().sample(40, random_state=0)

for i, t in enumerate(tail, 1):
    rows = df[df["title"] == t]
    print(f"\n--- {i}. [{counts[t]}x] labels={sorted(rows['label'])} {t!r}")
    for d in rows["description"].head(2):
        print(f"    {d[:110]}")