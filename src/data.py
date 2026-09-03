"""Canonical corpus loader. One definition of `text`, imported everywhere.

Nothing executes at import (METHOD 24).
"""

from pathlib import Path
import pandas as pd

TRAIN_CSV = Path("data/train.csv")
TEST_CSV = Path("data/test.csv")          # quarantined — see load_quarantined

COLUMNS = ["label", "title", "description"]
SEP = " "                                  # the one definition of the join
EXPECTED_TRAIN_ROWS = 120_000
EXPECTED_TEST_ROWS = 7_600

LABELS = {1: "World", 2: "Sports", 3: "Business", 4: "Sci-Tech"}


def _read(path: Path, expected_rows: int) -> pd.DataFrame:
    df = pd.read_csv(path, header=None, names=COLUMNS)
    if len(df) != expected_rows:
        raise ValueError(f"{path}: expected {expected_rows} rows, got {len(df)}")
    df["text"] = df["title"].astype(str) + SEP + df["description"].astype(str)
    df["class_name"] = df["label"].map(LABELS)
    return df


def load_train() -> pd.DataFrame:
    """The 120k working corpus. Every script uses this, never read_csv."""
    return _read(TRAIN_CSV, EXPECTED_TRAIN_ROWS)


def load_quarantined(i_am_sure: bool = False) -> pd.DataFrame:
    """The held-out 7,600.

    Guarded deliberately, not made impossible (METHOD 29). Distribution
    checks are fine; fitting anything on this is not (METHOD 12).
    """
    if not i_am_sure:
        raise RuntimeError(
            "Quarantined test set. Pass i_am_sure=True and say in the commit "
            "message why. Distribution checks only — never fit."
        )
    return _read(TEST_CSV, EXPECTED_TEST_ROWS)