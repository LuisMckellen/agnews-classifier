"""Canonical corpus loader. One definition of `text`, imported everywhere.

Merges the old `load.py` and `data.py`, which disagreed on two things:

  * `load.py` stripped both fields before joining; `data.py` did not.
  * `load.py` did `label - 1`, giving 0-3; `data.py` kept 1-4.

`inspect_corruption.py` used `load_corpus` and produced 38,679.
`collision.py` used `load_train` and produced the collision table. So two
published tables were computed on different strings and different labels.

STRIP below is UNRESOLVED. Run `scripts/01_verify.py` first: it reports the
corruption count under both, and whichever reproduces 38,679 is the one
that generated the appendix. Set it from that, do not guess.

Labels stay 1-4 and every table reports `class_name`, never `label`, so a
per-class row cannot be silently reordered.

Nothing executes at import (METHOD 24).
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

TRAIN_CSV = Path("data/train.csv")
TEST_CSV = Path("data/test.csv")

COLUMNS = ["label", "title", "description"]
SEP = " "
STRIP = True          # <- decide from 01_verify, then never touch again
EXPECTED_TRAIN_ROWS = 120_000
EXPECTED_TEST_ROWS = 7_600
EXPECTED_PER_CLASS = 30_000

LABELS = {1: "World", 2: "Sports", 3: "Business", 4: "Sci-Tech"}


def build_text(title: pd.Series, description: pd.Series, strip: bool = STRIP) -> pd.Series:
    """The one definition of `text`. Nothing builds it independently."""
    t, d = title.astype(str), description.astype(str)
    if strip:
        t, d = t.str.strip(), d.str.strip()
    return t + SEP + d


def _read(path: Path, expected_rows: int) -> pd.DataFrame:
    df = pd.read_csv(path, header=None, names=COLUMNS, encoding="utf-8")
    if len(df) != expected_rows:
        raise ValueError(f"{path}: expected {expected_rows} rows, got {len(df)}")
    if not set(df["label"]) <= set(LABELS):
        raise ValueError(f"{path}: unexpected labels {sorted(set(df['label']))}")
    df["text"] = build_text(df["title"], df["description"])
    df["class_name"] = df["label"].map(LABELS)
    return df


def load_train() -> pd.DataFrame:
    """The 120k working corpus. Every script uses this, never read_csv.

    `audit.py` called `pd.read_csv` directly and rebuilt `text` with its own
    local SEP. That is how you end up with two corpora.
    """
    df = _read(TRAIN_CSV, EXPECTED_TRAIN_ROWS)
    counts = df["class_name"].value_counts()
    if not (counts == EXPECTED_PER_CLASS).all():
        raise ValueError(f"class balance broken: {counts.to_dict()}")
    return df


def load_quarantined(i_am_sure: bool = False) -> pd.DataFrame:
    """The held-out 7,600.

    Guarded deliberately, not made impossible (METHOD 29). Every published
    AG News number is measured on these rows; fitting anything on them
    destroys that comparability permanently and silently. Distribution
    checks are fine (METHOD 12).
    """
    if not i_am_sure:
        raise RuntimeError(
            "Quarantined test set. Pass i_am_sure=True and say in the commit "
            "message why. Distribution checks only -- never fit."
        )
    return _read(TEST_CSV, EXPECTED_TEST_ROWS)