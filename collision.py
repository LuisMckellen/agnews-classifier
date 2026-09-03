"""
Queue items 1-4 and 7. Run from repo root: python collision_audit.py

Produces:
  - the 38,679 vs 38,678 reconciliation
  - repr() on the tokens repair creates
  - document-frequency residuals per suspect token  <- the collision table
  - why lt/gt/amp survived repair
  - a census of cells in the 2x2 JSONL
"""

import json
import re
from collections import Counter

import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer

from src.data import load_train, SEP
from src.clean import repair

JSONL = "results/corruption_2x2.jsonl"

df = load_train()
s = df["text"]
s_rep = s.map(repair)

# --- 1. reconcile the corruption count ---------------------------------
# The appendix figure was computed on some concatenation. If SEP differs,
# an entity spanning the join boundary appears or disappears.
BARE_NUM = re.compile(r"#\d{2,4};")
BARE_NAMED = re.compile(r"(?:lt|gt|quot|amp|nbsp|apos);")

print("=== reconciliation ===")
for sep in [" ", "", ". ", " . ", "\n"]:
    t = df["title"].astype(str) + sep + df["description"].astype(str)
    n = (t.str.contains(BARE_NUM) | t.str.contains(BARE_NAMED)).sum()
    mark = "  <-- current SEP" if sep == SEP else ""
    print(f"  SEP={sep!r:6} any_bare={n}{mark}")
print("appendix says 38,678. Whichever SEP reproduces it is the one that")
print("generated the appendix — adopt it in data.py or re-run the appendix.")

# --- 2. what repair creates: encoding or real? -------------------------
print("\n=== tokens repair creates ===")
tok = CountVectorizer().build_analyzer()
v_dirty = CountVectorizer().fit(s)
v_clean = CountVectorizer().fit(s_rep)
gained = sorted(set(v_clean.vocabulary_) - set(v_dirty.vocabulary_))
lost = sorted(set(v_dirty.vocabulary_) - set(v_clean.vocabulary_))
print("gained:", [(g, repr(g)) for g in gained[:20]])
print("lost  :", [(l, repr(l)) for l in lost[:20]])
print("\nIf repr() shows escapes like '\\xe2', the console mangled them and")
print("they are real tokens. If they look like plain words, it was display.")

# show a source row for each gained token
for g in gained[:5]:
    hit = s_rep[s_rep.str.contains(re.escape(g), regex=True)]
    if len(hit):
        i = hit.index[0]
        print(f"\n  {g!r} first appears in row {i}")
        print("    dirty   :", repr(s[i][:120]))
        print("    repaired:", repr(s_rep[i][:120]))

# --- 3. the collision table --------------------------------------------
SUSPECTS = ["39", "36", "151", "146", "147", "148", "160", "133", "145",
            "149", "38", "37", "lt", "gt", "amp", "quot", "nbsp", "apos"]

print("\n=== collision table (document frequency) ===")
print(f"{'token':8} {'dirty_df':>9} {'residual':>9} {'ratio':>7}  verdict")

def doc_freq(series, token):
    pat = r"\b" + re.escape(token) + r"\b"
    return int(series.str.contains(pat, regex=True).sum())

rows = []
for t in SUSPECTS:
    d = doc_freq(s, t)
    r = doc_freq(s_rep, t)
    ratio = r / d if d else float("nan")
    if d == 0:
        verdict = "absent"
    elif r == 0:
        verdict = "pure artifact"
    elif ratio > 0.95:
        verdict = "untouched"
    else:
        verdict = "COLLISION"
    rows.append((t, d, r, ratio, verdict))
    print(f"{t:8} {d:9} {r:9} {ratio:7.3f}  {verdict}")

print("\nresidual 0  -> token existed only as artifact, no collision")
print("0 < ratio   -> two meanings shared one weight: collision")
print("ratio ~ 1   -> repair did not touch it; explain why")

# --- 4. class profile for the big collisions ---------------------------
print("\n=== class profile: corrupted vs genuine occurrences ===")
for t, d, r, ratio, verdict in rows:
    if verdict != "COLLISION" or d < 2000:
        continue
    pat = r"\b" + re.escape(t) + r"\b"
    had = s.str.contains(pat, regex=True)
    still = s_rep.str.contains(pat, regex=True)
    corrupted_only = had & ~still          # occurrences repair removed
    print(f"\n  {t}: {int(corrupted_only.sum())} rows lost the token")
    prof = pd.DataFrame({
        "corrupted": df.loc[corrupted_only, "class_name"].value_counts(normalize=True),
        "genuine": df.loc[still, "class_name"].value_counts(normalize=True),
    }).round(3)
    print(prof.to_string())
    print("  Matching profiles -> harmless collision. Diverging -> reportable.")

# --- 5. the JSONL cell census ------------------------------------------
print("\n=== 2x2 JSONL census ===")
try:
    recs = [json.loads(l) for l in open(JSONL)]
except FileNotFoundError:
    print("not found")
    recs = []

if recs:
    c = Counter((r.get("experiment"), r.get("cell"), r.get("train"), r.get("test"))
                for r in recs)
    for k, n in sorted(c.items(), key=lambda kv: str(kv[0])):
        print(f"  {k}  x{n}")
    odd = [r for r in recs if r.get("train") == "-"]
    if odd:
        print(f"\n  {len(odd)} record(s) with train='-'. First:")
        print(" ", json.dumps(odd[0], indent=2)[:400])
        print("  Identify these before the JSONL is cited as evidence.")