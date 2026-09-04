"""Collision table and markup audit.

Replaces `collision.py` and `audit.py`. Both retyped `BARE_NAMED` without
the `\\b`, giving a third definition that also matches `salt;` and
`clamp;`. Here every pattern is imported.

    PYTHONIOENCODING=utf-8 python scripts/02_collision.py
"""

from __future__ import annotations

import pandas as pd

from agnews.clean import RE_INTACT, RE_MARKUP, repair
from agnews.data import load_train

SUSPECTS = ["39", "36", "151", "146", "147", "148", "160", "133", "145",
            "149", "38", "37", "lt", "gt", "amp", "quot", "nbsp", "apos"]

# The appendix flags this in prose only: the table was built case-sensitive
# while TfidfVectorizer lowercases, which is why lt/gt/amp showed residual 0
# yet survived in the vocabulary. It is a parameter now, and both are run.
CASES = (True, False)
UNTOUCHED_RATIO = 0.95


def doc_freq(series: pd.Series, token: str, case: bool) -> int:
    return int(series.str.contains(rf"\b{token}\b", regex=True, case=case).sum())


def verdict(dirty: int, residual: int) -> str:
    if dirty == 0:
        return "absent"
    if residual == 0:
        return "pure artifact"
    if residual / dirty > UNTOUCHED_RATIO:
        return "untouched"
    return "collision"


def collision_table(s: pd.Series, s_rep: pd.Series) -> pd.DataFrame:
    rows = []
    for case in CASES:
        for tok in SUSPECTS:
            d = doc_freq(s, tok, case)
            r = doc_freq(s_rep, tok, case)
            rows.append({
                "token": tok, "case_sensitive": case, "dirty_df": d,
                "residual": r, "ratio": (r / d) if d else float("nan"),
                "verdict": verdict(d, r),
            })
    return pd.DataFrame(rows)


def class_profile(df: pd.DataFrame, s: pd.Series, s_rep: pd.Series, tok: str) -> None:
    """Corrupted sense vs genuine sense.

    The genuine column is a POPULATION, not a sample -- it is every row
    where the token survives repair. So there are no error bars, and the
    proportions are exact facts about this corpus only. State the size
    beside them: 169 rows against 29,659 is a 175:1 ratio, and a sense
    holding 0.57% of a token's mass is not a plausible mechanism for a
    0.0039 effect (METHOD 23a). The divergence is real and small.
    """
    pat = rf"\b{tok}\b"
    had = s.str.contains(pat, regex=True)
    still = s_rep.str.contains(pat, regex=True)
    lost = had & ~still
    n_lost, n_still = int(lost.sum()), int(still.sum())
    print(f"\n  {tok}: corrupted sense {n_lost} rows, genuine sense {n_still} rows "
          f"({n_lost / max(n_still, 1):.0f}:1)")
    prof = pd.DataFrame({
        "corrupted": df.loc[lost, "class_name"].value_counts(normalize=True),
        "genuine": df.loc[still, "class_name"].value_counts(normalize=True),
    }).round(3)
    print(prof.to_string().replace("\n", "\n    "))


def markup(df: pd.DataFrame, s: pd.Series) -> None:
    """The 5,241 count is real. The containment check around it was not.

    RE_MARKUP requires an intact `&lt;`, which contains `lt;`, so
    "matched by intact" and "matched by bare_named" are guaranteed by
    construction. Reported here as counts only, with no verdict attached.
    """
    has = s.str.contains(RE_MARKUP)
    print(f"\n=== markup ===\n  rows {int(has.sum())}  "
          f"({has.mean():.5f} of corpus)")
    print(f"  also intact {int((has & s.str.contains(RE_INTACT)).sum())} "
          "(tautological: RE_MARKUP requires `&lt;`)")
    rates = df.assign(m=has).groupby("class_name")["m"].mean()
    print("\n  per class:")
    for name, r in rates.items():
        print(f"    {name:10} {r:.4f}")
    print(f"  spread {rates.max() / rates.min():.2f}x")


def main() -> None:
    df = load_train()
    s = df["text"]
    s_rep = s.map(repair)

    table = collision_table(s, s_rep)
    print("=== collision table ===")
    print(table.to_string(index=False, float_format=lambda v: f"{v:.3f}"))

    moved = table.pivot(index="token", columns="case_sensitive", values="residual")
    differs = moved[moved[True] != moved[False]]
    if len(differs):
        print("\n  residual differs by case for:", list(differs.index))
        print("  The vectorizer lowercases, so the case=False row is the one")
        print("  that describes what the model saw.")

    print("\n=== class profiles ===")
    for tok in table.query("verdict == 'collision' and dirty_df >= 2000")["token"].unique():
        class_profile(df, s, s_rep, tok)

    markup(df, s)


if __name__ == "__main__":
    main()