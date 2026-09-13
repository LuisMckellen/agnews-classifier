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
    neg: int
    pos: int
    zero: int
    inside_se: bool

    @property
    def majority(self) -> str:
        """Direction of the per-seed majority, or 'tied'.

        Reported from the seeds themselves, never from the sign of the
        mean -- a count that agrees with the mean by construction cannot
        corroborate it.
        """
        if self.pos > self.neg:
            return "pos"
        if self.neg > self.pos:
            return "neg"
        return "tied"

    def __str__(self) -> str:
        flag = "  <- mean inside its own se; the sign count is noise" if self.inside_se else ""
        zero = f" zero {self.zero}" if self.zero else ""
        return (f"{self.left}-{self.right}  {self.mean:+.{DP}f}  "
                f"sd {self.sd:.{DP}f}  "
                f"neg {self.neg} pos {self.pos}{zero} of {self.n} "
                f"({self.majority}){flag}")


def paired_delta(per_seed: dict[int, dict[str, float]], left: str, right: str) -> Delta:
    """Per-seed difference, then summarise. Shared split luck cancels (METHOD 2).

    Reports mean, spread and sign agreement together (METHOD 3). Flags the
    case where the mean sits inside its own standard error, because a sign
    count on such a delta is describing noise (METHOD 6a).

    Orientation is fixed and asserted in the tests: `paired_delta(p, "A",
    "B")` returns left minus right, so a negative mean means the left arm
    scores lower. Sign is counted per seed, and exact zeros are counted as
    zeros -- never folded into either direction.
    """
    seeds = sorted(per_seed)
    missing = {s: [c for c in (left, right) if c not in per_seed[s]] for s in seeds}
    missing = {s: c for s, c in missing.items() if c}
    if missing:
        raise KeyError(f"cells absent for some seeds: {missing}")

    d = np.array([per_seed[s][left] - per_seed[s][right] for s in seeds], dtype=float)
    n = len(d)
    if n < 2:
        raise ValueError("a delta needs at least two seeds to have a spread")

    neg = int((d < 0).sum())
    pos = int((d > 0).sum())
    zero = int((d == 0).sum())
    assert neg + pos + zero == n

    mean, sd = float(d.mean()), float(d.std(ddof=1))
    return Delta(
        left=left, right=right, mean=mean, sd=sd, n=n,
        neg=neg, pos=pos, zero=zero,
        inside_se=abs(mean) < sd / np.sqrt(n),
    )


# --- integrity checks on the arms themselves ------------------------------
#
# The telescoping residual below is zero for any three floats drawn from the
# same record, so it cannot detect mispaired seeds, a refit vectorizer or a
# different test slice -- the three things its old docstring claimed. It is
# kept as a float-arithmetic smoke test and must NOT be counted as a halt
# condition (METHOD: an audit whose result is forced by construction is not
# an audit). The two functions after it are the ones that can fail.


def telescoping_residuals(
    per_seed: dict[int, dict[str, float]], a: str, via: str, b: str
) -> dict[int, float]:
    """(a-via) + (via-b) - (a-b), per seed. Zero for ANY three floats.

    Catches float accumulation only. It is not evidence that an arm is the
    arm you think it is.
    """
    return {
        s: (v[a] - v[via]) + (v[via] - v[b]) - (v[a] - v[b])
        for s, v in per_seed.items()
    }


def assert_telescoping(per_seed, a: str, via: str, b: str, tol: float = 1e-12) -> None:
    bad = {s: r for s, r in telescoping_residuals(per_seed, a, via, b).items() if abs(r) > tol}
    if bad:
        raise AssertionError(f"float arithmetic failed via {via}: {bad}")


def assert_shared_vocab(
    per_seed: dict[int, dict[str, float]], groups=(("A", "B"), ("C", "D"))
) -> None:
    """Cells sharing a train side must share a vocabulary, per seed.

    The vectorizer is fit on train text only, so A and B come from one fit
    and C and D from another. A mismatch means a refit between cells, a
    mispaired seed, or train text that is not what the cell label says.
    """
    bad = {}
    for s, v in per_seed.items():
        for group in groups:
            vals = {c: v[c] for c in group if c in v}
            if len(set(vals.values())) > 1:
                bad[(s, group)] = vals
    if bad:
        raise AssertionError(f"vocab differs within a train side: {bad}")


def assert_shared_split(per_seed: dict[int, dict[str, object]]) -> None:
    """All cells of one seed must have been scored on the same test slice."""
    bad = {s: v for s, v in per_seed.items() if len(set(v.values())) > 1}
    if bad:
        raise AssertionError(f"test slice differs within a seed: {bad}")


def read_cells(
    path: str | Path, experiment: str, field: str = "macro_f1"
) -> dict[int, dict[str, object]]:
    """Load one experiment's cells out of a shared JSONL file.

    A results file holds more than one experiment (METHOD 30);
    corruption_2x2.jsonl carries the superseded run and five dummies, and
    the dummies use cell='dummy' with train/test='-'. Filter, never assume.

    `field` selects what lands in the map, so the same reader serves
    macro_f1, vocab_size and the split fingerprint.
    """
    per_seed: dict[int, dict[str, object]] = {}
    with Path(path).open(encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            r = json.loads(line)
            if r.get("experiment") != experiment:
                continue
            if field not in r:
                raise KeyError(f"record for seed {r.get('seed')} has no {field!r}")
            per_seed.setdefault(r["seed"], {})[r["cell"]] = r[field]
    if not per_seed:
        raise LookupError(f"no rows with experiment={experiment!r} in {path}")
    return per_seed