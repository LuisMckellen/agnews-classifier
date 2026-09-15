"""The corruption 2x2, re-run against the fixed `repair` (4 Sep boundary fix).

Supersedes the 31 Aug run in results/corruption_2x2.jsonl, which used a
`repair` that left the entity's space in place: `Ch #225;vez` became
`Ch avez`, two tokens. No result survives a change to the transform that
produced it, so C and D are void and B moves with them.

Cell A is dirty-trained and dirty-tested. `repair` is called on neither
array in that path, so the boundary fix has no route to it and cell A must
reproduce the old number exactly. A mismatch is a reimplementation
difference, not the fix -- the environment is ruled out separately, since
every old record carries sklearn 1.9.0 and this run is pinned to it.

Only the boundary changed. `_REPAIRABLE_NUM` stays at 30-39/100-299 so
this run isolates one edit (METHOD 21).

Nothing executes at import (METHOD 24).
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from sklearn.metrics import f1_score
from sklearn.model_selection import train_test_split

from agnews.clean import repair
from agnews.data import load_train
from agnews.evaluate import (
    assert_shared_split,
    assert_shared_vocab,
    paired_delta,
    read_cells,
)
from agnews.pipelines import make_pipe
from agnews.runlog import stamp

RESULTS = Path("results")
OUT = RESULTS / "corruption_2x2_v2.jsonl"
EXPERIMENT = "corruption_2x2_v2"

SEEDS = [0, 1, 2, 3, 4]
N_SAMPLE = 5000

# --- what the 31 Aug run recorded, at full precision ----------------------
#
# Read from results/corruption_2x2.jsonl, experiment="corruption_2x2".
# Cell A cannot move. A and B share a train side, so their vocabulary is
# fit on dirty text and cannot move either -- even though B's score does.

A_SEED0_EXPECTED = 0.8723996742029361
AB_VOCAB_EXPECTED = {0: 15980, 1: 16195, 2: 16267,3: 16243, 4: 16436}

CELL = {
    ("dirty", "dirty"): "A",
    ("dirty", "repaired"): "B",
    ("repaired", "dirty"): "C",
    ("repaired", "repaired"): "D",
}


def split_fingerprint(index) -> str:
    """Stable digest of a test slice.

    Not `hash()`: that is salted per process for some types and would
    differ between runs for no reason. The point is to compare across
    cells and across runs.
    """
    raw = ",".join(str(int(i)) for i in index).encode()
    return hashlib.sha1(raw).hexdigest()[:12]


def run(df, seeds=SEEDS, n=N_SAMPLE) -> list[dict]:
    env = stamp()
    rows: list[dict] = []

    for seed in seeds:
        sub = df.sample(n=n, random_state=seed)
        tr, te = train_test_split(
            sub, test_size=0.2, random_state=seed, stratify=sub["label"]
        )
        fingerprint = split_fingerprint(te.index)

        # Repair once per split, not once per cell.
        variants = {
            "dirty": (tr["text"], te["text"]),
            "repaired": (tr["text"].map(repair), te["text"].map(repair)),
        }

        for tr_kind in ("dirty", "repaired"):
            pipe = make_pipe(seed)
            pipe.fit(variants[tr_kind][0], tr["label"])
            vocab = len(pipe.named_steps["tfidf"].vocabulary_)

            for te_kind in ("dirty", "repaired"):
                cell = CELL[(tr_kind, te_kind)]
                pred = pipe.predict(variants[te_kind][1])
                score = f1_score(te["label"], pred, average="macro")

                if cell == "A" and seed == 0:
                    check_cell_a(score)
                if cell in ("A", "B"):
                    check_vocab(seed, cell, vocab)

                rows.append({
                    "experiment": EXPERIMENT,
                    "cell": cell,
                    "train": tr_kind,
                    "test": te_kind,
                    "seed": seed,
                    "n": n,
                    "macro_f1": score,
                    "vocab_size": vocab,
                    "test_idx_sha1": fingerprint,
                    **env,
                })

    return rows


# --- halt conditions ------------------------------------------------------
#
# Each fails loudly and stops the run. A number that survives a broken
# check is worse than no number.


def check_cell_a(score: float) -> None:
    if score != A_SEED0_EXPECTED:
        raise SystemExit(
            f"HALT: cell A seed 0 is {score!r}, expected {A_SEED0_EXPECTED!r} "
            f"(delta {score - A_SEED0_EXPECTED:+.3e}).\n"
            "`repair` is not called on either array in this path, and the "
            "environment matches, so this is a reimplementation difference. "
            "Check the vocab line below: if vocab also moved, the data path "
            "differs (text construction, separator, sample or split). If "
            "vocab matched, the difference is in the fit."
        )


def check_vocab(seed: int, cell: str, vocab: int) -> None:
    expected = AB_VOCAB_EXPECTED[seed]
    if vocab != expected:
        raise SystemExit(
            f"HALT: {cell} seed {seed} vocab is {vocab}, expected {expected}. "
            "A and B are dirty-trained; `repair` cannot reach their "
            "vocabulary. The token stream differs from the 31 Aug run."
        )


def write(rows: list[dict]) -> None:
    RESULTS.mkdir(exist_ok=True)
    if OUT.exists():
        raise SystemExit(
            f"HALT: {OUT} exists. Move it aside rather than overwriting -- "
            "the 31 Aug file was opened with 'w' and that is how a baseline "
            "gets destroyed."
        )
    with OUT.open("w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")


def summarise() -> None:
    scores = read_cells(OUT, EXPERIMENT, "macro_f1")
    assert_shared_vocab(read_cells(OUT, EXPERIMENT, "vocab_size"))
    assert_shared_split(read_cells(OUT, EXPERIMENT, "test_idx_sha1"))

    print("\nper cell:")
    for c in "ABCD":
        vals = [scores[s][c] for s in sorted(scores)]
        print(f"  {c}  {sum(vals) / len(vals):.6f}   "
              + " ".join(f"{v:.6f}" for v in vals))

    print("\npaired deltas:")
    for left, right in [("A", "B"), ("C", "D"), ("A", "C"), ("B", "D")]:
        print("  " + str(paired_delta(scores, left, right)))

    print("\nhalt conditions passed: cell A exact, A/B vocab exact, "
          "vocab shared within train side, split shared within seed.")


if __name__ == "__main__":
    write(run(load_train()))
    summarise()