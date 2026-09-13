"""Tests for the paired-delta arithmetic.

Property-based where a property pins the behaviour. Three things a
property cannot pin are asserted from the definition instead:

  - orientation: antisymmetry holds under either sign convention, so it
    cannot tell A-B from B-A. The sign of -0.0039 depends on this.
  - zero handling: a sign count that folds exact zeros into one direction
    satisfies every algebraic property above.
  - ddof: "sd is zero on a constant offset" passes identically for
    ddof=0 and ddof=1. At n=5 they differ by 1.118x.

Derived, not guessed. The failure mode this avoids is a hand-computed
expected value that is itself wrong and passes silently
(cf. test_hash_number_not_an_entity, which failed twice for that reason).
"""

from __future__ import annotations

import math

import pytest

from agnews.evaluate import (
    assert_shared_split,
    assert_shared_vocab,
    paired_delta,
    telescoping_residuals,
)


def cells(**by_cell: list[float]) -> dict[int, dict[str, float]]:
    """Build a per_seed map from parallel per-cell lists."""
    names = list(by_cell)
    n = len(by_cell[names[0]])
    assert all(len(v) == n for v in by_cell.values())
    return {s: {c: by_cell[c][s] for c in names} for s in range(n)}


# --- orientation ----------------------------------------------------------

def test_left_minus_right_not_right_minus_left() -> None:
    """A uniform +0.1 gap on the left arm must come back as +0.1.

    Derived from the name: paired_delta(p, "A", "B") is A minus B. If this
    inverts, every sign in the 2x2 write-up inverts with it.
    """
    p = cells(A=[0.5, 0.5, 0.5], B=[0.4, 0.4, 0.4])
    d = paired_delta(p, "A", "B")
    assert d.mean == pytest.approx(+0.1)
    assert d.pos == 3 and d.neg == 0
    assert d.majority == "pos"


def test_antisymmetry_does_not_fix_orientation() -> None:
    """Both orderings flip, which is why the test above is separate."""
    p = cells(A=[0.5, 0.5, 0.5], B=[0.4, 0.4, 0.4])
    assert paired_delta(p, "A", "B").mean == pytest.approx(
        -paired_delta(p, "B", "A").mean
    )


# --- sign counting --------------------------------------------------------

def test_exact_zero_is_counted_as_zero() -> None:
    """Ties belong to neither arm.

    `agree = max(pos, n - pos)` reported 3/5 neg on this input: the two
    zeros were folded into the negative count. Nothing in the algebra
    catches that.
    """
    p = cells(A=[0.5, 0.5, 0.5, 0.5, 0.5], B=[0.4, 0.4, 0.5, 0.5, 0.5])
    d = paired_delta(p, "A", "B")
    assert (d.pos, d.neg, d.zero) == (2, 0, 3)
    assert d.pos + d.neg + d.zero == d.n


def test_majority_is_tied_when_it_is_tied() -> None:
    """Two each way is not a majority for either."""
    p = cells(A=[0.5, 0.5, 0.4, 0.4], B=[0.4, 0.4, 0.5, 0.5])
    d = paired_delta(p, "A", "B")
    assert (d.pos, d.neg) == (2, 2)
    assert d.majority == "tied"


def test_sign_is_counted_per_seed_not_from_the_mean() -> None:
    """One large seed can outvote three small ones in the mean.

    A count taken as `sign(d) == sign(d.mean())` agrees with the mean by
    construction and corroborates nothing.
    """
    p = cells(A=[0.9, 0.4, 0.4, 0.4], B=[0.0, 0.5, 0.5, 0.5])
    d = paired_delta(p, "A", "B")
    assert d.mean > 0
    assert d.neg == 3 and d.pos == 1
    assert d.majority == "neg"


# --- spread ---------------------------------------------------------------

def test_sd_uses_ddof_one() -> None:
    """Sample convention, matching pandas Series.std() in floor.py.

    The 31 Aug spreads were produced by pandas, so ddof=0 here would make
    the re-run incomparable to the run it is checking. On [0, 0, 3] the
    two conventions give sqrt(3) and sqrt(2).
    """
    p = cells(A=[0.0, 0.0, 3.0], B=[0.0, 0.0, 0.0])
    d = paired_delta(p, "A", "B")
    assert d.sd == pytest.approx(math.sqrt(3.0))
    assert d.sd != pytest.approx(math.sqrt(2.0))


def test_constant_offset_has_zero_spread() -> None:
    """Passes under either ddof, which is the point of the test above."""
    p = cells(A=[0.5, 0.6, 0.7], B=[0.4, 0.5, 0.6])
    assert paired_delta(p, "A", "B").sd == pytest.approx(0.0)


def test_mean_of_differences_equals_difference_of_means() -> None:
    p = cells(A=[0.81, 0.77, 0.90], B=[0.80, 0.79, 0.85])
    d = paired_delta(p, "A", "B")
    assert d.mean == pytest.approx(
        sum(p[s]["A"] for s in p) / 3 - sum(p[s]["B"] for s in p) / 3
    )


def test_one_seed_has_no_spread() -> None:
    with pytest.raises(ValueError):
        paired_delta(cells(A=[0.5], B=[0.4]), "A", "B")


def test_missing_cell_names_the_seed() -> None:
    p = {0: {"A": 0.5, "B": 0.4}, 1: {"A": 0.5}}
    with pytest.raises(KeyError, match="1"):
        paired_delta(p, "A", "B")


# --- integrity checks -----------------------------------------------------

def test_telescoping_is_zero_for_arbitrary_floats() -> None:
    """Pins the limitation, so the check is never re-promoted to evidence.

    These numbers are nonsense as cells -- unequal, unpaired, no shared
    split. The residual vanishes anyway.

    Note the tolerance: the identity is exact in real arithmetic but not in
    binary floating point, where (0.9-0.2)+(0.2-0.5)-(0.9-0.5) lands around
    1e-17. That is what `tol` in assert_telescoping is absorbing, and it is
    the only thing the residual ever measures.
    """
    p = cells(A=[0.9, 0.1], B=[0.2, 0.8], C=[0.5, 0.5])
    residuals = telescoping_residuals(p, "A", "B", "C").values()
    assert all(abs(r) < 1e-12 for r in residuals)
    assert any(r != 0.0 for r in residuals)


def test_shared_vocab_catches_a_refit_within_a_train_side() -> None:
    good = cells(A=[16000, 16100], B=[16000, 16100],
                 C=[15990, 16090], D=[15990, 16090])
    assert_shared_vocab(good)

    bad = cells(A=[16000, 16100], B=[16000, 16101],
                C=[15990, 16090], D=[15990, 16090])
    with pytest.raises(AssertionError, match="train side"):
        assert_shared_vocab(bad)


def test_shared_split_catches_a_different_test_slice() -> None:
    good = cells(A=[111, 222], B=[111, 222], C=[111, 222], D=[111, 222])
    assert_shared_split(good)

    bad = cells(A=[111, 222], B=[111, 999], C=[111, 222], D=[111, 222])
    with pytest.raises(AssertionError, match="test slice"):
        assert_shared_split(bad)