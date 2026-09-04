"""Model constructions. Nothing executes at import (METHOD 24).

Preprocessing lives inside the Pipeline so the fit-before-split bug is
unwritable (METHOD 8). The vectorizer is part of the model.

Moved from floor.py with no change to any argument. Do not tune anything
here until the floor is measured.
"""

from __future__ import annotations

from sklearn.dummy import DummyClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline


def make_pipe(seed: int) -> Pipeline:
    """TF-IDF + LogReg, all defaults.

    `random_state` is inert here: the default lbfgs solver is
    deterministic and ignores it. Kept so this run stays bit-identical to
    the 31 Aug one. It follows that every bit of the 0.0177 marginal
    spread comes from the subsample and the split, not from the model.
    """
    return Pipeline([
        ("tfidf", TfidfVectorizer()),
        ("clf", LogisticRegression(max_iter=1000, random_state=seed)),
    ])


def make_dummy(seed: int) -> Pipeline:
    """Stratified baseline. ~0.10 macro F1 on 4 balanced classes, not 0.25."""
    return Pipeline([
        ("tfidf", TfidfVectorizer()),
        ("clf", DummyClassifier(strategy="stratified", random_state=seed)),
    ])