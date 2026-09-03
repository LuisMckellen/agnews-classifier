# src/floor.py
"""Noise floor and the corruption 2x2.

Every result row carries its environment. The xgboost 3.2.0 vs 3.4.1
episode cost a week because the version wasn't stored beside the metric.
"""
import json
import subprocess
import time
from pathlib import Path

import numpy as np
import sklearn
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import f1_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from src.load import load_corpus
from src.clean import repair

RESULTS = Path("results")
SEEDS = [0, 1, 2, 3, 4]
N_SAMPLE = 5000


def git_sha():
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], text=True
        ).strip()
    except Exception:
        return "unknown"


def make_pipe(seed):
    return Pipeline([
        ("tfidf", TfidfVectorizer()),
        ("clf", LogisticRegression(max_iter=1000, random_state=seed)),
    ])


def run_2x2(df, seeds=SEEDS, n=N_SAMPLE, out="corruption_2x2.jsonl"):
    sha, skv = git_sha(), sklearn.__version__
    rows = []

    for seed in seeds:
        sub = df.sample(n=n, random_state=seed)
        tr, te = train_test_split(
            sub, test_size=0.2, random_state=seed, stratify=sub["label"]
        )

        # Repair once per split, not once per cell.
        variants = {
            "dirty": (tr["text"], te["text"]),
            "repaired": (tr["text"].map(repair), te["text"].map(repair)),
        }

        for tr_kind in ("dirty", "repaired"):
            X_tr = variants[tr_kind][0]
            pipe = make_pipe(seed)
            t0 = time.perf_counter()
            pipe.fit(X_tr, tr["label"])
            fit_s = time.perf_counter() - t0

            for te_kind in ("dirty", "repaired"):
                X_te = variants[te_kind][1]
                pred = pipe.predict(X_te)
                rows.append({
                    "experiment": "corruption_2x2",
                    "cell": {("dirty", "dirty"): "A", ("dirty", "repaired"): "B",
                             ("repaired", "dirty"): "C",
                             ("repaired", "repaired"): "D"}[(tr_kind, te_kind)],
                    "train": tr_kind,
                    "test": te_kind,
                    "seed": seed,
                    "n": n,
                    "macro_f1": f1_score(te["label"], pred, average="macro"),
                    "vocab_size": len(pipe.named_steps["tfidf"].vocabulary_),
                    "fit_seconds": round(fit_s, 2),
                    "sklearn": skv,
                    "git_sha": sha,
                })

        # Dummy, once per seed, for the floor of the floor.
        d = DummyClassifier(strategy="most_frequent").fit(tr["text"], tr["label"])
        rows.append({
            "experiment": "dummy", "cell": "dummy", "train": "-", "test": "-",
            "seed": seed, "n": n,
            "macro_f1": f1_score(te["label"], d.predict(te["text"]), average="macro"),
            "sklearn": skv, "git_sha": sha,
        })

    RESULTS.mkdir(exist_ok=True)
    with open(RESULTS / out, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    return rows


def summarise(rows):
    import pandas as pd
    res = pd.DataFrame([r for r in rows if r["experiment"] == "corruption_2x2"])

    print("\nPer cell:")
    print(res.groupby("cell")["macro_f1"].agg(["mean", "std"]).round(4))

    # Paired deltas: same seed, so split luck cancels.
    wide = res.pivot(index="seed", columns="cell", values="macro_f1")
    print("\nPaired deltas (mean, std, n_seeds same sign):")
    for a, b in [("A", "B"), ("C", "D"), ("A", "D"), ("C", "B")]:
        d = wide[a] - wide[b]
        print(f"  {a}-{b}: {d.mean():+.4f}  sd {d.std():.4f}  "
              f"{int((np.sign(d) == np.sign(d.mean())).sum())}/{len(d)}")


if __name__ == "__main__":
    df = load_corpus()
    summarise(run_2x2(df))