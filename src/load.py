import pandas as pd

COLS = ["label", "title", "description"]
CLASSES = ["World", "Sports", "Business", "Sci-Tech"]

TRAIN_PATH = "data/train.csv"
OFFICIAL_TEST_PATH = "data/test.csv"


def _read(path):
    df = pd.read_csv(path, header=None, names=COLS, encoding="utf-8")
    df["label"] = df["label"] - 1
    df["text"] = df["title"].str.strip() + " " + df["description"].str.strip()
    return df


def load_corpus():
    """The 120k working corpus. All experiments draw from this."""
    return _read(TRAIN_PATH)


def load_official_test(i_am_reporting_final_benchmark=False):
    """QUARANTINED. Held-out benchmark split — touch once, in W10.

    Every published AG News number is measured on these 7,600 rows.
    Training, tuning, or resampling against them destroys that
    comparability permanently and silently.
    """
    if not i_am_reporting_final_benchmark:
        raise RuntimeError(
            "Quarantined until the final benchmark. If you are sure, "
            "pass i_am_reporting_final_benchmark=True."
        )
    return _read(OFFICIAL_TEST_PATH)

