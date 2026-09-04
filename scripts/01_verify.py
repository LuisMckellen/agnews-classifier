"""Verification, the STRIP decision, and duplicate titles.

Replaces `inspect_corruption.py`, `dup.py`, and the schema half of
`audit.py`. Every pattern is imported from `agnews.clean`; nothing here
retypes one.

    PYTHONIOENCODING=utf-8 python scripts/01_verify.py
"""

from __future__ import annotations

import pandas as pd

from agnews.clean import RE_CORRUPT, PATTERNS
from agnews.data import build_text, load_train

APPENDIX_ANY_BARE = 38_678       # four-way count, 3 Sep. The 2 Sep
                                 # "correction" to 38,679 came from a
                                 # `\\b`-less pattern retyped in audit.py,
                                 # which matched row 20884: "Israel Strikes
                                 # Hamas Camp; 13 Are Killed". Not corruption.
TAIL_MAX_COUNT = 3
TAIL_SAMPLE = 40


def schema(df: pd.DataFrame) -> None:
    print("=== schema ===")
    print(f"  shape           {df.shape}")
    print(f"  labels          {sorted(df['label'].unique())}")
    print(f"  nulls           {int(df.isna().sum().sum())}")
    print(f"  class balance   {df['class_name'].value_counts().to_dict()}")
    ln = df["text"].str.len()
    print(f"  length          mean {ln.mean():.1f}  sd {ln.std():.1f}  "
          f"min {ln.min()}  med {int(ln.median())}  max {ln.max()}")
    print(f"  exact dupes     text {int(df['text'].duplicated().sum())}  "
          f"title {int(df['title'].duplicated().sum())}  "
          f"description {int(df['description'].duplicated().sum())}")


def strip_decision(df: pd.DataFrame) -> None:
    """Which `text` definition produced 38,679?

    `load.py` stripped, `data.py` did not, and both were in use. This
    settles it with the terminal instead of a preference.
    """
    print("\n=== STRIP decision ===")
    for strip in (True, False):
        t = build_text(df["title"], df["description"], strip=strip)
        n = int(t.str.contains(RE_CORRUPT).sum())
        mark = "  <- reproduces the appendix" if n == APPENDIX_ANY_BARE else ""
        print(f"  strip={str(strip):5} any_bare={n}{mark}")
    print(f"  appendix says {APPENDIX_ANY_BARE}. Set data.STRIP to whichever")
    print("  matches. If neither does, the appendix figure is unreproducible")
    print("  and nothing downstream of it may be cited (METHOD 17).")


def corruption(df: pd.DataFrame) -> None:
    print("\n=== corruption ===")
    for name, pat in PATTERNS.items():
        print(f"  {name:12} {int(df['text'].str.contains(pat, regex=True).sum())}")
    hit = df["text"].str.contains(RE_CORRUPT)
    total = int(hit.sum())
    print(f"  any_bare     {total}  ({hit.mean():.4f})")

    rates = df.assign(hit=hit).groupby("class_name")["hit"].mean()
    print("\n  per class (share of rows):")
    for name, r in rates.items():
        print(f"    {name:10} {r:.4f}")

    # Balanced classes give a free identity (METHOD 16). Computed on counts,
    # not on 4dp rates -- rates round to a 3-row grid and cannot resolve one
    # row, which is why the 38,678 error was caught by the recount and only
    # confirmed by the identity.
    implied = int(df.assign(hit=hit).groupby("class_name")["hit"].sum().sum())
    print(f"\n  identity: per-class counts sum to {implied}, total is {total}")
    assert implied == total, "exact identity failed; no tolerance (METHOD 21)"
    print("  exact")


def duplicate_titles(df: pd.DataFrame) -> None:
    """Three quantities get called '5,636'. State which (METHOD 18)."""
    counts = df["title"].value_counts()
    dupes = counts[counts > 1]
    print("\n=== duplicate titles ===")
    print(f"  distinct titles appearing more than once   {len(dupes)}")
    print(f"  rows involved in those titles              {int(dupes.sum())}")
    print(f"  rows beyond the first of each              {int(df['title'].duplicated().sum())}")
    print("  The appendix says 5,636 without saying which. The head-is-3.8%")
    print("  claim only holds against one of them.")

    head = counts.head(8)
    print(f"\n  head totals {int(head.sum())} occurrences "
          f"= {100 * head.sum() / dupes.sum():.1f}% of rows involved")

    tail = dupes[dupes <= TAIL_MAX_COUNT].index.to_series().sample(
        TAIL_SAMPLE, random_state=0
    )
    conflicts = sum(
        df.loc[df["title"] == t, "label"].nunique() > 1 for t in tail
    )
    print(f"\n  tail sample n={TAIL_SAMPLE}, count<={TAIL_MAX_COUNT}: "
          f"{conflicts} label conflicts (counted, not eyeballed)")
    print("  Scope: syndicated pairs only. Selected for running on more than")
    print("  one desk, the population most likely to be dual-category, so")
    print("  the rate does not lift to the corpus (METHOD 38).")


def main() -> None:
    df = load_train()
    schema(df)
    strip_decision(df)
    corruption(df)
    duplicate_titles(df)


if __name__ == "__main__":
    main()