"""
Four cheap checks: markup, repair-on-markup, vocab_size, A-C and B-D.

Run from the repo root:  python audit.py
"""

import re
import json
import sys
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

from src.clean import repair            # adjust if your package path differs

# --- config ------------------------------------------------------------
CSV = "data/train.csv"
JSONL = "results/corruption_2x2.jsonl"
SEP = " "                               # title/description join separator
# -----------------------------------------------------------------------

# --- load: AG News ships headerless, 3 columns -------------------------
df = pd.read_csv(CSV, header=None, names=["label", "title", "description"])

# schema check before anything else
print("=== schema ===")
print("shape:", df.shape)
print("columns:", df.columns.tolist())
print("label values:", sorted(df["label"].unique()))
print(df.head(2).to_string())
if len(df) != 120000:
    print(f"\n!! expected 120000 rows, got {len(df)}. Stop and check header=None.")
    sys.exit(1)

df["text"] = df["title"].astype(str) + SEP + df["description"].astype(str)
s = df["text"]

# --- patterns: import from clean.py if you can, don't retype -----------
try:
    from src.clean import BARE_NUM, BARE_NAMED, INTACT
    print("\n(using patterns imported from src.clean)")
except ImportError:
    print("\n!! patterns retyped here — two definitions of CORRUPT (METHOD 19)."
          "\n   Move them into src/clean.py and import instead.")
    BARE_NUM = re.compile(r"#\d{2,4};")
    BARE_NAMED = re.compile(r"(?:lt|gt|quot|amp|nbsp|apos);")
    INTACT = re.compile(r"&(?:#\d+|\w+);")

MARKUP = re.compile(r"&lt;\s*/?[A-Za-z]")

# --- 1. is the markup already counted? ---------------------------------
has_markup = s.str.contains(MARKUP)
in_named = s.str.contains(BARE_NAMED)
in_intact = s.str.contains(INTACT)
any_bare = s.str.contains(BARE_NUM) | in_named

print("\n=== markup ===")
print("rows with markup:", int(has_markup.sum()))
print("  also matched by bare_named:", int((has_markup & in_named).sum()))
print("  also matched by intact    :", int((has_markup & in_intact).sum()))
print("  matched by NEITHER        :",
      int((has_markup & ~in_named & ~in_intact).sum()))
print("markup as % of corpus:", round(100 * has_markup.mean(), 3))
print("\nsanity — any bare rows:", int(any_bare.sum()),
      "(should be 38,678)")

print("\nmarkup rate by class:")
print(df.assign(m=has_markup).groupby("label")["m"].mean().round(4).to_string())

print("\nDecision: a few hundred -> strip in clean.py, no experiment."
      "\n          several thousand -> pre-register repair vs repair+strip.")

# --- 2. what repair does to a markup row -------------------------------
print("\n=== repair on markup ===")
if has_markup.any():
    for ex in s[has_markup].head(2):
        print("before:", ex[:150])
        print("after :", repair(ex)[:150])
        print("-")
else:
    print("no markup rows found — check the MARKUP pattern against a raw row")

# --- 3. vocab_size: dirty minus repaired -------------------------------
print("\n=== vocab_size ===")
v_dirty = TfidfVectorizer().fit(s)
v_clean = TfidfVectorizer().fit(s.map(repair))
d, c = len(v_dirty.vocabulary_), len(v_clean.vocabulary_)
print(f"dirty {d}  repaired {c}  diff {d - c}")
gone = sorted(set(v_dirty.vocabulary_) - set(v_clean.vocabulary_))
added = sorted(set(v_clean.vocabulary_) - set(v_dirty.vocabulary_))
print(f"lost {len(gone)}: {gone[:20]}")
print(f"gained {len(added)}: {added[:20]}")
print("\nExpected ~1 net ('39' leaves). A larger diff means repair changes"
      "\nmore than the apostrophe — read the lists before publishing anything.")

# --- 4. the two missing 2x2 contrasts ----------------------------------
print("\n=== A-C and B-D, paired ===")
try:
    rows = [json.loads(l) for l in open(JSONL)]
except FileNotFoundError:
    print(f"no {JSONL} — skip")
    rows = []

if rows:
    print("first record keys:", list(rows[0].keys()))
    cells = {}
    for r in rows:
        cells.setdefault((r["train"], r["test"]), {})[r["seed"]] = r["macro_f1"]
    print("cells found:", list(cells.keys()))

    def paired(k1, k2, name):
        if k1 not in cells or k2 not in cells:
            print(f"{name}: missing cell — check key spelling")
            return
        seeds = sorted(set(cells[k1]) & set(cells[k2]))
        if len(seeds) < 2:
            print(f"{name}: only {len(seeds)} shared seeds")
            return
        ds = [cells[k1][x] - cells[k2][x] for x in seeds]
        mean = sum(ds) / len(ds)
        sd = (sum((v - mean) ** 2 for v in ds) / (len(ds) - 1)) ** 0.5
        neg, pos = sum(v < 0 for v in ds), sum(v > 0 for v in ds)
        print(f"{name}: mean {mean:+.4f}  sd {sd:.4f}  "
              f"majority sign {max(neg, pos)}/{len(ds)}  (neg {neg} pos {pos})")
        if sd and abs(mean) < sd / len(ds) ** 0.5:
            print("   ^ mean inside its own standard error — read the sign count")

    paired(("dirty", "dirty"), ("repaired", "dirty"), "A-C  (train side, dirty test)")
    paired(("dirty", "repaired"), ("repaired", "repaired"), "B-D  (train side, repaired test)")
    print("\nExpected from marginals: A-C ~ -0.0037, B-D ~ 0.0000."
          "\nA mismatch means the marginals and the per-seed data disagree.")