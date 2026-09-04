"""Paired-delta arithmetic. One definition, one script, one run (METHOD 19).

Every comparison in this project routes through here so two tables cannot
be computed two ways. Nothing executes at import.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np

# Cells carry the same digits everywhere. 4dp gave A-B + B-D = -0.0039 but
# A-C + C-D = -0.0038 on identical data. Six digits, and the identities
# audit cleanly.
DP = 6


@dataclass(frozen=True)
class Delta:
    left: str
    right: str
    mean: float
    sd: float
    n: int
    agree: int
    sign: str
    inside_se: bool

    def __str__(self) -> str:
        flag = "  <- mean inside its own se; the sign count is noise" if self.inside_se else ""
        return (f"{self.left}-{self.right}  {self.mean:+.{DP}f}  "
                f"sd {self.sd:.{DP}f}  {self.agree}/{self.n} {self.sign}{flag}")


def paired_delta(per_seed: dict[int, dict[str, float]], left: str, right: str) -> Delta:
    """Per-seed difference, then summarise. Shared split luck cancels (METHOD 2).

    Reports mean, spread and sign agreement together (METHOD 3). Flags the
    case where the mean sits inside its own standard error, because a sign
    count on such a delta is describing noise (METHOD 6a).
    """
    seeds = sorted(per_seed)
    d = np.array([per_seed[s][left] - per_seed[s][right] for s in seeds], dtype=float)
    n = len(d)
    if n < 2:
        raise ValueError("a delta needs at least two seeds to have a spread")

    pos = int((d > 0).sum())
    mean, sd = float(d.mean()), float(d.std(ddof=1))
    return Delta(
        left=left, right=right, mean=mean, sd=sd, n=n,
        agree=max(pos, n - pos),
        sign="pos" if pos > n - pos else "neg",
        inside_se=abs(mean) < sd / np.sqrt(n),
    )


def telescoping_residuals(
    per_seed: dict[int, dict[str, float]], a: str, via: str, b: str
) -> dict[int, float]:
    """(a-via) + (via-b) - (a-b), per seed. Exactly zero by algebra.

    True by construction, so this validates plumbing, not science
    (METHOD 16). A non-zero residual means an arm is not the arm you think
    it is: mispaired seeds, a refit vectorizer, a different test slice.
    """
    return {
        s: (v[a] - v[via]) + (v[via] - v[b]) - (v[a] - v[b])
        for s, v in per_seed.items()
    }


def assert_telescoping(per_seed, a: str, via: str, b: str, tol: float = 1e-12) -> None:
    bad = {s: r for s, r in telescoping_residuals(per_seed, a, via, b).items() if abs(r) > tol}
    if bad:
        raise AssertionError(f"telescoping failed via {via}: {bad}")


def read_cells(path: str | Path, experiment: str) -> dict[int, dict[str, float]]:
    """Load one experiment's cells out of a shared JSONL file.

    A results file holds more than one experiment (METHOD 30);
    corruption_2x2.jsonl already carries the superseded run and five
    dummies. Filter, never assume.
    """
    per_seed: dict[int, dict[str, float]] = {}
    with Path(path).open(encoding="utf-8") as fh:
        for line in fh:
            r = json.loads(line)
            if r.get("experiment") != experiment:
                continue
            per_seed.setdefault(r["seed"], {})[r["cell"]] = r["macro_f1"]
    if not per_seed:
        raise LookupError(f"no rows with experiment={experiment!r} in {path}")
    return per_seed